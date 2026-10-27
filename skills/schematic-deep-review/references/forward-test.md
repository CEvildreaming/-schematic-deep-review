# Public validation procedure and boundaries

This public package deliberately excludes private project logs and original user schematics. Re-run the tests below against the version you use; an older local result or a workflow badge is not proof that your project's output is correct.

## Deterministic tests

From the repository root, install the documented dependencies and run:

```bash
python -m unittest discover -s skills/schematic-deep-review/tests -v
python examples/synthetic-rc/run.py
```

The unit suite exercises PDF/document validation, calculations, inventory and layout behavior, source-ink preservation, and portability. Additional installation and knowledge-search tests are provided by their test modules. See the test files and CI workflow for the exact executed scope.

The synthetic example creates an original teaching RC drawing, applies a complete-page explanation, and writes numerical/layout checks. It is deliberately simple and is **not a real board review, an OCR benchmark, or a datasheet-download demonstration**. Its known values make calculation and layout changes reproducible.

## Independent forward exercise

For a meaningful new capability, give another analyst the skill and a fresh source without the intended answer. Use an isolated output directory. Useful scenarios include a scan, multi-page input, repeated reference names across files, an optional component, a missing part number, a conflicting BOM, an unreadable junction, and a dense annotation area.

Inspect the resulting files, not only the analyst's status message. Record the tested revision, inputs, actual outputs, failures, repairs, and final checks. Never include private source paths or documents in a public validation record.

## What this does not prove

A unit test cannot prove that an inventory is complete, that a PDF-only connection was read correctly, that a datasheet applies to a package revision, or that the explanation makes sense to a reader. Source-ink preservation does not establish native netlist equivalence. A synthetic RC example does not validate arbitrary circuits.

No hardware qualification is included. Actual stability, thermal behavior, signal integrity, antenna matching, transient response, and compliance require the appropriate design data and measurements. The project acceptance checklist is in [acceptance.md](acceptance.md).
