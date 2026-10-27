"""Portable test font: PyMuPDF's bundled CJK face, written only in a temp folder."""
from pathlib import Path
import pymupdf as fitz


def test_font(directory: Path) -> Path:
    path = Path(directory) / "test-cjk-font.ttf"
    path.write_bytes(fitz.Font("cjk").buffer)
    return path
