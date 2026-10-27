# Resistors, capacitors, and RC networks

Use this note to explain a passive component through its two connected nodes and its interaction with the source and load. Reading context: P1 in [provenance](provenance.md).

## Resistors set currents, ratios, and default states

A resistor carrying current dissipates energy. In an approximately ohmic operating region:

    V = I * R
    P = V * I = I^2 * R = V^2 / R

Check continuous power, pulse energy, maximum working voltage, temperature derating, tolerance, and temperature coefficient for the actual series and package. A package code does not guarantee a particular wattage. A universal 50% derating rule cannot replace the applicable curve and product requirements.

For a simple indicator LED, a series resistor approximately sets I = (Vsupply - Vf - Vswitch) / R. Vf changes with current, temperature, and part variation. With an assumed 3.3 V source, 2.0 V LED drop, negligible switch drop, and 5 mA target, R = 260 ohm and P = 6.5 mW. Recalculate current at supply and Vf extremes before choosing a standard value. This model does not apply to an addressable LED's internal driver or an LED requiring regulated current.

A pull-up connects a signal to its positive logic rail; a pull-down connects it to the low reference. A series resistor lies in the signal path. Identify these functions from connectivity, not physical placement. A pull-up provides a default high state only if leakage and connected loads allow it:

    Vhigh >= Vpullup_min - Ileak_total_max * Rpullup_max
    Ilow approximately (Vpullup - Vlow) / Rpullup

An assumed 2 uA leakage through 47 kohm produces a 94 mV drop. Low-state current through a 10 kohm pull-up to 3.3 V is approximately 330 uA when Vlow is negligible. That current flows while the line is low; an unloaded high line does not continuously consume 330 uA. Very large pull-ups save low-state current but make leakage, contamination, coupling, and rise time more significant. Parallel pull-ups combine into a smaller effective resistance.

A zero-ohm link can select assembly variants, join domains, or provide a measurement break. It has finite resistance, current limits, and parasitic inductance. It is not an unlimited-current wire or a guaranteed noise filter.

## A voltage divider also has output resistance

For Rtop from Vin to the output and Rbottom from the output to ground:

    Vout = Vin * Rbottom / (Rtop + Rbottom)
    Idivider = Vin / (Rtop + Rbottom)
    Rth = Rtop * Rbottom / (Rtop + Rbottom)

The expressions assume a stiff input source and negligible output loading. If a resistive load RL connects to ground, replace Rbottom with Rbottom || RL. For maximum divider output with independent resistor tolerances, use the smallest Rtop and largest Rbottom, together with the largest Vin. Include leakage polarity and ADC input behavior separately.

Example: 5 V, 30 kohm above 10 kohm gives 1.25 V, 125 uA, and Rth = 7.5 kohm. A 100 kohm load reduces the output to 1.16279 V. Merely keeping the unloaded voltage below an ADC's range does not prove conversion accuracy; the sampling capacitor must settle during acquisition. Increasing both resistors preserves the ideal ratio but increases source resistance and leakage sensitivity.

## RC networks shape time and frequency

For an ideal source, series R, and shunt C with a high-impedance load:

    tau = R * C
    fc = 1 / (2 * pi * R * C)
    Vc(t) = Vfinal + (Vinitial - Vfinal) * exp(-t / tau)
    t_to_fraction_k = -tau * ln(1 - k)  [zero-to-final step, 0 < k < 1]

With 10 kohm and 100 nF, tau = 1 ms and fc = 159.155 Hz. The node reaches 63.21% after one tau and 90% after 2.30259 ms. A reset delay is the time to the relevant input threshold, not automatically one tau. Supply ramps, leakage, discharge paths, and a slow input edge can invalidate the simplest model.

For a loaded network, calculate the resistance seen by the capacitor with independent sources set to zero. Also recalculate DC gain. A shunt capacitor may reduce noise but delay ADC settling or hold a control pin in an unwanted state. An RC debounce network does not by itself prove that every mechanical contact event creates only one logic transition.

## Capacitors supply local charge and shape impedance

For a constant ideal capacitance:

    Q = C * V
    i = C * dV/dt
    E = 0.5 * C * V^2
    Zc = 1 / (j * 2 * pi * f * C)

Real capacitors also have equivalent series resistance (ESR), equivalent series inductance (ESL), leakage, and dielectric losses. An MLCC's effective capacitance can differ substantially from its nominal label because of DC bias, temperature, tolerance, and aging. Use the selected part's curves; voltage rating alone does not establish effective capacitance.

A decoupling capacitor closes a short local supply-current loop between a load's supply and return. The power and ground connections together determine loop inductance. A bulk capacitor supports longer current deficits. Neither role is established by the label 100 nF or 10 uF alone. Check the IC's required capacitor values, pin-specific connections, regulator stability, package, and placement.

Analog Devices' [MT-101: Decoupling Techniques, pages 1-3](https://www.analog.com/media/en/training-seminars/tutorials/MT-101.pdf) discusses local charge storage, low-inductance connections, and real-capacitor parasitics. Its examples illustrate mechanisms; the selected IC's own requirements remain the component-level design basis.

For a load deficit, the ideal charge calculation is C >= delta_I * delta_t / delta_V. ESR adds an immediate step approximately delta_I * ESR; connection inductance adds L * di/dt. See [power transients](power-paths-and-transients.md) for a worked example. Parallel values can create antiresonance with interconnect inductance; more capacitance is not automatically a better high-frequency network.

## Common mistakes and evidence boundaries

- Do not infer that two capacitors are parallel merely because both have ground symbols. Their other ends must also share a net.
- Do not replace a device's internal-regulator capacitor with a generic decoupling value.
- Do not assume a low-pass network is an anti-alias solution without the sampling frequency and required stop-band attenuation.
- Do not interpret DNP, NC, or a value without a fitted component as a working path. Confirm the assembly variant.
- Removal can affect stability, timing, EMC, or startup even if steady-state DC calculations still look correct. A schematic alone does not show placement or effective high-frequency impedance.
