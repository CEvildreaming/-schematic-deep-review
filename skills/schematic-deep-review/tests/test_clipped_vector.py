import sys,unittest
from pathlib import Path
import pymupdf as fitz
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from layout_engine import occupancy

class ClippedVectorTest(unittest.TestCase):
    def test_hidden_paths_do_not_block_blank_margin_but_light_visible_strokes_do(self):
        src=fitz.open();p=src.new_page(width=300,height=200)
        p.draw_line((150,0),(150,100),color=(0,0,1),width=1)
        p.draw_line((50,20),(50,80),color=(.96,.96,.96),width=.5)
        out=fitz.open();q=out.new_page(width=320,height=300)
        q.show_pdf_page(fitz.Rect(100,100,200,200),src,0,clip=fitz.Rect(0,0,100,100))
        mask=occupancy(q,res=3)
        self.assertFalse(mask[150*3,250*3], 'Out-of-clip source line is invisible and must not occupy the margin')
        self.assertTrue(mask[150*3,150*3], 'Visible pale line remains protected')
