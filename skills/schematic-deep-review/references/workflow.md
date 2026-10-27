# A standalone method for understanding a complete schematic

This method can be followed without a particular AI product. Its goal is a coherent explanation of the board: what it does, how power and signals move, and why each component is present. The main annotated drawing should explain normal operation on its own. Datasheets, calculations, and check records support that explanation.

The tools perform deterministic PDF, numerical, and bookkeeping work. The analyst remains responsible for connections, device applicability, missing evidence, and the quality of the explanation.

## 1. Establish the source and scope

Inspect the actual input: revision, page count, schematic versus BOM pages, readable text, vectors, and scans. Prefer native connectivity data when it is available and readable, but cross-check it with the visible drawing. An old annotation or similar online schematic is not a connection source.

Store byte-exact originals with SHA-256 hashes. Generate new artifacts from these originals, not by repeatedly annotating a previous output. Keep user circuits local unless external processing is authorized. Preserve the user's existing folder conventions; otherwise use a simple structure:

```text
review-output/
  originals/
  annotated/
  power/
  datasheets/
  excerpts/
  reference-circuits/
  checks/
  reproduce/
  README.md
```

The reader entry page links first to the annotated schematic and power explanation. Explain that `checks/` contains evidence and calculations and `reproduce/` contains tools for rebuilding. Neither should be a prerequisite for learning the circuit. Do not create folders or placeholder PDFs for content that was never obtained.

## 2. Establish the real component denominator

Count actual reference designators from the drawing, including connectors, DNP positions, zero-ohm links, test points, protection, and grounding hardware. Do not infer the total from the largest designator. Distinguish a multi-unit package from its individual symbols and exclude hidden PDF object identifiers.

For each component record source hash/file, page, reference, unit, value, full part number if known, package, manufacturer, group, pins/nets, assembly status, related components, source IDs, explanation, and verification status. Unknown fields remain unknown. A BOM discrepancy is a recorded conflict, not permission to silently rewrite the schematic.

Build functional groups along actual connections: input power, switching, regulation, startup, clocks, control, communication, measurement, and RF. Trace junctions, crossing wires, reused net labels, hidden power units, and off-page connections. PDF text extraction and OCR do not establish connectivity on their own. See [electrical-review.md](electrical-review.md).

## 3. Explain the board, then each interaction

Begin with supported board functions and a useful reading order. Describe each group as a process rather than a list of component definitions. A resistor-capacitor group should explain the charging path, observed node, time constant, threshold if known, and filtering tradeoff. A regulator group includes its enable/feedback network, input/output capacitors, load, and relevant operating states.

Each component or explicitly enumerated group should answer:

1. What does it do in this drawing, and for which load, pin, or signal?
2. How do current, charge, or information move through the group?
3. What do the values mean, and where did the choice or requirement come from?
4. What can be calculated, under which assumptions?
5. What may change if the part is removed or its value changes?
6. Which voltage, current, frequency, timing, thermal, or layout conditions matter?
7. What remains uncertain, and which input would resolve it?

Use [readable-writing.md](readable-writing.md) when turning analysis into annotations. General teaching notes in [the knowledge library](../knowledge/index.md) help explain concepts; they do not replace the exact manufacturer's pin or stability requirements.

Keep evidence categories separate: schematic fact, matching datasheet requirement, reference design, calculation, inference, unconfirmed, and requires measurement. Explain important uncertainty where it affects the drawing; store the full audit trail in supporting records.

## 4. Review the entire power path separately

For full-board work, create a standalone power explanation alongside the main annotated drawing. Follow the actual chain: input → protection/switching → regulation → load domains → battery or rail measurement. Do not invent a converter or power-path controller to complete that pattern.

Cover relevant states such as USB only, battery only, both connected, insertion/removal, low battery, sleep, and peak loads. Explain MOS/BJT control and body-diode paths, input/output capacitors, feedback/enable networks, and ADC divider/filter behavior.

Compute demand at each voltage domain and convert it to the upstream reference before comparing limits. Sustained capacity, dropout, heat, and short transients are distinct checks. A missing battery specification, load waveform, PCB thermal condition, or effective capacitance prevents a guaranteed whole-board current claim. See [power-review.md](power-review.md).

## 5. Obtain and explain matching source material

Use the exact manufacturer, full suffix, package, pinout, and applicable revision. Prefer manufacturer product pages, datasheets, hardware guides, application notes, reference boards, and errata. Similar-family material is explicitly unverified for the exact part.

Every component has a source status. Repeated exact parts may share a document; generic passives without MPNs may only have category guidance. Do not invent per-part manuals. Validate PDF content, page count, model/title applicability, and SHA-256 before calling a download successful.

Extract relevant pin, operating-condition, power, timing, formula, curve, application, layout, and errata content. Keep units, footnotes, conditions, figure numbers, and both PDF and printed page numbers. See [source-policy.md](source-policy.md).

For selected core reference circuits, identify and explain all their components, not just differences from the project. Label the original figure's actual source near its title. First explain its function and operation, then map identical, omitted, added, and changed parts to the project. A reference value is not automatically mandatory.

## 6. Make calculations reproducible

Record the model, formula, related components/nets, inputs and units, evidence, assumptions, outputs and units, and review status. Use SI units in script inputs while retaining the original displayed values. Missing conditions produce a parameterized result or a specific gap, not a fabricated precise number.

Common models, only when the topology supports them:

| Model | Formula and boundary |
|---|---|
| First-order RC | `tau = Rth C`; Rth is the resistance actually seen by the capacitor |
| General RC step | `V(t) = Vfinal + (Vinitial - Vfinal) exp(-t/tau)` |
| Threshold from zero | `t = -tau ln(1 - Vthreshold/Vfinal)`; ideal step, fixed threshold, no extra paths |
| Unloaded divider | `Vout = Vin Rbottom/(Rtop + Rbottom)`; `Rth = Rtop || Rbottom` |
| First-order low-pass | `fc = 1/(2 pi Rth C)`; account for source and loading |
| Resistive loss | `P = I²R = V²/R`; use voltage/current of that branch |
| LDO loss | `P ≈ (Vin - Vout) Iout + Vin Iground` |
| Charge support | `deltaV ≈ integral(Iload - Ireg)dt / Ceff`; add ESR and inductive terms |
| Crystal load | `CL ≈ C1 C2/(C1 + C2) + Cstray`; internal capacitors and actual topology matter |
| Inductor | `v = L di/dt`; check saturation and operating mode |
| RF reactance | `ZL = j omega L`, `ZC = 1/(j omega C)`; parasitics and reference planes matter |

For illustration only, 10 kΩ and 1 μF give tau = 10 ms. Reaching 70% of an ideal supply step takes 12.04 ms, not 10 ms. This is not an arbitrary enable pin's guaranteed startup delay.

RF analysis requires a model before a number. A pi network is not necessarily an impedance match; `1/(2 pi sqrt(LC))` is not the universal cutoff of arbitrary pi networks. Sweep the appropriate two-port model, include actual terminations, and distinguish matching from filtering. No simplified calculation proves antenna performance.

## 7. Produce readable complete-page annotations

Keep every source schematic complete on one annotated page, with explicit accounting for multiple source pages. Preserve source vectors; label scanned inputs honestly. Do not use generative images to reconstruct electrical drawings.

Measure nearby ordinary reference/value text. Start annotations at approximately 0.8–1.1 times that size, then inspect actual glyph height and density. Put explanations by their components in black text, with explicit designators. Do not replace the main explanation with a distant numbered lookup table.

Use existing whitespace first. Simplify repetitive audit prose and group genuinely interacting parts. Add real whitespace if necessary; scaling the entire page does not improve the relative text size. Moving circuit regions requires preserved connections, labels, junctions, boundaries, and recorded mappings. Without netlist comparison, report geometric and visual checks only. See [annotation-layout.md](annotation-layout.md).

## 8. Verify and report honestly

Follow an analyze → compose → render → inspect → repair → re-render loop. Check inventory coverage, BOM conflicts, source validity, page references, numerical models, text overflow, bounds, collisions, glyphs, and preserved source ink. Inspect every final page at overview scale and dense regions at working magnification.

Report four different things separately: explanation coverage, electrical confirmation, tool checks, and physical validation. “All inventory entries explained” does not mean “all requirements confirmed.” “No detected raster changes” does not mean native connectivity equivalence. No hardware measurements means no measured stability, thermal, RF, EMC, or compliance result.

Use [acceptance.md](acceptance.md) for the delivery checklist and [forward-test.md](forward-test.md) for reproducible public tool tests.

## Tool entry points

Run these from the repository root, or adjust paths to the installed skill. All PDF page arguments are one-based. Rectangles are PDF points with a top-left origin.

```bash
python skills/schematic-deep-review/scripts/review.py --help
python skills/schematic-deep-review/scripts/review.py inspect original.pdf --out checks/inspection.json
python skills/schematic-deep-review/scripts/review.py download sources.json --root datasheets --out checks/downloads.json
python skills/schematic-deep-review/scripts/review.py extract datasheet.pdf --page 12 --out excerpts/page-12.pdf
python skills/schematic-deep-review/scripts/review.py calculate calculations.json --out checks/calculated.json
python skills/schematic-deep-review/scripts/review.py qa components.json annotations.json --out checks/coverage.json
python skills/schematic-deep-review/scripts/review.py validate project.json
python skills/schematic-deep-review/scripts/knowledge_search.py "capacitor decoupling"
```

The schema and examples are under [assets](../assets/project.schema.json). Coverage is calculated over the supplied inventory, so inventory completeness needs its own review. PDF layout plans are a separate interface; see [annotation-layout.md](annotation-layout.md) and the runnable synthetic example in the repository.
