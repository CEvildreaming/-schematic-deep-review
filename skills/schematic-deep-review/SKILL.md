---
name: schematic-deep-review
description: Explain complete electronic schematics through verified connections, component interactions, power paths, calculations, and manufacturer evidence; collect datasheets and produce readable annotated PDFs. Use for schematic learning, detailed circuit reviews, and evidence-backed documentation, not automatic PCB modification.
---

# Schematic Deep Review

Help the reader understand what a board does, where power and signals flow, and why every component is there. Use the user's language for explanations; preserve part numbers, reference designators, pin names, and net names. Deliver actual files and report actual results. The annotated schematic should explain the basic circuit without making the reader open a datasheet first.

## Start from the requested scope

For a full review, follow [the standalone workflow](references/workflow.md). For a local correction, verify the changed region and update its dependent explanations and checks; preserve unrelated accepted work. Do not expand a small correction into a new whole-board redesign.

Use original schematics as evidence. Native EDA files and netlists can strengthen connection checks when reliably readable; vector PDFs and scans require appropriate visual verification. Save a read-only source copy and SHA-256. Previously annotated drawings are style references, not electrical evidence. Do not overwrite originals or upload private circuits to external services without authorization.

If a part number, connection, or operating condition is missing, continue independent work and state the specific gap. Without an actual schematic, produce only tools, method documentation, and explicitly synthetic test results.

## Analysis workflow

1. Identify the board's supported functions and trace its power and signal paths. Build an actual inventory, including DNP positions, zero-ohm links, connectors, protection, and mechanical grounding. Identity includes source/page/reference/unit; hidden PDF labels are not components. Read [electrical-review.md](references/electrical-review.md).
2. Verify each circuit group from its connections. Explain **which component helps which load or signal, how the group works, what the values mean, and what changes if a component is removed**. Do not assign roles from R/C/L prefixes alone. Use [readable-writing.md](references/readable-writing.md) before drafting annotations.
3. Read relevant topics from [knowledge/index.md](knowledge/index.md), or search them with `scripts/knowledge_search.py`. These are general teaching notes, not evidence for a specific pin, component variant, or value. Read only the topics relevant to the current circuit; confirm device-specific details from the matching manufacturer documents.
4. For a full review, deliver a separate [power-path explanation](references/power-review.md): inputs, protection and switching, regulators, load domains, battery/rail measurement. Analyze relevant source and control states, sustained current, dropout, heat, and load transients. User scenarios and teaching assumptions must not be presented as measurements.
5. Follow [source-policy.md](references/source-policy.md) to locate, download, validate, and archive the matching official datasheets and relevant guides. Every component has a source status; generic passives without MPNs do not get invented datasheets. Extract key content with page, figure, conditions, and footnotes. Explain all components in selected reference circuits before comparing them with the project.
6. Record formulas, units, inputs, assumptions, and results. Use `scripts/review.py --help` for deterministic inspection, download, extraction, calculation, inventory, and layout screening helpers. Scripts do not discover or certify an entire circuit automatically.
7. Follow [annotation-layout.md](references/annotation-layout.md). Keep each source schematic complete on one output page, preserve vector content where available, and place black explanations beside their circuit groups. Start with annotation text about **0.8–1.1 times the nearby reference/value text size**. Create real whitespace when necessary; do not hide dense content in tiny text or distant numbered tables.
8. Run [acceptance.md](references/acceptance.md). Render and visually inspect every final page and dense area. Repair collisions, missing glyphs, clipped content, and unclear explanations, then regenerate and inspect the final files. Without a native netlist comparison, do not claim proven electrical equivalence.

## Evidence and explanations

For JSON evidence records, use the schema keys `schematic`, `datasheet`, `reference`, `calculated`, `inferred`, `unresolved`, and `measurement_required`. Human-facing prose can spell these out as schematic facts, datasheet requirements, reference designs, calculations, inferences, unconfirmed claims, and items requiring measurement. Attach source document and one-based PDF page to device-specific claims. In reader-facing text, use a short local label such as **[Inference]** when needed; do not crowd every sentence with audit tags.

Define unfamiliar terms at first use. “Internal regulator node,” “see datasheet,” or unexplained silicon revision codes are not component explanations. State the purpose first and express revision-dependent conditions in ordinary language. Keep detailed applicability tables and audit trails in supporting records. Preserve conditions that affect the reader's decision next to the affected circuit.

Never treat absolute maximum ratings as recommended operation, a typical application as a guarantee, an RC time constant as an arbitrary chip's exact delay, or a regulator's headline current rating as the board's usable current. If the source and datasheet conflict, show the conflict rather than silently correcting the schematic.

## Deliverables

Use clear names and a short reader entry page that links first to the annotated schematic and power explanation. A full project normally includes:

- Original source copies and provenance.
- Complete annotated schematic pages and a standalone power explanation.
- Matching datasheets, useful excerpts, and explained manufacturer reference circuits.
- Component inventory, source manifest, calculations, annotations, and QA records.
- Reproduction scripts when requested or needed to maintain generated artifacts.

Folder names may follow the user's existing project. Explain that checks and reproduction tools are optional technical supporting material, not the reader's starting point. Do not create empty “downloaded” PDFs or package user circuits and third-party manuals inside this reusable skill.

Report the actual component denominator, explained and uncovered counts, confirmed and unresolved conclusions, source acquisition status, tests performed, unverified capabilities, and missing inputs. Coverage measures explained inventory entries; it does not prove the design is correct. See [forward-test.md](references/forward-test.md) for the public validation procedure and its limits.
