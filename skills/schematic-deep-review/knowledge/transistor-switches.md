# MOSFET and BJT switching networks

Use this note to explain the control path and load-current path separately, then show how they interact in each operating state. Reading context: P1 in [provenance](provenance.md).

## A MOSFET responds to gate-to-source voltage

Always identify gate, source, drain, and body-diode direction from the exact device pinout and symbol mapping. A rotated symbol does not change the physical pinout. Compare the gate voltage with the source voltage, not automatically with ground:

    Vgs = Vgate - Vsource

For a conventional enhancement NMOS, positive Vgs can turn the channel on. For a PMOS, negative Vgs can turn it on. The threshold voltage only indicates the onset of conduction at the datasheet's small test current. It does not establish a low on-resistance at a GPIO's voltage. Use a guaranteed Rds(on) at an applicable gate voltage, current, and temperature, and respect the gate absolute maximum.

When enhanced, a MOSFET channel can conduct current in either direction. In a conventional discrete NMOS with body tied to source, the intrinsic diode conducts from source to drain; a PMOS diode conducts from drain to source. Integrated switches and unusual devices require their own internal diagram. The diode can conduct with the gate off, so one MOSFET often cannot block both directions. Opposed series MOSFETs can block both directions when off if their gate drive is suitable. When on, they do not automatically stop reverse current; an appropriate controller must detect and disable unwanted flow.

## Explain a high-side PMOS with a small transistor driver

A resistor from PMOS gate to source biases the power switch off when the driver releases the gate. An NMOS or NPN can pull that gate lower to enable power. A separate bias resistor at the driver input defines the state while the controller resets. A series gate resistor can shape transition speed and damp ringing.

The intended sequence is: controller asserts the driver; the driver discharges the power-switch gate; negative Vgs develops; the PMOS channel carries load current. On release, the gate-to-source resistor removes that bias. Check every source voltage that can occur, including an externally powered output. A pull-up tied to a fixed input rail may not hold Vgs at zero when the source moves.

Example: a PMOS source at 5 V and gate at 0.2 V has Vgs = -4.8 V. This is a voltage calculation, not proof that a particular MOSFET is fully on. At an assumed hot Rds(on) of 80 milliohm and continuous 0.8 A, conduction loss is 51.2 mW.

    Pconduction approximately Irms^2 * Rds(on)
    Ig_average approximately Qg * fswitch
    t_transition approximately Qrelevant / Igate

For 8 nC total gate charge at 100 kHz, average charging current is 0.8 mA. Charging 8 nC with a constant 20 mA would take 0.4 us, but this is only a rough estimate: gate charge is voltage-dependent, the Miller interval matters, and a resistor-driven gate does not receive constant current. The driver must support peak current and switching loss, not just average charge current.

Slower switching can reduce edge-related interference but increase dissipation during the overlap of voltage and current. Faster switching can increase ringing and coupling. A universal gate-resistor value is not a verified design.

## A BJT switch needs enough base drive

Identify collector, base, and emitter from the actual package. For a simple grounded-emitter NPN with a base resistor:

    Ib approximately (Vdrive - Vbe) / Rbase
    forced_beta = Ic / Ib
    Pconduction approximately Ic * Vce_sat

Active-region hFE is not a saturation guarantee. Use the datasheet's Vce(sat) test conditions or a justified forced-beta design. Include drive-voltage droop and any current diverted through a base-emitter resistor.

Example: for 20 mA collector current and a chosen forced beta of 10, Ib = 2 mA. Assuming Vdrive = 3.3 V and Vbe = 0.8 V gives Rbase = 1.25 kohm. That design choice is illustrative; confirm saturation, GPIO drive, storage time, and temperature for the selected transistor. A tiny base current can still control a very small collector load, so a large base resistor is not automatically a functional fault.

A base-emitter bias resistor can speed discharge and define an off state. Saturation stores charge and can slow turn-off. For a PNP high-side switch, reverse the relevant polarities and compare the base with its emitter. A transistor driver can invert the control logic; describe the final load state rather than merely saying the GPIO is high.

## Load protection and state analysis

An inductive load needs a controlled path for its current at switch-off. A flyback diode, TVS, or another clamp changes the voltage stress and current-decay time. Select the solution for both protection and the required release speed; an arbitrary small signal diode is not suitable for every coil.

Evaluate at least power-off, reset, normal-on, normal-off, and external-output-powered states. A low-side switch can disconnect the nominal ground while signal cables create an alternate return. A high-side switch can be bypassed through signal protection structures. Neither arrangement alone proves reverse-polarity, overcurrent, charging, or battery protection.

Confirm pin mapping, hot on-resistance or saturation behavior, leakage, safe operating area, and pulse/thermal limits. Switching a capacitor bank slowly can put a MOSFET into a demanding linear operating region even when its steady on-state dissipation is small.
