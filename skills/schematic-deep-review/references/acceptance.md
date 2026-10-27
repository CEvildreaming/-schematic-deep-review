# Delivery acceptance and failure handling

This is a checklist, not a claim that a particular run passed. Record each item as passed, failed, not run, or not applicable, with evidence and the exact artifact checked.

| Area | Acceptance |
|---|---|
| Source protection | Source hashes unchanged; revision, page roles, and file provenance identified |
| Reader entry | Direct links to annotated schematic and power explanation; other folders have clear purposes |
| Overall understanding | Main drawing explains board function, power/signal paths, and reading order |
| Component inventory | Real denominator; every actual designator is explainable and locatable, including DNP and protection |
| Interaction quality | Purpose first, each member's role clear, relevant paths/states and useful numbers explained |
| Language | Unfamiliar terms defined; revision conditions readable; unknowns stated locally |
| Power review | Actual path and operating states, sustained/thermal/transient boundaries, and ADC behavior covered |
| Sources | Matching applicable documents or truthful missing/family-unverified statuses; valid files and hashes |
| Excerpts | Traceable page/figure and preserved units, conditions, footnotes, and circuit context |
| Reference circuits | Source clearly labeled; every component explained before project comparison |
| Calculations | Formula, units, assumptions, and evidence allow independent reproduction |
| Complete pages | Each source schematic retained completely on one annotated page; all source pages accounted for |
| Readability | Nearby black explanations, correct searchable glyphs, useful font ratio, no known new clipping/collisions |
| Connection fidelity | Claims limited to the geometry, visual, or native-netlist checks actually performed |
| Final visual QA | Every delivered page and dense area inspected after final generation |
| Reproduction | Re-running preserves originals and cache identity; delivered links resolve |

Coverage measures explained inventory entries, not verified electrical correctness. Report total N, explained C, uncovered N−C, and confirmed/partially confirmed/unresolved conclusions separately. Unknown MPNs do not justify invented manuals.

For current scenarios, identify the rail, waveform, duty cycle, allowed drop, and evidence. Missing effective capacitance, regulator response, or thermal conditions cannot silently become typical values.

## Meaningful tool tests

Use observable behavior and invariants rather than only text matching. Relevant cases include:

- Cross-file identical designators remain distinct; DNP and zero-ohm positions remain in the denominator.
- BOM conflicts and missing MPNs are retained.
- HTML, corrupt files, invalid pages, failed downloads, and conflicting cached sources fail truthfully.
- Scans are distinguished from vector/text sources.
- Calculation models reject invalid parameters and reproduce known independent results.
- Dense annotations, boundaries, source ink, nested clipping, and missing glyphs are checked.
- Multi-page input requires explicit page handling.
- Repeated runs do not mutate originals or stack annotations.
- Installation rejects existing targets and unsafe archive paths.

See [forward-test.md](forward-test.md) and the test commands in the repository README. Automated tests do not establish explanation quality or whole-board electrical correctness.

## Content review

Review every explanation for purpose, location, interaction, terms, and numerical assumptions. Pay special attention to power input, internal supplies, parallel capacitors, RC/ADC networks, and switches.

Reading only the power explanation should reveal source switching, regulator roles, surrounding component interactions, battery measurement, and the supported answer to a load scenario. Reading only an explained reference circuit should reveal its origin and all component roles.

An independent reviewer can improve confidence, but do not claim a blind read or user approval that did not occur.

## Failures and limitations

If a key connection is unreadable, record what is known and request a clearer source or netlist while continuing independent work. If one MPN or document is missing, restrict that conclusion rather than halting unrelated groups.

If a manual conflicts with the source, retain both pieces of evidence and the conditional conclusion. Do not silently repair the original. If rendering fails, fix and rerun the final artifact; do not rename an unchecked draft as verified.

Separate tool tests, schema validation, analyst review, independent rendering, native connectivity comparison, and hardware measurements. Without the relevant evidence, do not claim measured stability, thermal behavior, RF performance, EMC, or compliance.

When a real schematic is supplied for a complete review, tool fixtures alone are insufficient. Run the actual inventory → connections → sources → explanations/calculations → annotations/reference circuits → QA workflow, and identify any blocked stage honestly.
