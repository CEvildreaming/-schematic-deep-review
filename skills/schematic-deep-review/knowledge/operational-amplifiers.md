# Operational amplifier circuits

Use this note to identify feedback polarity, derive the intended transfer, and then check whether the selected amplifier can operate there. Reading context: P4 in [provenance](provenance.md).

## Start with feedback and operating range

An op-amp changes its output in response to the voltage difference between its non-inverting (+) and inverting (-) inputs. Negative feedback can make those voltages nearly equal while input currents remain small. These are approximations for a stable, linear operating condition with adequate loop gain.

Do not impose Vplus = Vminus when the output is saturated, the input common-mode range is exceeded, feedback is positive, the loop is unstable, or the signal is too fast. Small input current does not mean zero bias current, zero leakage, or unlimited input voltage. A circuit containing an op-amp symbol is not automatically a linear amplifier; it could be used as a comparator, although a given op-amp may not be suitable for that service.

For a voltage follower, apply the signal to the non-inverting input and connect the output to the inverting input. This creates negative feedback. Reversing those input connections creates positive feedback rather than an ordinary follower. Require unity-gain stability and check capacitive-load behavior. The buffer lowers loading on a source; it does not provide galvanic isolation. See TI's [buffer circuit design](https://www.ti.com/tool/CIRCUIT060021) for a manufacturer example.

## Derive gains from defined nodes

For a non-inverting stage, let Rf connect output to the inverting node and Rg connect that node to a low-impedance reference Vref:

    Vout = (1 + Rf / Rg) * Vin - (Rf / Rg) * Vref
    Vout - Vref = (1 + Rf / Rg) * (Vin - Vref)

For an inverting stage, connect Rin from Vin to the inverting node, Rf from output to that node, and the non-inverting input to Vref:

    Vout = Vref - (Rf / Rin) * (Vin - Vref)

The formulas assume negligible input current and a stiff reference. Reference impedance, source impedance, resistor tolerance, and amplifier errors need additional analysis. A mid-supply reference must sink or source the currents that the surrounding circuit sends to it.

Example: Rf = 100 kohm and Rg = 10 kohm produce a non-inverting gain of 11. A 0.2 V input with Vref = 0 V ideally produces 2.2 V. With the same 100 kohm feedback and a 10 kohm input resistor, an inverting stage has a signal gain of -10. For Vref = 1.65 V and Vin = 1.75 V, the ideal output is 0.65 V. Verify that both inputs and the output are within their actual allowed ranges.

## Noise gain is not always signal gain

For the simple resistor-feedback inverting stage, noise gain is 1 + Rf/Rin, while signal gain is -Rf/Rin. Noise gain governs amplification of input offset voltage and, in a simple voltage-feedback dominant-pole model, the bandwidth estimate:

    fclosed_loop approximately GBW / noise_gain
    output_offset_from_Vos approximately noise_gain * Vos

With 1 MHz GBW and noise gain 11, the estimate is 90.91 kHz. An assumed 50 uV input offset contributes approximately 550 uV at the output. These are first estimates: GBW varies, higher poles matter, and current-feedback or decompensated amplifiers need different treatment.

Input bias current produces an input error approximately Ib * Rsource. A hypothetical 20 nA through 100 kohm produces 2 mV. Balancing input resistances can reduce error only when the relevant bias currents track; it can also add noise. Use the device's bias, offset-current, temperature, and input-stage characteristics instead of always adding a matching resistor.

For a sine wave of output peak amplitude Vpeak:

    required_slew_rate >= 2 * pi * f * Vpeak

At 20 kHz and 2 V peak, the mathematical minimum is approximately 0.2513 V/us. Additional margin is needed for distortion and device variation. Passing a small-signal bandwidth check does not prove that the same large-amplitude waveform can be reproduced.

## Single-supply operation and loads

Check input common-mode range, output swing at the actual load, supply range, output current, and overload recovery. Rail-to-rail input and rail-to-rail output describe separate capabilities. An output typically needs some distance from the rails, and that distance depends on load and temperature. A 3.3 V supply does not automatically permit a clean 0 to 3.3 V output.

An ADC input can behave as a switched capacitive load. Driving it may require an isolation resistor, charge reservoir, and adequate settling time. A long cable or large output capacitor can reduce phase margin. Adding a capacitor directly to an unstable output is not a universal cure. Use the amplifier's load guidance and verify the complete feedback and load network.

TI's [SBOA418: Determine Optimal Isolation Resistance for Driving Capacitive Load, sections 2-4](https://www.ti.com/lit/pdf/sboa418) explains the interaction of output impedance and capacitive load, with a worked isolation-resistor example. Its calculation assumes a particular output-impedance behavior; do not apply the example's resistor value to every amplifier.

Feedback capacitors can shape noise gain and bandwidth, but their effect depends on where they connect and on parasitic capacitance. Label each added capacitor's purpose and derive or simulate its effect rather than assuming that any small capacitance improves stability.

## Integrators illustrate why assumptions matter

For an ideal inverting integrator with Rin at the input, feedback capacitor Cf, a constant non-inverting reference, and operation within the output range:

    dVout/dt = -(Vin - Vref) / (Rin * Cf)
    Vout(t) = Vout(0) - integral((Vin(t) - Vref) / (Rin * Cf), dt)

The reference must remain constant for that expression. A constant input difference produces a linear ramp until the output saturates. A parallel feedback resistor makes a leaky integrator with finite DC gain and an exponential settling component; it is a different circuit.

Example: a 0.1 V constant difference, Rin = 100 kohm, and Cf = 10 nF produce -100 V/s, or a -0.1 V change in 1 ms. The initial output, bias currents, offset, and available output swing determine how long integration can continue. A reset switch can initialize the capacitor but introduces charge injection and leakage.

## Evidence and diagnosis

Explain the intended signal path and transfer first. Then compare the predicted input/output ranges with the exact device's specifications. Use simulation for an appropriate model and measurements for stability, noise, overload, and settling. A correct ideal gain equation does not prove the circuit has adequate phase margin, dynamic range, precision, or output drive.
