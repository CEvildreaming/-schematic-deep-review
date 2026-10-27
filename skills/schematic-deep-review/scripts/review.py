#!/usr/bin/env python3
"""Deterministic helpers for schematic reviews. Never infer electrical roles from refs.

All page numbers are 1-based. Rectangles use PDF points, top-left coordinates.
All calculation inputs use SI units as named in the input keys. Python >=3.10.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import re
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    # Deterministic content is retained; an interrupted write cannot destroy an old result.
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     suffix=".tmp", delete=False) as f:
        tmp = Path(f.name)
        f.write(text)
    tmp.replace(path)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for data in iter(lambda: f.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def require_fitz():
    try:
        import pymupdf as fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF required. Install requirements.txt into a project-local environment.") from exc
    return fitz


def validate_pdf(path, expected_text=None):
    fitz = require_fitz()
    path = Path(path)
    with path.open("rb") as f:
        if not f.read(1024).lstrip().startswith(b"%PDF-"):
            raise ValueError("Not a PDF: missing %PDF magic; HTML/login/error pages are rejected")
    with fitz.open(path) as doc:
        if doc.needs_pass or not len(doc):
            raise ValueError("PDF is encrypted or contains no readable pages")
        text = "\n".join(p.get_text() for p in doc)
        if expected_text and expected_text.casefold() not in text.casefold():
            raise ValueError(f"Expected model/title text not found: {expected_text!r}")
        return {"sha256": sha256(path), "bytes": path.stat().st_size,
                "pages": len(doc), "title": doc.metadata.get("title") or "",
                "text_characters": len(text), "text_check": "matched" if expected_text else "not_requested",
                "parse_status": "passed", "applicability_review": "requires_human_review"}


def inspect_pdf(path):
    fitz = require_fitz()
    result = validate_pdf(path)
    result["file"] = str(Path(path).resolve())
    result["pages_detail"] = []
    with fitz.open(path) as doc:
        result["bookmarks"] = [{"level": level, "title": title, "page": page} for level, title, page in doc.get_toc()]
        result["bookmark_note"] = "Altium SmartPDF may include Components and Nets bookmark trees. These are export metadata that can aid pin/net identification; validate against visible connections. NetLabels and hidden object IDs are not components."
        for n, p in enumerate(doc, 1):
            text = p.get_text()
            drawings = p.get_drawings()
            words = p.get_text("words")
            result["pages_detail"].append({
                "page": n, "width_pt": p.rect.width, "height_pt": p.rect.height,
                "text": text, "text_characters": len(text.strip()),
                "vector_path_count": len(drawings), "image_count": len(p.get_images()),
                "likely_scan": len(text.strip()) < 8 and bool(p.get_images()),
                "text_boxes": [{"bbox": list(w[:4]), "text": w[4]} for w in words],
                "vector_boxes": [list(d["rect"]) for d in drawings],
                "font_records": [list(f) for f in p.get_fonts(full=True)]})
    result["limitations"] = ["Text/vector presence does not prove connectivity or completeness.",
                              "Scanned pages need visual tracing; OCR is not netlist extraction."]
    return result


def safe_part(value):
    part = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(value)).strip(" .")
    return part[:120] or "unspecified"


def safe_destination(root, rel):
    root = Path(root).resolve()
    target = (root / rel).resolve()
    if target == root or root not in target.parents:
        raise ValueError("Destination must stay inside archive root")
    return target


def download_sources(manifest, root, timeout=30, max_bytes=100 * 1024 * 1024):
    """Fetch public URLs only. Cache exact source identity; never overwrite conflicting content.

    Manifest: list or {sources:[...]}; each item needs id, url, model, manufacturer,
    version, document_type. Optional local_path and expected_text. Version is declared
    by the reviewer, not guessed from metadata; applicability remains separately reviewed.
    """
    records = manifest.get("sources", []) if isinstance(manifest, dict) else manifest
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    results = []
    for request in records:
        record = dict(request)
        record["accessed_utc"] = datetime.now(timezone.utc).isoformat()
        temp = None
        try:
            for key in ("id", "url", "model", "manufacturer", "version", "document_type"):
                if not request.get(key):
                    raise ValueError(f"Missing manifest field: {key}")
            if not request["url"].startswith(("https://", "http://")):
                raise ValueError("Only public HTTP(S) URLs are accepted")
            identity = {k: request[k] for k in ("manufacturer", "model", "version", "document_type", "url")}
            identity_hash = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:12]
            cache_index = root / ".source-cache" / (identity_hash + ".json")
            if cache_index.exists():
                cached = read_json(cache_index)
                cached_path = safe_destination(root, cached["local_path"])
                if cached.get("identity") == identity and cached_path.exists() and sha256(cached_path) == cached.get("sha256"):
                    checked = validate_pdf(cached_path, request.get("expected_text"))
                    record.update(checked, status="cached", local_path=cached_path.relative_to(root).as_posix(), identity=identity)
                    results.append(record)
                    continue
            default = Path(safe_part(request["model"])) / safe_part(request["manufacturer"]) / safe_part(request["version"]) / (safe_part(request["model"]) + "_" + safe_part(request["document_type"]) + "_详解.pdf")
            target = safe_destination(root, request.get("local_path", default))
            sidecar = target.with_suffix(".source.json")
            if target.exists() and sidecar.exists():
                old = read_json(sidecar)
                if old.get("identity") == identity and sha256(target) == old.get("sha256"):
                    checked = validate_pdf(target, request.get("expected_text"))
                    record.update(checked, status="cached", local_path=target.relative_to(root).as_posix(), identity=identity)
                    write_json(cache_index, record)
                    results.append(record)
                    continue
            target.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(request["url"], headers={"User-Agent": "schematic-deep-review/1.0 (document archival)"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                record["resolved_url"] = response.geturl()
                record["content_type"] = response.headers.get("Content-Type", "")
                total = 0
                with tempfile.NamedTemporaryFile("wb", dir=target.parent, suffix=".part", delete=False) as f:
                    temp = Path(f.name)
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > max_bytes:
                            raise ValueError("Download exceeds configured size limit")
                        f.write(chunk)
            checked = validate_pdf(temp, request.get("expected_text"))
            if target.exists():
                if sha256(target) == checked["sha256"]:
                    # Content-identical material may be shared, but version identities stay in records.
                    temp.unlink()
                    temp = None
                else:
                    target = target.with_name(target.stem + "_" + identity_hash + "_" + checked["sha256"][:8] + target.suffix)
                    sidecar = target.with_suffix(".source.json")
                    if target.exists() and sha256(target) != checked["sha256"]:
                        raise ValueError("Archive conflict; refusing overwrite")
                    temp.replace(target)
                    temp = None
            else:
                temp.replace(target)
                temp = None
            record.update(checked, status="downloaded", local_path=target.relative_to(root).as_posix(), identity=identity)
            write_json(sidecar, record)
            write_json(cache_index, record)
        except Exception as exc:
            record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        finally:
            if temp is not None and temp.exists():
                temp.unlink()
        results.append(record)
    return results


def extract_pdf(source, page_number, output, clip=None, png=None, dpi=450):
    fitz = require_fitz()
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError("Source PDF is immutable; output must be different")
    if not 72 <= dpi <= 1200:
        raise ValueError("DPI must be between 72 and 1200")
    before = sha256(source)
    with fitz.open(source) as src:
        if not 1 <= page_number <= len(src):
            raise ValueError("Page number out of range (1-based)")
        page = src[page_number - 1]
        area = fitz.Rect(clip) if clip else page.rect
        if area.is_empty or not page.rect.contains(area):
            raise ValueError("Clip must be a positive rectangle inside the source page")
        out = fitz.open()
        new = out.new_page(width=area.width, height=area.height)
        new.show_pdf_page(new.rect, src, page_number - 1, clip=area)
        out.set_metadata({"title": f"Excerpt PDF page {page_number}: {source.name}",
                          "subject": "Source content retained; PDF page number is 1-based"})
        output.parent.mkdir(parents=True, exist_ok=True)
        out.save(output, garbage=4, deflate=True)
        if png:
            Path(png).parent.mkdir(parents=True, exist_ok=True)
            new.get_pixmap(dpi=dpi, alpha=False).save(png)
        out.close()
    if sha256(source) != before:
        raise RuntimeError("Source checksum changed unexpectedly")
    result = validate_pdf(output)
    result.update(source_sha256=before, source_file=str(source), pdf_page=page_number,
                  printed_page=None, clip=list(area), output=str(output), preview=str(png) if png else None,
                  preview_dpi=dpi if png else None)
    write_json(output.with_suffix(".excerpt.json"), result)
    return result


def finite_num(inputs, name, positive=False, nonnegative=False, default=None):
    if name not in inputs:
        if default is None:
            raise ValueError(f"Missing parameter {name}; do not invent an input")
        v = default
    else:
        v = inputs[name]
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f"{name} must be a finite SI number")
    if positive and v <= 0 or nonnegative and v < 0:
        raise ValueError(f"Invalid sign for {name}")
    return float(v)


def calculate(record):
    kind, i = record["kind"], record["inputs"]
    n = lambda key, **kw: finite_num(i, key, **kw)
    limitation = "Ideal lumped-component model; actual tolerances, loading, parasitics and temperature require review."
    if kind == "rc":
        r, c = n("r_ohm", positive=True), n("c_f", positive=True)
        tau = r * c
        out = {"tau_s": tau, "fc_hz": 1 / (2 * math.pi * tau)}
        formula = "tau=R_th*C; fc=1/(2*pi*R_th*C); t=-tau*ln(1-threshold_fraction)"
        if "threshold_fraction" in i:
            f = n("threshold_fraction")
            if not 0 < f < 1:
                raise ValueError("Threshold fraction must be strictly between 0 and 1")
            out["threshold_time_s"] = -tau * math.log1p(-f)
        if "time_s" in i:
            t, v0, vf = n("time_s", nonnegative=True), n("initial_v"), n("final_v")
            out["voltage_v"] = vf + (v0 - vf) * math.exp(-t / tau)
        limitation += " RC is not automatically reset/debounce/startup delay; threshold and supply ramp matter."
    elif kind == "divider":
        vin, rt, rb = n("vin_v"), n("r_top_ohm", positive=True), n("r_bottom_ohm", positive=True)
        out = {"ratio": rb/(rt+rb), "vout_v": vin*rb/(rt+rb), "current_a": vin/(rt+rb),
               "r_th_ohm": rt*rb/(rt+rb), "top_power_w": (vin/(rt+rb))**2*rt,
               "bottom_power_w": (vin/(rt+rb))**2*rb}
        formula = "Vout=Vin*Rb/(Rt+Rb); I=Vin/(Rt+Rb); Rth=Rt*Rb/(Rt+Rb); P=I^2*R"
        limitation += " Unloaded divider; ADC acquisition and leakage are not included."
    elif kind == "led":
        vs, vf, sw, current = n("supply_v"), n("vf_v"), n("switch_drop_v", nonnegative=True, default=0), n("current_a", positive=True)
        if vs <= vf + sw:
            raise ValueError("No positive resistor headroom")
        out = {"resistance_ohm": (vs-vf-sw)/current, "power_w": (vs-vf-sw)*current}
        formula = "R=(Vs-Vf-Vswitch)/I; P=I^2*R"
    elif kind == "ldo":
        vin, vout, current, iq = n("vin_v"), n("vout_v"), n("current_a", nonnegative=True), n("iq_a", nonnegative=True, default=0)
        if vin < vout:
            raise ValueError("LDO input below requested output; regulation cannot be assumed")
        out = {"power_w": (vin-vout)*current+vin*iq}
        formula = "P=(Vin-Vout)*Iout+Vin*Iq"
        limitation += " Dropout/headroom and thermal resistance are not included; rated current is not a thermal proof."
    elif kind == "hold_up":
        current, time, dv = n("current_a", nonnegative=True), n("time_s", nonnegative=True), n("delta_v", positive=True)
        out = {"minimum_c_f": current*time/dv}
        formula = "C>=I*delta_t/delta_V"
        limitation += " Assumes constant current; ESR step, regulator response and capacitance derating are excluded."
    elif kind == "energy":
        out = {}
        if "c_f" in i:
            out["capacitor_energy_j"] = n("c_f", nonnegative=True)*n("voltage_v")**2/2
        if "l_h" in i:
            out["inductor_energy_j"] = n("l_h", nonnegative=True)*n("current_a")**2/2
        if not out:
            raise ValueError("Specify c_f with voltage_v and/or l_h with current_a")
        formula = "Ec=C*V^2/2; El=L*I^2/2"
    elif kind == "inductor_slope":
        out = {"di_dt_a_per_s": n("voltage_v")/n("l_h", positive=True)}
        formula = "di/dt=V/L"
    elif kind == "crystal":
        c1, c2, cp = n("c1_f", positive=True), n("c2_f", positive=True), n("stray_f", nonnegative=True)
        out = {"load_c_f": c1*c2/(c1+c2)+cp}
        formula = "CL=C1*C2/(C1+C2)+Cstray"
        limitation += " Assumes the stated two-capacitor oscillator topology; IC internal capacitors must be accounted for."
    elif kind == "impedance":
        w = 2*math.pi*n("frequency_hz", positive=True)
        out = {}
        if "l_h" in i:
            out["zl_ohm"] = {"real": 0, "imag": w*n("l_h", nonnegative=True)}
        if "c_f" in i:
            out["zc_ohm"] = {"real": 0, "imag": -1/(w*n("c_f", positive=True))}
        if not out:
            raise ValueError("Specify l_h and/or c_f")
        formula = "ZL=j*2*pi*f*L; ZC=1/(j*2*pi*f*C)"
    elif kind == "pi":
        w = 2*math.pi*n("frequency_hz", positive=True)
        ci, co, l, rl, z0 = n("cin_f", nonnegative=True), n("cout_f", nonnegative=True), n("l_h", nonnegative=True), n("load_ohm", positive=True), n("z0_ohm", positive=True)
        zout = 1/(1/rl+1j*w*co)
        zin = 1/(1j*w*ci+1/(1j*w*l+zout))
        gamma = (zin-z0)/(zin+z0)
        g = abs(gamma)
        out = {"zin_ohm": {"real": zin.real, "imag": zin.imag},
               "gamma": {"real": gamma.real, "imag": gamma.imag}, "gamma_abs": g,
               "return_loss_db": -20*math.log10(g) if g > 1e-15 else None,
               "ideal_exact_match": g <= 1e-15}
        formula = "Zout=(1/RL+j*w*Cout)^-1; Zin=(j*w*Cin+1/(j*w*L+Zout))^-1; Gamma=(Zin-Z0)/(Zin+Z0)"
        limitation += " Topology is input shunt Cin / series L / output shunt Cout / real RL. No arbitrary cutoff or PCB matching claim follows. Null return loss means an ideal exact match, not a measurement."
    elif kind == "l_match":
        rs, rl, f = n("source_ohm", positive=True), n("load_ohm", positive=True), n("frequency_hz", positive=True)
        if rl <= rs:
            raise ValueError("This model requires Rload>Rsource: series L then shunt C across Rload")
        q = math.sqrt(rl/rs-1)
        out = {"q": q, "series_l_h": q*rs/(2*math.pi*f), "shunt_c_f": q/(rl*2*math.pi*f)}
        formula = "Q=sqrt(RL/RS-1); L=Q*RS/w; C=Q/(RL*w)"
        limitation += " Single-frequency low-pass L matching model, series L then output shunt C. Not a filter cutoff specification."
    else:
        raise ValueError(f"Unknown calculation kind: {kind}")
    result = dict(record)
    result.update(formula=formula, results=out, model_limitations=limitation, computation_status="computed")
    result.setdefault("assumptions", [])
    result["input_evidence_status"] = "supplied" if record.get("input_evidence") else "not_provided"
    return result


def component_id(component):
    for key in ("file", "page", "ref"):
        if component.get(key) is None or component.get(key) == "":
            raise ValueError(f"Component lacks identity field {key}")
    return "/".join(str(component.get(k, "")) for k in ("file", "page", "ref", "unit"))


def as_records(data, key):
    return data.get(key, []) if isinstance(data, dict) else data


def coverage_qa(components, annotations, bom=None):
    components, annotations = as_records(components, "components"), as_records(annotations, "annotations")
    ids, duplicates, unanalysed, missing_fields, missing_parts = [], [], [], [], []
    for c in components:
        cid = c.get("id") or component_id(c)
        if cid in ids:
            duplicates.append(cid)
        ids.append(cid)
        if not c.get("analysis") or not str(c.get("analysis")).strip():
            unanalysed.append(cid)
        absent = [key for key in ("value", "package", "manufacturer", "group", "pins", "related", "assembly", "sources", "status") if key not in c]
        if absent:
            missing_fields.append({"id": cid, "fields": absent})
        if c.get("requires_datasheet") and not c.get("part_number"):
            missing_parts.append(cid)
    covered, empty_annotations, unknown = set(), [], set()
    for a in annotations:
        references = a.get("component_ids", [])
        if not a.get("text", "").strip():
            empty_annotations.append(a.get("id", ""))
            continue
        covered.update(references)
        unknown.update(set(references)-set(ids))
    missing = sorted(set(ids)-covered)
    conflicts = []
    if bom is not None:
        lookup = {c.get("id") or component_id(c): c for c in components}
        for row in as_records(bom, "components"):
            cid = row.get("id") or component_id(row)
            if cid not in lookup:
                conflicts.append({"id": cid, "kind": "bom_only"})
            else:
                for field in ("value", "part_number", "assembly"):
                    if row.get(field) is not None and lookup[cid].get(field) != row[field]:
                        conflicts.append({"id": cid, "field": field, "schematic": lookup[cid].get(field), "bom": row[field]})
    return {"actual_unique_components": len(set(ids)), "record_count": len(ids),
            "annotated_components": len(set(ids) & covered), "uncovered_count": len(missing),
            "uncovered": missing, "unanalysed": unanalysed, "duplicate_ids": duplicates,
            "unknown_annotation_ids": sorted(unknown), "empty_annotations": empty_annotations,
            "missing_record_fields": missing_fields, "missing_identifiable_part_numbers": missing_parts,
            "bom_conflicts": conflicts,
            "passed": not (missing or unanalysed or duplicates or unknown or empty_annotations or missing_fields or conflicts),
            "limitations": "Coverage is over the supplied inventory, not proof the PDF inventory is complete. DNP and zero-ohm positions remain in the denominator. Electrical truth requires review."}


def rect_valid(r):
    return isinstance(r, (list, tuple)) and len(r) == 4 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in r) and r[2] > r[0] and r[3] > r[1]


def intersects(a, b, margin=0):
    return a[0] < b[2]+margin and a[2] > b[0]-margin and a[1] < b[3]+margin and a[3] > b[1]-margin


def layout_qa(annotations, page_sizes, obstacles=None, margin=0):
    annotations = as_records(annotations, "annotations")
    obstacles = obstacles or []
    errors, pairs, collisions, glyph_errors = [], [], [], []
    fitz = None
    for a in annotations:
        aid, p, r = a.get("id", ""), str(a.get("page", 1)), a.get("bbox")
        if not rect_valid(r):
            errors.append({"id": aid, "error": "invalid_bbox"})
            continue
        size = page_sizes.get(p) or page_sizes.get(int(p))
        if not size or r[0] < 0 or r[1] < 0 or r[2] > size[0] or r[3] > size[1]:
            errors.append({"id": aid, "error": "outside_page_or_missing_size"})
        if "\ufffd" in a.get("text", "") or "\x00" in a.get("text", ""):
            glyph_errors.append({"id": aid, "characters": "replacement_or_NUL"})
        if a.get("font_file"):
            try:
                fitz = fitz or require_fitz()
                font = fitz.Font(fontfile=a["font_file"])
                absent = sorted({c for c in a.get("text", "") if not c.isspace() and not font.has_glyph(ord(c))})
                if absent:
                    glyph_errors.append({"id": aid, "characters": "".join(absent)})
            except Exception as exc:
                glyph_errors.append({"id": aid, "font_error": str(exc)})
        for ob in obstacles:
            if str(ob.get("page", 1)) == p and rect_valid(ob.get("bbox")) and intersects(r, ob["bbox"], margin):
                collisions.append({"annotation": aid, "obstacle": ob.get("id", ""), "kind": ob.get("kind", "original")})
    for idx, a in enumerate(annotations):
        for b in annotations[idx+1:]:
            if a.get("page", 1) == b.get("page", 1) and rect_valid(a.get("bbox")) and rect_valid(b.get("bbox")) and intersects(a["bbox"], b["bbox"], margin):
                pairs.append([a.get("id", ""), b.get("id", "")])
    unchecked = [a.get("id", "") for a in annotations if not a.get("font_file")]
    return {"boundary_errors": errors, "annotation_overlaps": pairs,
            "original_obstacle_intersections": collisions, "glyph_errors": glyph_errors,
            "glyph_check_not_run": unchecked,
            "checks_complete": not unchecked,
            "screening_passed": not (errors or pairs or collisions or glyph_errors),
            "passed": not (errors or pairs or collisions or glyph_errors or unchecked),
            "limitations": "Bounding-box screening cannot prove no occlusion, connection fidelity or readable wrapping. Inspect rendered PDFs and original-region pixel equality; font checks require font_file."}


def export_csv(components, output):
    rows = as_records(components, "components")
    keys = ["id", "file", "page", "ref", "unit", "value", "part_number", "package", "manufacturer", "group", "pins", "related", "assembly", "sources", "status", "analysis"]
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with Path(output).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("inspect"); p.add_argument("input"); p.add_argument("--out", required=True); p.add_argument("--text")
    p = sub.add_parser("download"); p.add_argument("manifest"); p.add_argument("--root", required=True); p.add_argument("--out", required=True); p.add_argument("--timeout", type=int, default=30)
    p = sub.add_parser("extract"); p.add_argument("input"); p.add_argument("--page", type=int, required=True); p.add_argument("--out", required=True); p.add_argument("--clip"); p.add_argument("--png"); p.add_argument("--dpi", type=int, default=450)
    p = sub.add_parser("calculate"); p.add_argument("input"); p.add_argument("--out", required=True)
    p = sub.add_parser("qa"); p.add_argument("components"); p.add_argument("annotations"); p.add_argument("--out", required=True); p.add_argument("--page-sizes"); p.add_argument("--obstacles"); p.add_argument("--bom")
    p = sub.add_parser("csv"); p.add_argument("components"); p.add_argument("--out", required=True)
    p = sub.add_parser("validate"); p.add_argument("input"); p.add_argument("--schema", default=str(Path(__file__).resolve().parents[1]/"assets/project.schema.json"))
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            result = inspect_pdf(args.input)
            if args.text:
                Path(args.text).parent.mkdir(parents=True, exist_ok=True)
                Path(args.text).write_text("\n\f\n".join(p["text"] for p in result["pages_detail"]), encoding="utf-8")
            write_json(args.out, result)
        elif args.command == "download":
            result = download_sources(read_json(args.manifest), args.root, args.timeout)
            write_json(args.out, result)
            print(json.dumps({"status_counts": {s: sum(r["status"] == s for r in result) for s in ("downloaded", "cached", "failed")}}, ensure_ascii=False))
            return int(any(r["status"] == "failed" for r in result))
        elif args.command == "extract":
            result = extract_pdf(args.input, args.page, args.out, [float(x) for x in args.clip.split(",")] if args.clip else None, args.png, args.dpi)
        elif args.command == "calculate":
            records = read_json(args.input)
            result = [calculate(r) for r in as_records(records, "calculations")]
            write_json(args.out, result)
        elif args.command == "qa":
            comp, ann = read_json(args.components), read_json(args.annotations)
            result = {"coverage": coverage_qa(comp, ann, read_json(args.bom) if args.bom else None)}
            if args.page_sizes:
                result["layout"] = layout_qa(ann, read_json(args.page_sizes), read_json(args.obstacles) if args.obstacles else None)
            result["passed"] = all(x["passed"] for x in result.values())
            write_json(args.out, result)
            print(json.dumps({"passed": result["passed"], "report": args.out}))
            return int(not result["passed"])
        elif args.command == "csv":
            export_csv(read_json(args.components), args.out)
        elif args.command == "validate":
            import jsonschema
            jsonschema.Draft202012Validator(read_json(args.schema)).validate(read_json(args.input))
        print(json.dumps({"command": args.command, "status": "completed"}, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
