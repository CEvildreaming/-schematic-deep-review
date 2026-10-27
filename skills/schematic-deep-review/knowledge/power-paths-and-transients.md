# Power conversion, battery paths, and transient current

Use this note to trace where energy enters, which path carries it, and which loads share each limit. Reading context: P1 and P2 in [provenance](provenance.md). All numerical examples are hypothetical.

## Start with rails and operating states

Make one row per distinct supply rail. Record its source, protection and series components, regulator, voltage range, enabled states, and loads. Distinct outputs from two 500 mA regulators do not create a 1 A source for either rail. Do not parallel outputs unless their manufacturers support the chosen current-sharing arrangement.

For each rail, assess the intersection of the regulator's guaranteed operating envelope, thermal capability, available input headroom, upstream current budget, interconnect limits, and transient response. A shorthand is:

    usable current <= min(guaranteed electrical capability,
                          thermal capability, headroom capability,
                          upstream and path capability)

The bounds interact and vary with voltage, temperature, and time; this is not a single universal nameplate number. Absolute-maximum current is not a recommended continuous operating point. A typical current-limit value is not a guaranteed deliverable output current.

## An LDO trades voltage for heat

A low-dropout linear regulator adjusts a pass element to hold its output. It needs sufficient input headroom at the actual load and temperature. If the input falls too close to the output, the regulator enters dropout and the output can fall below its target. A battery-fed 3.3 V LDO does not hold 3.3 V throughout an arbitrary battery discharge range.

For a simple regulator whose input current is approximately Iout + Iq:

    Ploss approximately (Vin - Vout) * Iout + Vin * Iq
    efficiency approximately Vout * Iout / (Vin * (Iout + Iq))
    Tjunction approximately Tambient + Ploss * theta_JA
    Ithermal approximately [Pallow - Vin * Iq] / (Vin - Vout)

The last expression assumes positive headroom and a valid allowed-dissipation estimate. Theta_JA is specific to a thermal test setup and board conditions; do not transfer it blindly to a different enclosure or copper area. For a short pulse, use transient thermal impedance and pulse conditions when supplied, rather than treating steady-state theta_JA as a complete pulse model.

TI's [Semiconductor and IC Package Thermal Metrics, SPRA953D, section 1](https://www.ti.com/lit/an/spra953d/spra953d.pdf) explains why junction-to-ambient thermal resistance depends on the test environment. Its [LDO basics: Thermals](https://www.ti.com/video/5845988024001) relates this issue to regulator dissipation and package selection.

Example: 5 V to 3.3 V at 0.3 A dissipates about 0.51 W, ignoring Iq. At 0.6 A it dissipates about 1.02 W. An illustrative 100 degrees C/W thermal resistance would produce rises of 51 and 102 degrees C. With a 50 degrees C ambient and a chosen 110 degrees C design limit, the same simplified thermal budget is 0.6 W or about 353 mA. These assumptions do not qualify a real package.

Check minimum effective input/output capacitance, ESR windows, enable thresholds, startup, reverse current, and discharge behavior. Low ESR is not universally stable for every LDO. Power-supply rejection depends on frequency, headroom, load, and capacitance; an LDO is not an ideal noise eraser.

## A switching converter transfers energy in cycles

A buck converter reduces voltage; a boost converter increases it. A buck-boost topology can cover an input range above and below its target if the actual implementation supports that range. Controller limits, topology, conduction mode, and component losses determine the practical range.

For ideal fixed-frequency continuous-conduction models:

    Buck: D = Vout / Vin
    Buck: delta_IL_pp = (Vin - Vout) * D / (L * fswitch)
    Buck: Ipeak = Iout + delta_IL_pp / 2
    Boost: D = 1 - Vin / Vout
    Boost: delta_IL_pp = Vin * D / (L * fswitch)

These are lossless first estimates, not universal control laws. Use the chosen controller's equations for real losses, minimum on/off time, current limiting, discontinuous conduction, and mode transitions. A generic efficiency correction to duty cycle does not describe every loss mechanism.

For a nonideal converter, power balance gives:

    Iin_average approximately Vout * Iout / (efficiency * Vin)

A hypothetical 5 V, 0.5 A output from 3 V at 90% efficiency draws about 0.926 A average input. A boost switch-current rating is therefore not the same as its output-current rating.

Example buck: 12 V to 3.3 V, 500 kHz, and 10 uH gives D = 0.275 and approximately 0.4785 A pp ripple. At 1 A load, peak inductor current is approximately 1.23925 A. Verify inductance under bias, saturation margin, RMS heating, and the controller's guaranteed minimum current-limit threshold. Also check startup and fault peaks.

For an ideal buck with small inductor ripple and a locally supplied pulsed input current:

    I_Cin_rms approximately Iout * sqrt(D * (1 - D))
    delta_Vout_pp approximately delta_IL_pp / (8 * fswitch * Cout)
                              + delta_IL_pp * ESR

The square root in the RMS expression matters. At D = 0.5 and Iout = 1 A, its result is 0.5 A. The ripple-voltage expression assumes triangular capacitor current and treats the ESR contribution as an approximate added amplitude; actual waveform phase and parasitics affect the sum. It does not size capacitance for a long load step.

Keep high di/dt commutation loops compact and the switch node away from sensitive signals. Identify the loop by comparing switch-on and switch-off current paths. Never describe the intended operation as both half-bridge switches conducting simultaneously; that is shoot-through.

## Capacitors cover the temporary current deficit

When load current rises faster than the supply can respond, the capacitor supplies the difference. The general charge model is:

    delta_Q = integral(Iload(t) - Isource(t), dt)
    delta_Vcapacitive = delta_Q / Ceffective
    delta_VESR approximately delta_I * ESR
    delta_Vinductive approximately Lpath * di/dt

For a constant deficit, C >= delta_I * delta_t / delta_Vcapacitive. State whether delta_t is measured control-loop recovery, a pulse duration, or an assumed scenario. Do not assume the supply contributes zero current without saying so.

Example: a 0.25 A deficit lasting 200 us with 0.1 V allocated to capacitive droop needs 500 uF effective capacitance in this ideal model. A 20 milliohm ESR contributes another 5 mV. If the entire allowed droop is 0.1 V, only 95 mV remains for charge loss, requiring approximately 526.32 uF before inductive and tolerance effects. At 2 ms, the capacitance for the 0.1 V charge-only budget becomes 5000 uF.

A 22 uF effective capacitor supports the same 0.25 A deficit for only 8.8 us at a 0.1 V charge-only droop. Increasing capacitance can help a short transient, but it cannot make an undersized continuous supply adequate. Check recharge time, repetitive pulse duty cycle, inrush, stability, and current limit.

## Battery, external input, and charger interaction

Trace both positive and return paths for battery-only, external-input-only, charging with the system active, input removal, and disabled states. Diodes and MOSFET body diodes can create startup or backfeed paths before a controller turns on. Load-switch shutdown does not prove that signal pins or another connector cannot power the same rail.

For parallel branches behind a linear external-input path, the input budget includes system loads, charging current, and quiescent current. If converters intervene, translate each branch by power and efficiency instead of simply adding output currents at different voltages.

A charger connected to a battery node shared by the system may see load current in its termination decision. A dedicated system/power-path function can manage this differently. Identify the actual charger architecture before claiming that a diode or MOSFET provides complete load sharing. An input from a solar panel does not prove maximum-power-point tracking.

Charging control, cell protection, reverse-polarity protection, and source selection are distinct functions. Use the specified cell chemistry and pack limits; a connector label alone does not identify a safe charging voltage or current. Battery life estimates must include sleep leakage, radio duty cycles, conversion losses, usable capacity, temperature, and discharge cutoff.

## What establishes adequate current capability

Require exact regulator and power-path parts, guaranteed limits over relevant conditions, effective capacitance, load waveforms, PCB thermal information, source limits, and measurements at the load pins. Report a calculation as conditional until these inputs are known. A typical headline current, a protection threshold, or two regulator names cannot by itself establish continuous or burst capability.
