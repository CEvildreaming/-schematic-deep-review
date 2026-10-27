"""Synthetic toolchain regression tests. These are not a real schematic review."""
import contextlib
import importlib.util
import io
import json
import math
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from font_fixture import test_font

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("review", ROOT / "scripts/review.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def component(file="a.pdf", ref="R1", value="10k", assembly="fitted"):
    c = {"file": file, "page": 1, "ref": ref, "unit": "", "value": value,
         "part_number": None, "package": None, "manufacturer": None, "group": "synthetic",
         "pins": [{"pin": "1", "net": "TEST", "status": "confirmed"}],
         "related": [], "assembly": assembly, "sources": [], "status": "unresolved",
         "analysis": "[推断] 自建夹具的测试连接，仅验证记录与覆盖率机制。"}
    c["id"] = r.component_id(c)
    return c


def annotation(c, aid="A1", bbox=None):
    return {"id": aid, "component_ids": [c["id"]], "page": 1, "text": c["analysis"],
            "bbox": bbox or [20, 20, 150, 40], "font_size": 9, "sources": []}


def pdf_bytes(text="TEST-IC revision A"):
    fitz = r.require_fitz()
    doc = fitz.open()
    p = doc.new_page(width=300, height=200)
    p.insert_text((20, 30), text, fontsize=12)
    p.draw_line((20, 80), (200, 80))
    p.draw_rect((70, 70, 120, 90))
    data = doc.tobytes()
    doc.close()
    return data


class TestCalculations(unittest.TestCase):
    def calc(self, kind, **inputs):
        return r.calculate({"id": "fixture", "kind": kind, "inputs": inputs, "assumptions": ["synthetic"]})["results"]

    def test_rc_threshold_and_step(self):
        v = self.calc("rc", r_ohm=10000, c_f=1e-6, threshold_fraction=.7,
                      time_s=.01, initial_v=0, final_v=3.3)
        self.assertAlmostEqual(v["tau_s"], .01)
        self.assertAlmostEqual(v["threshold_time_s"], .01203972804325936)
        self.assertAlmostEqual(v["voltage_v"], 3.3*(1-math.exp(-1)))
        with self.assertRaises(ValueError):
            self.calc("rc", r_ohm=10000, c_f=1e-6, threshold_fraction=1)

    def test_divider_power_and_source_resistance(self):
        v = self.calc("divider", vin_v=4.2, r_top_ohm=100000, r_bottom_ohm=100000)
        self.assertAlmostEqual(v["vout_v"], 2.1)
        self.assertAlmostEqual(v["r_th_ohm"], 50000)
        self.assertAlmostEqual(v["current_a"], 21e-6)
        self.assertAlmostEqual(v["top_power_w"]+v["bottom_power_w"], 4.2*v["current_a"])

    def test_energy_ldo_and_hold_up(self):
        self.assertAlmostEqual(self.calc("ldo", vin_v=5, vout_v=3.3, current_a=.1, iq_a=1e-6)["power_w"], .170005)
        self.assertAlmostEqual(self.calc("hold_up", current_a=.1, time_s=.001, delta_v=.2)["minimum_c_f"], .0005)
        self.assertAlmostEqual(self.calc("energy", c_f=10e-6, voltage_v=5)["capacitor_energy_j"], .000125)
        self.assertAlmostEqual(self.calc("inductor_slope", voltage_v=2, l_h=10e-6)["di_dt_a_per_s"], 200000)

    def test_led_crystal_impedance(self):
        self.assertAlmostEqual(self.calc("led", supply_v=3.3, vf_v=2, current_a=.005)["resistance_ohm"], 260)
        self.assertAlmostEqual(self.calc("crystal", c1_f=12e-12, c2_f=12e-12, stray_f=2e-12)["load_c_f"], 8e-12)
        self.assertAlmostEqual(self.calc("impedance", frequency_hz=1e6, c_f=1e-9)["zc_ohm"]["imag"], -159.154943091895)

    def test_matching_independent_backsubstitution(self):
        match = self.calc("l_match", source_ohm=50, load_ohm=200, frequency_hz=100e6)
        check = self.calc("pi", frequency_hz=100e6, cin_f=0, cout_f=match["shunt_c_f"],
                          l_h=match["series_l_h"], load_ohm=200, z0_ohm=50)
        self.assertAlmostEqual(check["zin_ohm"]["real"], 50)
        self.assertAlmostEqual(check["zin_ohm"]["imag"], 0)
        self.assertLess(check["gamma_abs"], 1e-14)
        self.assertIsNone(check["return_loss_db"])

    def test_missing_and_nonfinite_inputs_rejected(self):
        for inputs in ({"vin_v": 4.2, "r_top_ohm": 100}, {"vin_v": float("nan"), "r_top_ohm": 10, "r_bottom_ohm": 10}):
            with self.assertRaises(ValueError): self.calc("divider", **inputs)
        with self.assertRaises(ValueError): self.calc("ldo", vin_v=2.9, vout_v=3.3, current_a=.1)


class TestEvidenceQA(unittest.TestCase):
    def test_same_reference_across_files_is_distinct(self):
        a, b = component("a.pdf"), component("b.pdf")
        qa = r.coverage_qa([a, b], [annotation(a)])
        self.assertEqual(qa["actual_unique_components"], 2)
        self.assertEqual(qa["uncovered"], [b["id"]])

    def test_duplicate_record_and_unknown_reference_rejected(self):
        a, b = component(), component("b.pdf")
        qa = r.coverage_qa([a, a], [annotation(a), annotation(b, "B")])
        self.assertFalse(qa["passed"])
        self.assertEqual(qa["duplicate_ids"], [a["id"]])
        self.assertEqual(qa["unknown_annotation_ids"], [b["id"]])

    def test_dnp_and_zero_ohm_remain_in_denominator(self):
        a, b = component(ref="C7", value="DNP", assembly="DNP"), component(ref="R4", value="0 Ω")
        qa = r.coverage_qa([a, b], [annotation(a), annotation(b, "B")])
        self.assertTrue(qa["passed"])
        self.assertEqual(qa["annotated_components"], 2)

    def test_missing_part_number_does_not_invent_source(self):
        a = component(ref="F1", value="6 V 2 A")
        a["requires_datasheet"] = True
        qa = r.coverage_qa([a], [annotation(a)])
        self.assertEqual(qa["missing_identifiable_part_numbers"], [a["id"]])
        self.assertIsNone(a["manufacturer"])

    def test_bom_conflict_retained(self):
        a = component(value="10k")
        b = dict(a, value="100k")
        qa = r.coverage_qa([a], [annotation(a)], [b])
        self.assertFalse(qa["passed"])
        self.assertEqual(qa["bom_conflicts"][0]["schematic"], "10k")
        self.assertEqual(a["value"], "10k")

    def test_dense_layout_obstacles_and_bounds(self):
        a = component()
        ann = [annotation(a, "A", [10,10,100,40]), annotation(a, "B", [90,30,140,50]), annotation(a, "C", [190,100,210,120])]
        qa = r.layout_qa(ann, {"1": [200,200]}, [{"id":"wire", "page":1,"kind":"wire","bbox":[30,20,31,80]}])
        self.assertFalse(qa["passed"])
        self.assertEqual(qa["annotation_overlaps"], [["A", "B"]])
        self.assertEqual(len(qa["boundary_errors"]), 1)
        self.assertEqual(len(qa["original_obstacle_intersections"]), 1)

    def test_schema_rejects_fake_download_success(self):
        import jsonschema
        data = {"project":{"name":"fixture","original_files":[]},"components":[],"sources":[{"id":"x","model":"X","manufacturer":"M","version":"1","document_type":"datasheet","status":"downloaded"}],"annotations":[],"calculations":[]}
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(data, r.read_json(ROOT/"assets/project.schema.json"))


class TestPdfAndDownload(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="schematic-review-tests-")
        self.root = Path(self.tmp.name)
        self.source = self.root/"synthetic.pdf"
        self.source.write_bytes(pdf_bytes())

    def tearDown(self): self.tmp.cleanup()

    def test_pdf_validation_rejects_html_and_wrong_model(self):
        fake = self.root/"login.pdf"; fake.write_text("<html>Sign in</html>")
        with self.assertRaises(ValueError): r.validate_pdf(fake)
        with self.assertRaises(ValueError): r.validate_pdf(self.source, "WRONG-MODEL")
        self.assertEqual(r.validate_pdf(self.source, "TEST-IC")["pages"], 1)

    def test_extract_preserves_vector_and_source_repeated(self):
        output, png = self.root/"clip.pdf", self.root/"clip.png"
        before = r.sha256(self.source)
        for _ in range(2):
            result = r.extract_pdf(self.source, 1, output, [10,10,220,110], png, dpi=150)
            self.assertEqual(result["pages"], 1)
            self.assertEqual(r.sha256(self.source), before)
            inspect = r.inspect_pdf(output)
            self.assertGreater(inspect["pages_detail"][0]["vector_path_count"], 0)
            self.assertIn("TEST-IC", inspect["pages_detail"][0]["text"])
        self.assertTrue(png.exists())
        with self.assertRaises(ValueError): r.extract_pdf(self.source, 1, self.source)

    def test_scanned_page_classification(self):
        from PIL import Image, ImageDraw
        fitz = r.require_fitz()
        im = Image.new("RGB", (400,200), "white"); ImageDraw.Draw(im).line((10,100,390,100), fill="black", width=3)
        stream = io.BytesIO(); im.save(stream, format="PNG")
        doc = fitz.open(); p = doc.new_page(width=400,height=200); p.insert_image(p.rect, stream=stream.getvalue())
        path=self.root/"scan.pdf"; doc.save(path); doc.close()
        result = r.inspect_pdf(path)["pages_detail"][0]
        self.assertTrue(result["likely_scan"])
        self.assertEqual(result["vector_path_count"], 0)

    def test_chinese_special_glyphs_and_roundtrip(self):
        fitz = r.require_fitz()
        font = test_font(self.root)
        text = "中文测试 Ω μ π 3.3 V 10 kΩ"
        a = annotation(component()); a.update(text=text,font_file=str(font))
        self.assertEqual(r.layout_qa([a], {"1":[300,200]})["glyph_errors"], [])
        doc=fitz.open(); p=doc.new_page(width=400,height=120); p.insert_font(fontname="F0",fontfile=str(font)); p.insert_text((20,50),text,fontname="F0",fontsize=12)
        path=self.root/"cjk.pdf"; doc.save(path); doc.close()
        with fitz.open(path) as check:
            self.assertIn("中文测试", check[0].get_text())
            self.assertIn("Ω", check[0].get_text())
            self.assertGreater(len(check.extract_font(check[0].get_fonts()[0][0])[3]), 0)
            check[0].get_pixmap(dpi=150).save(self.root/"cjk.png")

    def test_download_cache_versions_and_failure(self):
        payloads = {"/a.pdf": pdf_bytes("TEST-IC revision A"), "/b.pdf": pdf_bytes("TEST-IC revision B"), "/html.pdf":b"<html>Login required</html>"}
        counts = {}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                counts[self.path]=counts.get(self.path,0)+1
                if self.path not in payloads:
                    self.send_error(404); return
                self.send_response(200); self.send_header("Content-Type","application/pdf"); self.end_headers(); self.wfile.write(payloads[self.path])
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            base=f"http://127.0.0.1:{server.server_port}"
            a={"id":"a","url":base+"/a.pdf","model":"TEST-IC","manufacturer":"Synthetic fixture","version":"A","document_type":"datasheet","expected_text":"TEST-IC","local_path":"TEST-IC/TEST-IC_详解.pdf"}
            first=r.download_sources([a],self.root/"archive")
            self.assertEqual(first[0]["status"],"downloaded")
            self.assertEqual(r.download_sources([a],self.root/"archive")[0]["status"],"cached")
            self.assertEqual(counts["/a.pdf"],1)
            b=dict(a,id="b",url=base+"/b.pdf",version="B")
            second=r.download_sources([b],self.root/"archive")[0]
            self.assertEqual(second["status"],"downloaded")
            self.assertNotEqual(first[0]["local_path"],second["local_path"])
            self.assertEqual(r.download_sources([b],self.root/"archive")[0]["status"],"cached")
            self.assertEqual(counts["/b.pdf"],1)
            self.assertEqual(r.sha256(self.root/"archive"/first[0]["local_path"]),first[0]["sha256"])
            failed=r.download_sources([dict(a,url=base+"/html.pdf",local_path="bad.pdf"),dict(a,url=base+"/404.pdf",local_path="404.pdf")],self.root/"archive")
            self.assertTrue(all(x["status"]=="failed" for x in failed))
            self.assertFalse((self.root/"archive/bad.pdf").exists())
            self.assertFalse(list((self.root/"archive").rglob("*.part")))
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)

    def test_archive_path_escape_rejected(self):
        with self.assertRaises(ValueError): r.safe_destination(self.root,"../outside.pdf")

    def test_cli_calculation_example_and_atomic_repeat(self):
        out=self.root/"calculations.json"
        self.assertEqual(r.main(["calculate",str(ROOT/"assets/calculations.example.json"),"--out",str(out)]),0)
        first=out.read_bytes(); stamp=out.stat().st_mtime_ns
        self.assertEqual(r.main(["calculate",str(ROOT/"assets/calculations.example.json"),"--out",str(out)]),0)
        self.assertEqual(out.read_bytes(),first)
        self.assertEqual(out.stat().st_mtime_ns,stamp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
