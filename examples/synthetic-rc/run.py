"""Generate a synthetic RC source and verify a one-page annotated review.

No real board, manufacturer schematic, or confidential project is used.
Run from any working directory: python examples/synthetic-rc/run.py
"""
from pathlib import Path
import hashlib
import json
import math
import sys

import pymupdf as fitz

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "skills/schematic-deep-review/scripts"))
from readable_layout import render
from review import calculate


def main():
    out = Path(__file__).resolve().parent / "output"
    out.mkdir(exist_ok=True)
    source = out / "synthetic-rc-original.pdf"
    doc = fitz.open()
    page = doc.new_page(width=570, height=290)
    blue = (0.05, 0.15, 0.45)
    def line(a, b):
        page.draw_line(a, b, color=blue, width=1.3)
    def text(x, y, value, size=11):
        page.insert_text((x, y), value, fontsize=size, color=blue)
    text(20, 25, "SYNTHETIC TEACHING CIRCUIT - not a real board", 12)
    text(30, 78, "3.3 V step")
    text(170, 72, "R1   10 kohm")
    line((40, 100), (155, 100))
    page.draw_rect((155, 91, 240, 109), color=blue, width=1.3)
    line((240, 100), (485, 100))
    page.draw_circle((330, 100), 2.5, color=blue, fill=blue)
    text(395, 78, "Vout / ideal input")
    line((330, 100), (330, 160))
    line((306, 160), (354, 160))
    line((306, 169), (354, 169))
    line((330, 169), (330, 220))
    line((306, 220), (354, 220))
    line((314, 226), (346, 226))
    line((322, 232), (338, 232))
    text(365, 173, "C1   1 uF")
    text(316, 253, "GND")
    text(20, 278, "Assume: ideal source, initially discharged C1, no input loading.", 10)
    doc.save(source, garbage=4, deflate=True)
    doc.close()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    font = out / "demo-font.ttf"
    font.write_bytes(fitz.Font("helv").buffer)
    notes = [
        ("roles", [610, 50, 880, 153],
         "R1 + C1: delay and low-pass filtering\nR1 limits charging current; C1 stores charge, so Vout cannot jump instantly. Together they slow a voltage edge and reduce fast input variations. C1 is not a power-supply bypass capacitor in this connection."),
        ("calculation", [610, 165, 880, 285],
         "Calculated example\ntau = R1 x C1 = 10 ms.\nVout = 3.3 x (1 - exp(-t/tau)).\nAn assumed 70% input threshold is reached after -tau x ln(0.3) = 12.04 ms. The small-signal cutoff is 1/(2*pi*tau) = 15.92 Hz. This is not a guaranteed digital power-on reset."),
        ("failure", [40, 355, 455, 455],
         "What changes if a part is removed?\nC1 open: this intentional delay disappears. R1 open: the input has no defined charging path. R1 short: C1 loads the source directly; the intended 10 ms time constant is lost. Input leakage or an internal pull resistor changes the result."),
        ("checks", [485, 355, 880, 455],
         "Before applying this to hardware\nCheck the actual receiver threshold and slow-edge tolerance. Use effective capacitance and resistor tolerance. Include source resistance and input loading in the Thevenin resistance. Measure the edge if timing matters."),
    ]
    plan = {
        "source": str(source), "font": str(font),
        "canvas_size": [940, 620], "title_box": [20, 10, 920, 42],
        "title": "RC DELAY: COMPONENTS, INTERACTION, AND LIMITS", "title_size": 16,
        "summary_box": [20, 570, 920, 612], "summary_size": 10,
        "summary": "Synthetic example. Values and threshold are teaching assumptions. No datasheet is required or claimed. Source vectors are preserved; annotations are screened for clipping, overlap, and source-ink changes.",
        "drawing_label_pt": 11, "font_source_pt": 10.5,
        "minimum_font_ratio": 0.8,
        "panels": [{"id": "rc", "title": "01  RC timing and filtering", "size": [900, 510], "pos": [20, 50], "origin": [0, 0], "pad": [20, 40], "clips": [[0, 0, 570, 290]]}],
        "annotations": [{"id": key, "panel": "rc", "bbox": box, "text": body, "font_size": 10.5} for key, box, body in notes],
    }
    report = render(plan, out / "synthetic-rc-annotated.pdf")
    calc = calculate({"id": "rc", "kind": "rc", "inputs": {"r_ohm": 10000, "c_f": 1e-6, "threshold_fraction": .7}, "assumptions": ["Ideal unloaded RC; C initially discharged; threshold 70%."]})
    expected = -.01 * math.log(.3)
    assert math.isclose(calc["results"]["threshold_time_s"], expected, rel_tol=1e-12)
    assert math.isclose(calc["results"]["fc_hz"], 15.915494309189533, rel_tol=1e-12)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    rendered = fitz.open(out / "synthetic-rc-annotated.pdf")
    assert len(rendered) == 1
    extracted = rendered[0].get_text()
    for marker in ("12.04", "15.92", "R1", "C1", "What changes", "Before applying"):
        assert marker in extracted, marker
    rendered[0].get_pixmap(matrix=fitz.Matrix(1.3, 1.3)).save(out / "preview.png")
    rendered.close()
    result = {"example": "synthetic; not hardware validation", "layout": report, "calculation": calc, "source_unchanged": True, "text_markers_present": True}
    (out / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"passed": True, "output": str(out), "source_unchanged": True}))


if __name__ == "__main__":
    main()
