# Knowledge provenance

These English notes are original explanatory writing, not a translation, transcript, or verbatim republication of the reading material. Selected local learning PDFs informed topic selection and were treated as secondary educational material. Their original files, extracted text, diagrams, watermarks, contact details, and private project content are not included in this public knowledge package.

The table records actual selected reading. Page numbers are one-based PDF page positions, not an inferred printed pagination. Headings were also skimmed to locate relevant sections; that skim is not represented as a complete technical review of any document. No full-document reading claim is made.

| ID | Source filename | PDF pages read as relevant text | Pages also checked visually | Reading scope |
|---|---|---|---|---|
| P1 | 1_硬件电路设计学习文档-元器件篇.pdf | 8-9, 11, 30-31, 46-47, 54, 83, 86, 91, 94, 98, 108-109 | 94 | Resistor roles and dividers; RC timing; capacitor charge and decoupling; inductor ratings; BJT and MOSFET switching; power-path illustration; ferrite-bead behavior |
| P2 | 2-电源-LDO_DCDC.pdf | 1, 4-5, 7, 10, 13, 16-18, 23, 27, 35 | 17-18 | LDO headroom and thermal limits; capacitor stability; buck/boost operation; inductor ripple and current; input capacitor RMS; load-step charge balance |
| P3 | 3_硬件设计学习文档-单片机.pdf | 2, 4, 9-10, 14-15, 40-41, 46, 57 | 9 | Supply decoupling and reference paths; crystal loading; reset; GPIO modes; I2C pull-ups; SPI; peripheral shutdown and sleep-current paths |
| P4 | 4_硬件设计学习文档-运放.pdf | 6-11, 20-21, 24-25 | 24 | Gain, offset, bandwidth and slew rate; limits of ideal analysis; feedback polarity; inverting/non-inverting stages; integration; buffer operation and loads |

## Editorial and calculation boundaries

The notes retain established circuit principles while restating them independently and making their assumptions explicit. Fixed-value prescriptions, universal percentage margins, claims of electrical isolation by an ordinary buffer, and blanket rules about ground splitting were not adopted as general requirements.

Several inconsistencies in the selected reading were resolved by circuit equations and dimensional analysis. The buffer illustration and its accompanying polarity description differ; the public note uses output-to-inverting-input negative feedback. A constant input to an ideal integrator produces a linear ramp. A charge-deficit capacitance calculation must have units of farads. A buck input-capacitor RMS estimate includes the square root of D * (1 - D). The public notes do not reproduce the conflicting passages or diagrams.

Manufacturer web references used for narrow cross-checks are linked at the relevant points in the topic notes. Those links do not make the local learning documents manufacturer specifications, and no third-party document is redistributed here.

The numerical examples were newly constructed with generic values. The executable checks cover those examples and selected dimensional identities. They do not validate any real circuit, hardware assembly, source document as a whole, or device operating limit. Consult the actual part's current manufacturer documentation when applying a note.
