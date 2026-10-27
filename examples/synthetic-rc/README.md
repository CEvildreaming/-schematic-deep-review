# Synthetic RC walkthrough

This fully original teaching example has a 10 kohm series resistor and a 1 uF shunt capacitor. It demonstrates readable component explanations, interaction, equations, failure effects, and uncertainty without publishing a real board or third-party manual.

From the repository root, after installing the Python dependencies:

```sh
python examples/synthetic-rc/run.py
```

The script creates `output/synthetic-rc-original.pdf`, `output/synthetic-rc-annotated.pdf`, a preview, and `output/verification.json`. It checks one-page output, unchanged source bytes and visible source ink, text extraction, and layout constraints. Output is generated locally and excluded from Git.

For the stated ideal assumptions, the RC time constant is 10 ms, the 70% threshold crossing is 12.04 ms, and the small-signal cutoff is 15.92 Hz. An actual digital input requires its own threshold, leakage, and slow-edge specifications. This example does not test netlist recognition or hardware behavior.
