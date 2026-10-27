# Explain power from the input to the loads and measurement

For a full-board review, deliver this explanation beside the annotated schematic. Start with one clear statement of the actual power path and supported conclusions. Use original designators and net names so the reader can follow it on the drawing.

## Trace the actual chain

| Stage | Explain | Components to connect in the explanation |
|---|---|---|
| Input | Which source supplies which rail, under which voltage/current conditions | Connector, source identification, cable, fuse, input capacitors |
| Protection/switching | How sources are selected and what happens during insertion, removal, and loss of one rail | Diodes, MOSFETs including body diodes, BJT drivers, pulls, charger |
| Regulation | Which voltage becomes which voltage, and when regulation is possible | LDO/DC-DC, enable, feedback, input/output capacitors, inductor |
| Load domains | Always-on versus switched loads and shared limits | MCU, radio, display, external interfaces, load switches, local bypassing |
| Measurement | What voltage is measured, how it is scaled, and when a reading is valid | Divider, switch, filter capacitor, ADC input/reference |

Use the actual topology. A charger is not automatically a system power-path manager; an internal chip regulator is not automatically available to external loads. A net named 3V3 is not proof that it remains 3.3 V under low battery or overload.

## Turn component lists into a sequence of actions

Explain what each protective part actually does and which path it serves. USB connector presence, CC resistors, and a “2 A” fuse do not alone establish permission or capacity to draw 2 A.

For charging, distinguish battery charge current from system current. Determine whether system and charger share the input and whether a system load affects charge termination. Use the exact charger's operating description and connections.

For MOS/BJT controls, state who pulls which node high or low and why that opens or closes the power path. Explain VGS as gate voltage minus source voltage. Include pulls, default states, control-current limiting, and body-diode paths. “Off” does not imply bidirectional isolation.

An LDO continuously regulates a higher DC voltage down to a lower voltage; much of the excess energy becomes heat. Explain dropout as the input-output headroom needed to maintain regulation. Input and output capacitors buffer disturbances; the output capacitor may also be part of the regulator's stability requirements.

A DC-DC converter transfers energy through switching and, for common inductive topologies, an inductor and capacitors. Explain the actual on/off current paths for the converter type. Describe feedback and enable pins in ordinary language. Check peak inductor current, saturation, switch limits, mode, and efficiency.

For parallel supply capacitors, enumerate the designators and served domain. When load current increases faster than the upstream supply responds, nearby capacitors release charge. They also reduce some supply disturbances and coupling. Their effective capacitance, routing, ESR, and ESL matter; “large for low frequency, small for high frequency” is not sufficient validation.

## Analyze operating states before capacity

Include only relevant states: USB only, battery only, both connected, insertion/removal, low battery, sleep, transmission/display updates, or another specified pulse. For each state record source and path, switch control/default state, rail voltage/regulation status, system/charging demand, and confirmed or missing conditions.

State whether a load scenario is user-provided, measured, datasheet-derived, or a teaching assumption. A 500 mA to 700 mA example is not a measurement unless evidence says so.

## Sustained current budget

Build a load table per rail: part/module, voltage, idle/sleep/active current, conditions, simultaneous activity, pulse duration, and duty cycle. Avoid double-counting a module and its internal devices. Do not compare currents from different voltage domains without conversion.

```text
LDO input current ≈ Iout + Iground
DC-DC input current ≈ Vout Iout / (Vin efficiency)
Resistive/MOS drop ≈ I R; loss ≈ I²R
Diode loss ≈ I VF(I, temperature)
```

Efficiency must match the relevant voltage/load conditions. Add charging demand along the actual shared input path. Compare source limits, cable/connector/fuse losses, battery and protection limits, diodes/MOSFETs, regulators, PCB paths, and heat. Unknown links prevent a guaranteed board-wide rating; a known component limit is only a bound.

For batteries, consider internal resistance, temperature, state of charge, protection, and connector drop. Average current does not validate a peak requirement.

## LDO headroom and heat

```text
Vin_reg_min = Vsource_min - path drops
Required: Vin_reg_min - Vout >= dropout requirement at the actual load/temperature
P ≈ (Vin_reg - Vout) Iout + Vin_reg Iground
TJ ≈ TA + P thetaJA                     [steady-state estimate]
Ithermal ≈ ((TJ_target - TA)/thetaJA - Vin_reg Iground)/(Vin_reg - Vout)
```

TJ is junction temperature, TA is ambient temperature, and thetaJA describes the thermal path to ambient under specified board conditions. Select TJ_target within recommended conditions and the project's margin. Do not use an absolute maximum as an ordinary target. Datasheet thermal resistance depends on the test board; transient heating needs transient thermal data and pulse timing.

**Teaching example only:** at 5.0 V in and 3.3 V out, ignoring ground current, 500 mA dissipates 0.85 W and 700 mA dissipates 1.19 W. With assumed TA = 50°C, thetaJA = 100°C/W, and TJ_target = 105°C, the thermal current boundary is about 0.324 A. An “800 mA” headline would not make this assumed thermal setup suitable for sustained 700 mA.

## Load step: 500 mA to 700 mA

Answer three separate questions:

1. Can the entire supply path eventually sustain 700 mA?
2. Before the regulator responds, how far does the load voltage dip?
3. Between repeated pulses, can the system replenish charge and control temperature?

If the regulator initially supplies the old 500 mA, the incremental deficit begins at 200 mA. It changes as the regulator responds.

```text
deltaQ = integral(max(Iload(t) - Ireg(t), 0)) dt over the deficit interval
deltaV_C ≈ deltaQ / Ceff
Initial ESR contribution ≈ deltaI ESR
Path-inductance contribution ≈ Lpath dI/dt
Ceff >= deltaI deltat / (allowed_drop - deltaI ESR - other_budgeted_losses)
```

The final formula assumes a constant deficit; its denominator must be positive. Ceff is capacitance after bias, tolerance, and temperature effects. The allowed drop depends on load minimum voltage, static losses, regulation accuracy, and margin. Do not invent regulator response time from a generic example.

**Teaching example only:** a 200 mA deficit for 100 μs with 0.1 V allowed drop requires 200 μF if ESR and other losses are ignored. With 20 mΩ ESR, 4 mV is spent on ESR and about 208 μF is needed for the remaining 96 mV budget. At a 1 ms deficit, the ideal requirement is 2000 μF. A 10 μF capacitor supports that 200 mA deficit for only about 5 μs under the ideal 0.1 V budget.

These estimates do not certify loop stability or the actual waveform. A capacitor cannot make up a permanent current shortage. For DC-DC converters also inspect inductor peak/saturation, switch current limit, input demand, and control mode. For example, an assumed 3.0 V input, 3.3 V/0.7 A output, and 90% efficiency imply about 0.856 A input, not 0.7 A.

Conclude “meets,” “does not meet,” or “cannot yet confirm” under stated conditions. If measurement is needed, identify input/output/load-pin probe points, source state, load rise time, duration, repetition, minimum voltage, and recovery behavior.

## Battery or rail ADC measurement

Explain the measured node, divider, switching, filtering, sampling, and reference together.

```text
VADC = Vmeasured Rbottom/(Rtop + Rbottom)     [unloaded ideal divider]
Idivider = Vmeasured/(Rtop + Rbottom)
Rth = Rtop Rbottom/(Rtop + Rbottom)
tau = Rth Cfilter                          [when this first-order model applies]
t_to_fraction_(1-epsilon) = -tau ln(epsilon) [zero-start ideal step]
```

A high-resistance divider saves current but can make acquisition slower and leakage errors larger. The ADC sampling capacitor takes charge; its input drive and acquisition requirements come from the actual device. An external filter capacitor can reduce noise and locally supply sampling charge but adds startup/enable settling time.

Check disabled and unpowered states, clamp/back-power paths, switch drop/leakage, resistor tolerance, and reference error. Measuring battery voltage does not itself provide battery protection.

## Deliver a usable conclusion

A reader should understand who supplies the board after an input is removed, what each regulator does, why the surrounding R/C parts exist, how ADC measurement works, and what is known about the specified current scenario. Keep critical calculations in the explanation; full source tables and numerical records can be supporting files. List missing inputs precisely rather than filling the page with generic warnings.
