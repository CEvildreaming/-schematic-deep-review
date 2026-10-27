# Regression tests

Run from the repository root with Python 3.10 or newer:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s skills/schematic-deep-review/tests -v
```

Fixtures are synthetic PDFs, records, Markdown files, ZIP files and a local HTTP server. Tests do not upload user files or contact GitHub. Download failures use controlled responses; passing those tests does not verify live GitHub availability.

Layout and text round-trip tests use the CJK font bundled with PyMuPDF. The font is written only to a temporary test directory and removed afterward. Core layout tests do not skip when Windows fonts are unavailable. No font binaries are distributed in this repository. CI is configured for Linux, Windows and macOS with Python 3.10 and 3.12; a workflow definition alone is not evidence that a platform run passed.

The original tool tests cover formula back-substitution, duplicate reference designators across files, DNP and zero-ohm coverage, missing part numbers, BOM conflicts, PDF validation, scanned pages, vector excerpts, download/cache version handling, Chinese glyphs and layout constraints. Layout checks include source hashes, source ink preservation, repeated generation, clipped and pale vector paths, bounds, minimum font size and overlapping annotations. Failed rendering must preserve an existing valid output.

Installer tests cover nested GitHub-style and repository-content ZIPs, existing destinations, path traversal, Windows paths, symbolic-link entries, duplicate/case-colliding paths, file/directory conflicts, invalid ZIPs, size limits, timeout and HTTP failures, partial-copy cleanup, and an actual standard-library-only offline CLI installation. Knowledge search tests cover Chinese terms, Unicode/case normalization, all-keyword matches within one section, headings, source line numbers, excerpts, fenced code and JSON CLI output.

Use `install.py --zip archive.zip --dest temporary-skills-directory` to inspect a release ZIP without writing to the real user skill directory. Existing skills are never overwritten. Machine-specific test logs, runtimes, fonts and Python caches must not be committed here.

Synthetic tests cannot establish complete identification, electrical correctness or physical-board operation. Real projects still require original-connection checks, exact part/version applicability and rendered-page inspection. PDF checks are not native-netlist equivalence or hardware validation.
