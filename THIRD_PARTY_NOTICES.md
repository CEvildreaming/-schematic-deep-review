# Third-party material and dependencies

The MIT license applies to this repository's original code and documentation. It does not relicense manufacturer datasheets, external learning documents, fonts, or software dependencies.

## Reference material

The knowledge library contains independently written explanations, formulas, examples, and review guidance. Its [provenance record](skills/schematic-deep-review/knowledge/provenance.md) identifies the learning material consulted and the reading scope. Original learning PDFs, private schematics, downloaded manufacturer manuals, and personal correspondence are not included.

When the skill collects datasheets for a user's project, preserve the publisher's title, authorship, copyright notices, revision, URL, and document hash. Those documents remain separate project inputs. Check their terms before redistributing a generated project bundle publicly; downloading a document does not make it part of this repository's MIT license.

## Runtime dependencies

Dependencies are installed separately and retain their respective licenses:

| Dependency | Use | Upstream |
|---|---|---|
| PyMuPDF | PDF reading, extraction, rendering, vector composition, font checks | [PyMuPDF](https://pymupdf.readthedocs.io/) |
| NumPy | Raster and layout calculations | [NumPy](https://numpy.org/) |
| Pillow | Image handling in tests and tooling | [Pillow](https://python-pillow.github.io/) |
| jsonschema | Structured project validation | [jsonschema](https://python-jsonschema.readthedocs.io/) |

PyMuPDF offers AGPL and commercial licensing; consult its current terms for your use and distribution. This repository does not bundle these packages or grant additional rights to them.

An independent PDF renderer such as Poppler is recommended for final visual QA and has its own license. Use a locally available font with appropriate embedding rights and the glyphs needed by the output language. No operating-system font files are redistributed here.
