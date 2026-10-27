# Sources, downloads, excerpts, and applicability

Read this before collecting or quoting technical material.

## Match the device before accepting evidence

Confirm full manufacturer part number, suffix, package, pinout, and relevant revision. A generic value is not a manufacturer part number. Similar-family documentation may be useful, but remains unverified for the exact component.

Prefer manufacturer product pages, datasheets, hardware guides, application notes, reference designs, and errata. If using an authorized or otherwise traceable mirror, identify it as a mirror rather than calling its domain official. Record access failures; do not bypass access controls.

Every component needs a source status. Exact repeated parts may share one document. Generic passives without an MPN can use category guidance with that limitation stated. A downloaded file is not automatically an applicable source.

Old annotations and learning materials can inform explanation style and general concepts, but their device-specific conclusions must be checked again. Fixed “rules of thumb” for layout distances, derating, thresholds, or capacitance are not universal device requirements.

## Download and archive

Validate PDF magic, successful parsing, nonzero page count, model/title content, and revision applicability. A successful HTTP status is insufficient; reject HTML login/error pages and damaged files.

Use temporary files until validation succeeds. Record a SHA-256 hash and retain distinct manufacturers, document types, and versions without overwriting them. Repeated runs should reuse a hash-verified cache. Never create empty PDFs to represent unavailable sources.

Use descriptive filenames such as `<part>_<document>_<revision>.pdf`. If a helper's default naming contains an “explanation” suffix, clarify that the downloaded PDF remains the unmodified publisher document, or set an explicit `local_path` in the manifest.

A source record should contain source ID, title, publisher/manufacturer, applicable part numbers, document number/type, revision/publication date if known, source URL, retrieval date, source tier, relative local path, size, pages, hash, applicability status, related components, key pages, and failure reason when relevant. Retrieval date is not publication date.

## Extract useful context

Select only content needed by the review: pins, recommended operation, relevant maximum ratings, startup, capacitor/stability requirements, formulas, curves, application circuits, layout, and errata. Preserve conditions, units, footnotes, and variant restrictions. Absolute maximum ratings are not a normal operating range.

Record source ID and hash, one-based PDF page, printed page label, section/figure, crop rectangle, coordinate units, and subject. Preserve original vectors when available. Keep all circuit labels, junctions, grounds, values, and relevant context. A high DPI setting alone does not restore detail absent from a scan.

Do not redraw a supposed manufacturer circuit with an image generator. A crop is acceptable when complete and clearly identified as an excerpt. Find reference circuits in hardware guides or reference boards when a datasheet lacks them; record the gap when no applicable reference is found.

## Explain reference circuits before comparing

Near the figure title state its true origin, for example:

> Original manufacturer datasheet figure: publisher, document, revision, PDF page, printed page, figure number. Explanations added for this review.

Use “application note” or “reference board” if that is the actual source. The reader should not have to guess.

Inventory the reference circuit's own components and explain its power/signal flow, every component's role, required versus optional parts, useful calculations, and applicable conditions. For unnumbered parts, label any teaching IDs as additions to the explanation layer.

Then compare the reference with the project: identical, omitted, added, and changed connections/values; supply, load, frequency, and package differences. Unsupported reasons remain inferences. A copied reference circuit is not evidence of measured stability, RF performance, EMC, or certification.

## Public packages

Keep user schematics, received files, manufacturer PDFs, and verbatim learning-document extracts outside the reusable skill. Public knowledge notes should be independently written, with concise source provenance and explicit boundaries. A project's generated archive needs its own review before public redistribution.
