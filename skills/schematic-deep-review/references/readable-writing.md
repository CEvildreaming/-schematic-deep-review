# Write explanations that a reader can use beside the circuit

The reader should find the component, understand what it serves, and follow how it works with its neighbors without first opening a manual or an audit log.

## Explain purpose before qualification

Start with the board's supported function, main power and signal paths, and reading order. Group explanations by function rather than by component prefix. Every member of a group still needs an identifiable role.

Use this paragraph sequence:

1. **Designators and purpose:** who helps which chip, rail, or signal do what.
2. **Interaction:** the current/signal/charge path and relevant state changes.
3. **Numbers:** values, a useful result, and the necessary formula or assumption.
4. **Consequence:** what removal or a change may affect, plus a concise essential condition.

Define terms when first used. For example, decoupling means providing nearby short-term current and reducing supply disturbance; an LDO regulates a higher DC voltage down to a lower voltage while dissipating much of the excess energy as heat.

Two reading layers help: the drawing and power explanation contain function, key calculations, and conditions; datasheets, full revision applicability tables, and check records contain supporting detail. An unresolved condition that changes operation must stay beside the affected circuit.

## Original teaching examples

These examples do not describe a particular user's board.

**Parallel supply capacitors:** “C2 and C3 connect between U1's supply and ground. When U1 suddenly draws more current, they release nearby charge and reduce the voltage dip caused by the supply path. They also carry some fast disturbance current through a local loop. The larger capacitance stores more charge; high-frequency behavior also depends on package and routing. Removing them weakens local supply support and may violate the regulator's stability requirements.”

This explains why bypassing, filtering, and charge support can coexist. Do not claim that any large/small pair covers all frequencies; parasitics can produce impedance peaks.

**RC enable network:** “R1 charges C4, so U1's enable voltage rises gradually. With 10 kΩ, 1 μF, an ideal supply step, and a threshold of 70% of the final voltage, tau = RC = 10 ms and the threshold is reached in 12.04 ms. The network also attenuates short disturbances, at the cost of a slower response. Actual startup requires the enable threshold, supply ramp, leakage, and discharge path.”

Do not label tau as the exact action delay or invent an RC delay where the topology does not support one.

**ADC divider:** “R2 and R3 reduce the battery voltage for the ADC, which converts voltage into a digital reading. If both are 100 kΩ, 4.2 V becomes 2.1 V and the divider continuously draws 21 μA. Its 50 kΩ source resistance may require more acquisition time; check the ADC sampling specification.”

**Internal supply capacitor:** Only after confirming the exact pin in the manual: “C1 connects to the chip's internal supply output. It gives that internal circuit a nearby charge reserve and helps keep its voltage stable. This is not a general external power output; capacitance and layout follow this device's requirements.”

“Internal regulator node” alone is not enough. Do not apply this explanation blindly to references, switching nodes, or unrelated DEC pin variants.

**MOS power switch:** Explain which control pulls the gate up or down, how that changes gate-to-source voltage, and which source then powers the load. Include the actual body-diode direction. The threshold voltage indicates a small test current, not full-load conduction.

**Regulator current:** “A 700 mA continuous load must satisfy input headroom, current limits, upstream capacity, and heat limits together. A sudden extra 200 mA also needs temporary support while the regulator responds.” Give a conditional result rather than quoting the headline current rating.

## Uncertainty without clutter

Use a local **[Inference]** label for a supported interpretation that is not confirmed. State the exact missing input: full part number, pin mapping, threshold, battery specification, or PCB thermal condition. Do not replace an explanation with “check datasheet,” “risk,” or unexplained silicon build codes.

If a revision changes whether a capacitor is needed, say what it does first, then “whether this part is required depends on the exact chip revision; confirm the full marking.” Keep the revision table in supporting records.

## Reader check

For every group, ask: can the reader find it; does the first sentence state its purpose; does the action make sense; are unfamiliar terms defined; are numerical conditions clear? Review dense power, internal supply, RC/ADC, and switch groups particularly carefully. Claim an independent reader test only if one actually happened.

Source checks and unchanged drawing geometry are production evidence, not substitutes for component explanations.
