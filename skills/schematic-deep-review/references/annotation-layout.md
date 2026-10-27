# Complete-page annotations and visual QA

The goal is a drawing that is readable, easy to navigate, and faithful to the original connections. Saving a PDF successfully or obtaining zero bounding-box collisions is not enough.

## Preserve the source

Each source schematic page should correspond to one complete annotated output page. Track all source pages explicitly; BOM pages are separate. Do not split one schematic into reading fragments.

Generate from original copies. Preserve vectors when present, and identify scans honestly. Record source hashes, page dimensions, transformations, and crop geometry. Do not reconstruct electrical drawings with generative images.

Prefer existing whitespace. Group genuinely related explanations and remove repeated audit prose before changing layout. If necessary, add real whitespace; uniformly enlarging the page does not improve the annotation-to-drawing ratio. Preserve approximate functional organization.

Moving regions requires checking every boundary for wires, junctions, components, values, and net labels. Record source-to-output mappings. Pixel preservation inside supplied clips says nothing about omitted regions outside them. A native layout edit should be followed by normalized netlist comparison; a PDF-only workflow cannot claim that proof.

## Text and proximity

Use black text, restrained headings, explicit designators, and a consistent font. Put each explanation near its group. Use a short leader only when necessary; a distant numbered table should not carry the main explanation.

Measure ordinary nearby reference/value text, excluding titles, unusually small pin names, and transformed anomalies. Start annotation body text at approximately **0.8–1.1 times** that size. Same nominal point size can look different across fonts, so inspect actual rendering. Do not inherit a small script default as the acceptance criterion.

Embed an appropriately licensed font containing the required glyphs. Test search/copy behavior and symbols such as Ω, μ, and π. Do not redistribute operating-system fonts. Make paragraph widths and line spacing suitable for the output language.

A paragraph normally states designators/function, interaction, key value/calculation, and essential condition. Explain terms at first use. Detailed source IDs and revision tables belong in supporting records, while uncertainty that affects the circuit stays local.

## Source labels and summaries

A reference-circuit title should identify the actual manufacturer document type, title/revision, PDF page, and figure number, and distinguish added explanations from the original figure.

A page summary should describe board function, power path, main module interactions, and a useful reading order. Only the most decision-relevant unknowns belong in that summary; a full audit list belongs elsewhere.

## Overlay helper

Run from the repository root:

```bash
python skills/schematic-deep-review/scripts/layout_engine.py plan.json --out annotated.pdf
```

The JSON plan uses source-page coordinates in PDF points, with a top-left origin:

| Field | Meaning |
|---|---|
| source | Original PDF path |
| source_page | One-based source page; required to choose a multi-page input explicitly |
| font | Local font file with needed glyphs and embedding rights |
| scale | Uniform output scaling; does not create internal whitespace or change text-size ratio |
| extra_bottom | Actual added whitespace below the original, in source points |
| summary | String or array of column strings for that added space |
| groups | Items with id, refs, text, bbox, font_size |
| autoplace | Optional search for whitespace inside each group's allowed rectangle |
| size | Explicit font size for automatic placement; choose after measuring the drawing |

A manual group's bbox is `[x0,y0,x1,y1]`. For automatic placement provide `allowed`, `anchor`, and optional `widths`. The tool finds geometric space near the anchor, but does not decide whether the explanation belongs to that component or is sufficiently intuitive to find.

Map plain designators in the layout plan to the fully qualified component IDs in project records. The helper emits one page per invocation. For multi-page projects, account for every schematic page, run each explicitly, and combine complete pages in source order.

The emitted `.layout.json` contains chosen geometry and source-ink checks. Raster thresholds, rendering resolution, and anti-aliasing limit the check. It is not netlist equivalence.

## Reviewed-region composition

Use `readable_layout.py` when reviewed region boundaries allow extra real whitespace:

```bash
python skills/schematic-deep-review/scripts/readable_layout.py plan.json --out annotated.pdf
```

The analyst supplies the boundaries; this tool is not an automatic circuit partitioner.

| Field | Meaning |
|---|---|
| source, source_page, font | Original PDF, one-based page, local font |
| canvas_size | Final composition canvas width/height before uniform scaling |
| title, title_box, title_size | Page title and geometry |
| summary, summary_box, summary_size | Page explanation and geometry |
| drawing_label_pt | Measured ordinary source reference/value font size |
| font_source_pt | Main annotation size for the summary report |
| minimum_font_ratio | Minimum accepted annotation/source ratio, normally 0.8 |
| panels | Items with id, title, size, origin, pad, clips, pos |
| annotations | Items with id, panel, bbox, font_size, text |
| scale | Final uniform scaling |

Each `clips` entry is a source rectangle. Subtract `origin` and add `pad` to locate it inside the panel; `pos` places that panel on the final canvas. Multiple clips may preserve an irregular boundary, but all edges need review. Do not duplicate a circuit to inflate coverage.

The engine rejects panel/canvas violations, panel/title/summary overlap, annotation collisions, source-ink interference, and undersized annotations. Preserved ink inside clips does not prove all source content was included. Use an independent partition coverage review.

## Render, inspect, repair

Render every final page with an independent PDF renderer such as Poppler. Check the full-page structure and reading order, then inspect dense IC, RF, capacitor, switching, and tight text areas at working magnification. If the drawing labels are readable, the annotation text should also be readable without a separate extreme zoom.

Check text overflow, missing glyphs, clipping, collisions, source-region differences, fonts, copy/search behavior, and all component locations. Bounding boxes may overflag backgrounds and miss fine geometry; document justified exceptions, then inspect pixels.

Repair text or layout, regenerate, and inspect the final version again. The evidence must correspond to the delivered PDF. Record unperformed visual checks and netlist comparisons explicitly. “No known new collision” is not the same as “the original schematic contains no defects.”
