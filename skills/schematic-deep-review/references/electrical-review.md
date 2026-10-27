# Component and interaction review

Apply knowledge after establishing connections. A script matching R/C/L prefixes cannot determine a component's role. This checklist supports the analyst; do not compress it directly into reader-facing annotations.

## Identity and completeness

Use source/page/reference/unit identity, with a package grouping for multi-unit symbols. Record original value, full MPN, package, manufacturer, assembly, pins/nets, group, sources, and status separately. Keep BOM conflicts visible. Distinguish DNP components, optional fitted parts, IC NC pins, and actual zero-ohm links.

Count all actual components, including connectors, test points, protection, switches, jumpers, and grounding hardware. Hidden PDF labels and duplicate representations do not increase the physical count.

## Resistors and RC groups

Verify both endpoints and the served pin before deciding among pull-up/down, boot strap, LED/base current limiting, gate control, divider, feedback, sensing, bias, charge setting, timing, termination, discharge, or configuration.

- For pulls, explain the rail and default state during startup, reset, high impedance, and power loss. Check thresholds, leakage, static current, capacitance, and potential back-power.
- For dividers, calculate ratio, current, Thevenin resistance, range, loading, and ADC settling. Battery measurement is not battery protection.
- For LEDs, use the branch current direction, forward-voltage range, driver loss, and resistor power. Missing LED identity means unknown precise brightness.
- For series signal resistors, assess damping or termination in the actual driver/load/layout context. “In series” does not automatically mean DC current limiting.
- For PROG/FB pins, obtain the formula and coefficient units from the exact device, not a similar package.
- For zero-ohm links, explain the supported configuration or measurement role and distinguish inference from documented intent. They still have finite resistance and ratings.

For an RC network, identify the charging/discharging path and observed node. Use the resistance actually seen by the capacitor. Tau describes response speed; a threshold, initial/final voltage, and input waveform are needed for action delay. State filtering and response-time tradeoffs.

## Capacitors

Distinguish input/output bulk support, supply decoupling, internal supply/reference pins, RC timing, coupling, crystal loads, RF matching, snubbers, compensation, bootstrap, soft-start, and charge pumps.

An internal regulator capacitor is not interchangeable with ordinary bypassing. Confirm exact pin requirements for value, tolerance, stability, and layout. Explain which internal function it serves; a technical node label is not the explanation.

For parallel supply capacitors, list each designator and served load. Explain nearby charge support and reduced disturbance, the possible effect of removal, and how effective capacitance/parasitics affect performance. Do not assume more capacitance is always acceptable; startup, inrush, and loop stability may constrain it.

Check maximum actual node voltage including relevant transients, DC bias, tolerance, temperature, ESR/ESL, and package. Do not invent effective capacitance without an applicable part curve. A low-voltage board input does not imply every generated internal or display rail is low voltage.

## Inductors and ferrite beads

The L prefix does not guarantee an inductor. Identify energy-storage inductors, RF inductors, beads, common-mode chokes, transformers, or zero-ohm placeholders.

Storage inductors require ripple, peak current, saturation, temperature-rise current, DCR, and converter mode checks. RF parts require Q, self-resonant frequency, package, reference plane, and frequency context. A bead's impedance at one frequency is not a constant resistance or inductance.

## MOSFETs and BJTs

Verify actual part, polarity, package, and pin mapping. Explicitly identify a symbol/datasheet conflict before reasoning from the symbol.

Trace gate/source/drain and body diode. For relevant states, record control high/low/high-impedance, external source present/absent, one side unpowered, gate and source voltages, VGS, conduction assumptions, diode paths, and supplied load. A single off MOSFET is not automatically a bidirectional blocker.

VGS(th) is measured at a small current; use RDS(on) at the actual gate drive for load conduction. For dynamics, consider gate charge, Miller charge, and driver conditions rather than forcing a fixed linear RC model onto every transition.

Explain gate/base resistors and pulls together: default state, charging/discharging, damping, current limiting, turn-off, and loss. Typical BJT gain is not a reliable saturation guarantee. Back-power paths may include I/O clamps, ESD devices, regulator reverse paths, and body diodes; verify the actual circuit and device behavior.

## Diodes, TVS, and fuses

Mark anode/cathode and paths for relevant states. Separate rectification, source selection, flyback, clamping, reverse-polarity handling, and transient protection. Check voltage/current/temperature conditions, leakage, surge, power, and junction capacitance on data/RF lines.

A label such as “6 V 2 A” does not identify a fuse as resettable PPTC. Protection coordination requires actual models, time/current behavior, clamp voltage at the relevant current, upstream fault limits, and protected-device ratings. Do not claim a tested ESD or safety level from a schematic alone.

## ICs, clocks, and interfaces

Explain the IC's system role and actually used functions, power domains, reset/enable, straps, clocks, and low-power retention. Do not mechanically translate the entire pin table.

Distinguish a crystal from an active oscillator. For crystals, verify frequency, load capacitance, ESR, drive level, internal/external capacitors, and parasitics. Unknown CL prevents validation of exact pF choices.

For interfaces, state pin roles, voltage levels, power direction, ground, hot-plug/unpowered conditions, and protection. For USB-C, separate VBUS direction, CC role, data routing, damping, ESD, and shield connection. A connector alone does not establish available current or protocol compliance.

For modules, displays, memory, and antennas, obtain the applicable specification; an interface or silhouette is not proof of internal controller or performance. Explain test points, buttons, LEDs, jumpers, and shield contacts by their actual served network.

## Review conclusions

Separate confirmed facts, supported inferences, missing parameters, and items requiring measurement. Check whether “required,” “recommended,” “typical,” and “starting value” were distinguished correctly.

For a power path, use [power-review.md](power-review.md). For writing beside the circuit, use [readable-writing.md](readable-writing.md). Retain unresolved conditions plainly; do not conceal them in jargon or silently modify the source.
