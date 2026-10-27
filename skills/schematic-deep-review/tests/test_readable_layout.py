"""Independent CLI checks for readable multipanel plans; synthetic circuits only."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz
from font_fixture import test_font


ROOT = Path(__file__).resolve().parents[1]


class TestReadableLayoutCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="readable-panel-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.font = test_font(self.root)
        self.source = self.root / "two-circuits.pdf"
        with fitz.open() as d:
            p = d.new_page(width=300, height=140)
            p.insert_text((20, 40), "R1 100k", fontsize=10)
            p.draw_line((20, 80), (130, 80), color=(0, 0, 1), width=.6)
            p.insert_text((180, 40), "C1 100n", fontsize=10)
            p.draw_line((180, 80), (280, 80), color=(.96, .96, .96), width=.8)
            d.save(self.source)
        self.source_hash = self.digest(self.source)
        self.output = self.root / "readable.pdf"
        self.plan_path = self.root / "plan.json"
        self.plan = {
            "source": str(self.source), "source_page": 1, "font": str(self.font),
            "canvas_size": [500, 310], "title_box": [10, 4, 490, 32],
            "title": "Synthetic panel regression", "title_size": 12,
            "summary_box": [10, 276, 490, 303], "summary": "Synthetic test only",
            "summary_size": 9, "drawing_label_pt": 10, "font_source_pt": 9,
            "minimum_font_ratio": .8, "scale": 1,
            "panels": [
                {"id": "left", "title": "Left channel", "size": [230, 210],
                 "origin": [0, 0], "pad": [20, 40], "clips": [[0, 0, 150, 140]],
                 "pos": [10, 40]},
                {"id": "right", "title": "Right channel", "size": [230, 210],
                 "origin": [150, 0], "pad": [20, 40], "clips": [[150, 0, 300, 140]],
                 "pos": [260, 40]},
            ],
            "annotations": [
                {"id": "left-note", "panel": "left", "bbox": [15, 165, 215, 195],
                 "font_size": 9, "text": "左侧电路解释 Ω"},
                {"id": "right-note", "panel": "right", "bbox": [15, 165, 215, 195],
                 "font_size": 9, "text": "右侧电路解释 μ"},
            ],
        }

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def invoke(self, plan):
        self.plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
        return subprocess.run([sys.executable, "-X", "utf8",
                               str(ROOT / "scripts/readable_layout.py"),
                               str(self.plan_path), "--out", str(self.output)],
                              capture_output=True, text=True, encoding="utf-8")

    def test_valid_two_panel_cli_repeat_keeps_source_and_one_annotation_copy(self):
        for _ in range(2):
            run = self.invoke(self.plan)
            self.assertEqual(run.returncode, 0, run.stderr)
            report = json.loads(self.output.with_suffix(".layout.json").read_text(encoding="utf-8"))
            self.assertEqual(report["source_sha256"], self.source_hash)
            self.assertEqual(len(report["panels"]), 2)
            self.assertTrue(all(p["changed_source_ink_pixels"] == 0 for p in report["panels"]))
            with fitz.open(self.output) as d:
                self.assertEqual(len(d), 1)
                text = d[0].get_text()
                for expected in ["R1 100k", "C1 100n", "左侧电路解释", "右侧电路解释"]:
                    self.assertEqual(text.count(expected), 1, text)
                self.assertGreaterEqual(len(d[0].get_drawings()), 2)
                self.assertEqual(len(d[0].get_images()), 0)
        self.assertEqual(self.digest(self.source), self.source_hash)

    def test_small_type_and_source_cover_reject_without_replacing_valid_output(self):
        run = self.invoke(self.plan)
        self.assertEqual(run.returncode, 0, run.stderr)
        good_hash = self.digest(self.output)
        report_path = self.output.with_suffix(".layout.json")
        report_hash = self.digest(report_path)
        for mutation, error in [("small", "too small"), ("cover", "covers original ink"),
                                ("canvas", None), ("panel_overlap", None)]:
            plan = copy.deepcopy(self.plan)
            if mutation == "small":
                plan["annotations"][0]["font_size"] = 7
            elif mutation == "cover":
                plan["annotations"][0]["bbox"] = [25, 110, 175, 145]
            elif mutation == "canvas":
                plan["panels"][1]["pos"] = [480, 40]
            else:
                plan["panels"][1]["pos"] = [100, 40]
            with self.subTest(mutation=mutation):
                run = self.invoke(plan)
                self.assertNotEqual(run.returncode, 0)
                if error is not None:
                    self.assertIn(error, run.stderr)
                self.assertEqual(self.digest(self.output), good_hash)
                self.assertEqual(self.digest(report_path), report_hash)
                self.assertFalse(self.output.with_name("readable.pending.pdf").exists())
                self.assertEqual(self.digest(self.source), self.source_hash)


if __name__ == "__main__":
    unittest.main(verbosity=2)
