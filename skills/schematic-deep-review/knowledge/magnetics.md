# Inductors and ferrite beads

Use this note to distinguish energy storage, RF matching, and loss-based noise suppression. Reading context: P1 and P2 in [provenance](provenance.md).

## Inductors resist changes in current

For an ideal linear inductor with the passive sign convention:

    v = L * di/dt
    E = 0.5 * L * I^2
    Z = j * 2 * pi * f * L

The model applies over a limited frequency and current range. Winding resistance causes heating; core loss and saturation alter behavior; parasitic capacitance causes self-resonance. Above a self-resonant region the part may behave predominantly capacitively. A nominal inductance alone is insufficient for either a converter or RF design.

Separate two current checks. **Saturation current** describes a specified decrease in inductance under DC bias; the percentage and temperature are manufacturer-defined. **Temperature-rise current** describes heating under stated conditions. Check the peak waveform against inductance-versus-current data and the RMS waveform against thermal limits. A current marked 1 A can mean different tests in different product families.

For a triangular ripple around a positive DC current:

    Ipeak = Iaverage + delta_I_pp / 2
    Irms = sqrt(Iaverage^2 + delta_I_pp^2 / 12)
    Pcopper approximately Irms^2 * DCR

Example: 1 A average with 0.4 A pp ripple gives 1.2 A peak and 1.00664 A RMS. With 80 milliohm DCR, copper loss is approximately 81.07 mW. Core and AC winding losses are additional. Startup, a short circuit, or a current-limit cycle may impose a larger peak than normal operation.

## Match the model to the topology

An inductor between a regulator switch node and its output is commonly a buck energy-storage element. An inductor in an RF path may instead form an impedance transformation or resonance with nearby capacitance and device parasitics. The same schematic symbol does not imply the same design criteria.

An ideal isolated LC resonance is:

    f0 = 1 / (2 * pi * sqrt(L * C))

For 10 uH and 1 nF, f0 = 1.59155 MHz. This number is not automatically the cutoff, impedance match, or antenna frequency of a loaded multi-element network. Establish whether elements are in series, parallel, or a different arrangement by tracing both ends. Source and load impedance, losses, PCB parasitics, and other reactive elements affect the response. RF validation normally requires an applicable reference layout and measurements or a credible network model.

Changing L in a switching supply changes ripple, current peaks, transient response, and potentially control-loop behavior. Changing an RF inductor shifts impedance and resonance. Shorting it may preserve DC continuity while destroying the intended AC function.

## Ferrite beads have frequency-dependent loss

A bead is described by a complex impedance Z(f) = R(f) + jX(f). In a useful suppression band, a substantial resistive component dissipates unwanted high-frequency energy. At low frequency, its DCR may be small. A marking such as 600 ohm at 100 MHz is neither 600 ohm DC resistance nor a flat impedance over frequency.

Check the impedance curve at the unwanted frequencies and at the expected DC bias. Check DCR voltage loss and heating separately. For 0.6 A through an assumed 0.15 ohm DCR, the drop is 90 mV and DC loss is 54 mW. A bead that meets a heating limit can still lose useful high-frequency impedance under DC bias.

A bead with load-side decoupling can reduce conducted noise between two supply regions. Its interaction with capacitors can also create resonance and transient droop. A bead is not a drop-in replacement for a converter's power inductor. A two-capacitor pi arrangement is one possible filter, not a requirement for every bead application.

## Return paths and coupled inductors

Follow both the outgoing current and its return. Do not insert a bead into a signal reference or split a ground plane solely because a circuit has both analog and digital functions. Added return impedance can increase voltage error and force high-frequency current into a larger loop. Use the actual converter, ADC, or MCU layout guidance and the board's current paths.

A common-mode choke uses coupled windings to present different impedances to common-mode and differential-mode current. The winding dots and current directions matter. Leakage inductance, imperfect coupling, and winding capacitance mean its differential effect is not zero. On a data interface, verify signal integrity as well as the intended noise suppression.

## Evidence to request

Use exact magnetic-part identifiers, impedance/bias curves, saturation and heating definitions, DCR tolerance, and converter requirements. A schematic cannot establish core temperature, loop area, or EMI compliance. Keep a calculated ideal resonance distinct from measured network behavior.
