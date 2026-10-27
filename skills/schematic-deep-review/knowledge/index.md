# Schematic review knowledge index

This is an original English engineering reference for an AI reviewing a schematic. It explains common mechanisms, calculation models, and failure modes. It does not establish the behavior of an unidentified component or validate a particular board.

Read only the relevant topic, then obtain the exact manufacturer's documentation for the parts in the user's design. Follow the actual nets before applying a familiar circuit pattern. A symbol name, reference designator, package outline, or nearby wire is not sufficient evidence of a connection or pin function.

## Retrieval map

| Question or trigger | Read | Useful search terms |
|---|---|---|
| What does this resistor/capacitor do? Why this value? | [Passives and RC networks](passives-and-rc.md) | divider, pull-up, leakage, time constant, decoupling, ESR, ESL, DC bias |
| Is this a power inductor, RF inductor, or ferrite bead? | [Inductors and ferrite beads](magnetics.md) | ripple, saturation, RMS, DCR, resonance, impedance |
| How do the transistors interact? Can current flow when off? | [MOSFETs and BJTs](transistor-switches.md) | gate-source voltage, body diode, base drive, high side, backfeed |
| Can the supply deliver continuous or peak current? | [Power conversion and battery paths](power-paths-and-transients.md) | LDO, buck, boost, thermal, dropout, load sharing, pulse, capacitance |
| Will the MCU start, sample, and communicate? | [MCU, clocks, and interfaces](mcu-clocks-and-interfaces.md) | crystal load, reset, GPIO, I2C, SPI, ADC, power sequence |
| Does the amplifier topology and operating range make sense? | [Operational amplifiers](operational-amplifiers.md) | negative feedback, noise gain, offset, common mode, stability, integrator |
| What was actually read to create these notes? | [Provenance](provenance.md) | source filenames, page ranges, selected reading |
| Are the numerical examples reproducible? | [Example data](examples.json), [validator](verify_examples.py), [validation results](validation.json) | SI inputs, expected outputs, tolerance, dimensional checks |

## How to use a topic in a review

1. **Observe:** record the reference, value, exact part, package, connected pins, and net names. Distinguish fitted, optional, and unpopulated parts.
2. **Explain the function:** describe the current or signal path and the result it creates. Explain how nearby parts cooperate before discussing missing evidence.
3. **Calculate:** state the model, units, input ranges, and assumptions. Mark the result as a calculation, not a measurement. Use effective values and worst-case bounds when judging compliance.
4. **Check the specific part:** verify pin mapping, recommended operating conditions, guaranteed electrical limits, test conditions, errata, and applicable reference circuit. A typical curve or absolute maximum is not a guaranteed operating specification.
5. **State consequences:** explain what changes if a value increases, decreases, is shorted, or is omitted. Keep deliberate design options distinct from faults.
6. **Close the evidence gap:** name the remaining measurement or input that would resolve uncertainty. Avoid repeating generic disclaimers after every sentence.

Use separate evidence labels in project output: **observed connection**, **manufacturer requirement**, **calculation**, **engineering inference**, and **unverified**. Do not turn a general lesson from this directory into a manufacturer requirement.

## Notation and limits

Unless stated otherwise, calculations use volts (V), amperes (A), ohms (ohm), farads (F), henries (H), seconds (s), hertz (Hz), and watts (W). In code and plain text, u means micro: uF = 1e-6 F; nF = 1e-9 F; pF = 1e-12 F. A peak-to-peak quantity is labeled pp; it is not an RMS or one-sided peak quantity.

Every numerical example is synthetic. Examples are not values extracted from a private board. Validation checks arithmetic, selected dimensional identities, internal links, and package hygiene. It does not simulate a real regulator, establish RF performance, certify a battery design, or replace PCB inspection and measurement.

Run the numerical and document checks with standard Python:

    python verify_examples.py

The command is run from this directory and rewrites validation.json. No network access, third-party Python package, or original source PDF is needed.
