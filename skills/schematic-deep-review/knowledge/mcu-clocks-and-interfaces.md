# MCU power, clocks, reset, and interfaces

Use this note to connect the MCU's operating requirements with its supply, clock, control pins, and peripherals. Reading context: P3 in [provenance](provenance.md).

## Verify the exact package and supply domains

Map every supply and ground pin, exposed pad, internal-regulator node, reference pin, and battery-backup pin. Package variants may use different pin numbers or functions. An internal regulator's decoupling node is not automatically a supply output for external loads. An internal DC-DC stage may power only the core; it does not necessarily supply the board or increase the external regulator's capacity.

Use the part's required capacitor values and layout. A general rule of one 100 nF capacitor per supply pin cannot override a pin-specific requirement or a newer silicon revision. A ferrite bead on an analog supply needs a current, impedance, and transient analysis; splitting the ground reference is not a default remedy for ADC noise.

For each GPIO, check voltage tolerance while powered and unpowered, input thresholds, output voltage at load current, per-pin and aggregate current limits, pin multiplexing, and reset state. An input marked 5 V tolerant may have restrictions in analog mode or when the device is off. A resistor plus a protection diode is not automatically an approved level translator.

## Crystal capacitors form a load network

A passive crystal requires an oscillator amplifier. An active oscillator provides an output signal and has its own power and output specifications. Do not substitute one for the other based only on a similar package.

For a simplified two-capacitor crystal network:

    CL approximately C1 * C2 / (C1 + C2) + Cstray
    If C1 = C2 = C: C approximately 2 * (CL - Cstray)

Here C1 and C2 represent the total capacitance of each leg in the chosen model. Some oscillator ICs provide substantial, asymmetric, or programmable internal capacitance. Include it in the correct leg and do not count it again in Cstray. The crystal's specified CL is a target external loading condition; it is distinct from its shunt capacitance C0.

Example: a target CL of 10 pF and an assumed combined stray contribution of 2 pF gives equal external legs of 16 pF when internal leg capacitance is neglected. This is an initial estimate, not proof of startup or frequency accuracy. Confirm the actual IC model, crystal ESR, drive level, startup margin, temperature, and PCB parasitics. Probe capacitance can change the oscillator being measured.

Clock error includes initial tolerance, temperature drift, aging, and oscillator loading. An illustrative 20 ppm constant error accumulates 1.728 seconds per day. Interface clock requirements must be taken from the specific protocol implementation; there is no universal UART or USB crystal tolerance for every design.

## Reset and boot state must agree with the supply sequence

Identify reset polarity, thresholds, internal pulls, minimum pulse width, brownout behavior, and boot-strapping pins. For an RC release from zero with a step supply:

    trelease = -R * C * ln(1 - Vthreshold / Vsupply)

With R = 47 kohm, C = 100 nF, and a hypothetical threshold of 0.7 * Vsupply, release occurs after approximately 5.65867 ms. A slow supply ramp, a short power interruption, or leakage can give a different result. An RC delay does not monitor voltage with the same defined thresholds as a supervisor. Conversely, an external supervisor is not mandatory when the MCU's internal reset system already meets the application's conditions.

Check that boot straps settle before sampling and that attached peripherals or a debugger do not override them. Preserve a practical recovery/programming path. Interpret pull-ups and pull-downs in the power domain to which they actually connect.

## Open-drain buses need a pull-up interval

An open-drain output actively pulls low and releases for high. The total pull-up resistance must satisfy both low-level drive and rise-time requirements. For a first-order RC rise from 30% to 70%:

    tr = ln(0.7 / 0.3) * Rpullup * Cbus
       approximately 0.8473 * Rpullup * Cbus
    Rmax = tr_allowed / (0.8473 * Cbus)
    Rmin = (Vpullup_max - VOL_max) / IOL_guaranteed

Use the weakest participant's guaranteed sink behavior and include all parallel pull-ups. Confirm that the final high voltage, leakage, bus capacitance, and each device's timing limits are compatible. Active rise-time accelerators and some high-speed modes need different analysis. NXP's [UM10204, Rev. 7.0, section 7.1, PDF page 50](https://www.nxp.com/docs/en/user-guide/UM10204.pdf) derives the passive pull-up calculation.

Example assumptions: 3.3 V pull-up, VOL <= 0.4 V at 3 mA, Cbus = 100 pF, and tr_allowed = 300 ns. The approximate interval is 967 ohm to 3.541 kohm. A 2.2 kohm nominal resistor gives tr approximately 186.4 ns and 1.318 mA at VOL = 0.4 V, before tolerance and additional loads. The example demonstrates the calculation; it is not a universal resistor recommendation.

## SPI and UART require electrical and timing checks

For SPI, identify the controller's clock and output signals, peripheral data output, chip-select polarity, mode, maximum clock, and setup/hold requirements. A shared data output must release when its peripheral is deselected. A flash pin labeled HOLD in a generic symbol may be RESET or another function in a specific ordering option. Read the exact part's pin table.

Series resistors can damp a fast edge when placed near the relevant driver, but determine their value from the driver's impedance, trace, receiver, and required timing. Edge time and trace delay matter, not merely clock frequency. Do not impose arbitrary equal-length routing on every slow SPI connection or assume every long connection is acceptable below a fixed frequency.

UART logic-level signals, RS-232, and RS-485 are different electrical interfaces. A matching baud-rate setting does not make their voltage levels compatible. For bidirectional buses, inspect direction control, termination, biasing, and the reference path for the chosen transceiver and topology.

## ADC settling and switched peripherals

An ADC input often draws short sampling-current pulses. The divider's Thevenin resistance, internal switch resistance, sampling capacitance, and acquisition time determine settling. A simple first-order error model is:

    remaining_error_fraction = exp(-tacquire / (Rtotal * Csample))
    tacquire >= (N + 1) * ln(2) * Rtotal * Csample

The second expression gives at most half an LSB residual from a full-scale step for an ideal N-bit conversion. It assumes a single RC pole and excludes other ADC errors. For N = 12, Rtotal = 10 kohm, and Csample = 10 pF, the model requires approximately 0.9011 us. Use the actual ADC acquisition specification or model; external filter capacitors, channel switching, input buffers, and kickback can alter the result.

When a peripheral rail is switched off, check every connected signal for back-powering. Set firmware states, pull-up rails, and any isolation so that the unpowered device remains within its limits. Sleep current includes divider current, low-state pull-ups, reverse leakage, regulator quiescent current, debugger paths, and enabled clocks. Confirm it in the intended operating state, not just from the MCU's headline sleep-current figure.
