"""Independent invariant tests for the vector overlay engine; synthetic sources only."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
import pymupdf as fitz
from font_fixture import test_font

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("layout_engine", ROOT/"scripts/layout_engine.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class TestVectorOverlay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="schematic-layout-tests-")
        self.root = Path(self.tmp.name)
        self.font = test_font(self.root)
        self.source=self.root/"source.pdf"
        d=fitz.open(); p=d.new_page(width=300,height=200)
        p.insert_text((15,25),"R1 100k",fontsize=10)
        p.draw_line((20,120),(270,120),color=(0,0,1),width=.5)
        p.draw_rect((120,115,155,125),color=(0,0,1),width=.5)
        d.save(self.source);d.close()
        self.before=hashlib.sha256(self.source.read_bytes()).hexdigest()

    def tearDown(self): self.tmp.cleanup()

    def group(self, **kw):
        g={"id":"teaching","bbox":[100,40,270,90],"text":"中文 Ω μ π 100 kΩ","font_size":9}
        g.update(kw);return g

    def test_vector_source_ink_and_searchable_chinese_preserved(self):
        out=self.root/"output.pdf"
        qa=engine.build_overlay(self.source,out,[self.group()],self.font,scale=2,extra_bottom=30)
        self.assertEqual(qa["ink_comparison"]["changed_ink_pixels"],0)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.before)
        with fitz.open(out) as d:
            self.assertEqual(len(d),1)
            self.assertIn("中文",d[0].get_text())
            self.assertIn("R1 100k",d[0].get_text())
            self.assertGreaterEqual(len(d[0].get_drawings()),2)
            self.assertEqual(len(d[0].get_images()),0)

    def test_collision_bounds_and_annotation_overlap_rejected(self):
        for groups in ([self.group(bbox=[15,110,280,140])],
                       [self.group(bbox=[280,40,320,90])],
                       [self.group(),self.group(id="duplicate")]):
            with self.assertRaises(ValueError):
                engine.build_overlay(self.source,self.root/"bad.pdf",groups,self.font)
        self.assertFalse((self.root/"bad.pdf").exists())

    def test_font_missing_glyph_and_overflow_rejected(self):
        for group in (self.group(text="\U0010ffff"),self.group(text="long line "*200,bbox=[100,40,115,45])):
            with self.assertRaises(ValueError):
                engine.build_overlay(self.source,self.root/"bad.pdf",[group],self.font)

    def test_source_overwrite_and_implicit_multipage_rejected(self):
        with self.assertRaises(ValueError):engine.build_overlay(self.source,self.source,[],self.font)
        multi=self.root/"multi.pdf"
        with fitz.open(self.source) as d:
            d.new_page(width=300,height=200);d.save(multi)
        with self.assertRaises(ValueError):engine.build_overlay(multi,self.root/"out.pdf",[],self.font)

    def test_repeat_run_does_not_stack_annotations(self):
        out=self.root/"output.pdf"
        for _ in range(2):
            engine.build_overlay(self.source,out,[self.group()],self.font,scale=2,extra_bottom=30)
            with fitz.open(out) as d:self.assertEqual(d[0].get_text().count("中文"),1)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.before)

    def test_autoplace_uses_blank_region_and_reports_impossible(self):
        with fitz.open(self.source) as d:
            groups=[{"id":"possible","text":"中文 Ω","anchor":[150,60],"allowed":[100,40,280,95],"widths":[60]},
                    {"id":"impossible","text":"中文文字"*100,"anchor":[30,120],"allowed":[20,118,30,123],"widths":[8]}]
            placed,failed=engine.autoplace(d[0],groups,self.font,size=8)
            self.assertEqual([g["id"] for g in placed],["possible"])
            self.assertEqual([g["id"] for g in failed],["impossible"])
            self.assertEqual(engine.area_sum(engine.integral(engine.occupancy(d[0])),placed[0]["bbox"],3),0)

    def test_pale_vector_line_is_still_original_geometry(self):
        pale=self.root/"pale.pdf"
        d=fitz.open();p=d.new_page(width=300,height=200)
        p.draw_line((15,55),(280,55),color=(.96,.96,.96),width=1)
        d.save(pale);d.close()
        with self.assertRaises(ValueError):
            engine.build_overlay(pale,self.root/"pale_out.pdf",[self.group()],self.font,scale=2,extra_bottom=0)


if __name__=="__main__":unittest.main(verbosity=2)
