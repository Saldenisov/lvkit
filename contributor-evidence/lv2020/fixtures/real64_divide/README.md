# DBL division at signed zero: LabVIEW 2020 evidence

`real64_divide.vi` was newly authored in LabVIEW 2020 SP1 64-bit (`20.0.1f1`).
Two DBL controls, `numerator` and `denominator`, feed one native Divide
primitive; one DBL `quotient` indicator is connected to the output. All three
terminals are on the connector pane. No subVIs or hardware are required.

VI SHA-256:
`e771ed6df3f9932513f423e1c55d7f1b616334be6f3e683651fcf6e0da38ad89`.
`spec.json` defines 24 scalar input cases. `golden_labview.json` contains their
actual native outputs, effective transferred inputs, version, capture time and
capture-script hashes. Native execution reset each case, transferred inputs
as COM doubles, read them back, ran synchronously and checked input/disk bytes
were unchanged.

Baseline: v0.8.7/current main,
`27ce18682e3f402e43368be9c0cd19ec669ffba4`. Python 3.12.14 on Windows,
repository's locked development dependencies.

| Check | Clean baseline | Independent patch |
| --- | --- | --- |
| 37 generated-code cases | 19 failed, 18 passed | 37 passed |
| 24 native output comparisons | 10 matched, 14 `ZeroDivisionError` | 24/24 match |
| Related codegen/primitive/elementwise selection | New-case receipt above | 166 passed, 1 skipped |
| Native pytest comparisons | 14 failed, 10 passed | 24 passed |
| Ruff on source checkout | Not repeated | Passed |
| Pyright on source checkout | Not repeated | 0 errors, 0 warnings |

The cases include all numerator/denominator zero signs, signed nonzero and
infinite numerators over zero, NaN propagation, finite controls, signed-zero
outputs, infinity/infinity and overflow. Strict JSON tags preserve numeric
classification and negative-zero/infinity signs; NaN payload/sign and
floating-point status flags are not compared.

The catalog's neutral `DIVIDE` operation selects a Python template from
terminal type metadata. When all terminal element types are DBL, generated
code calls the DBL runtime helper. That helper returns IEEE results at zero
and delegates other scalar division to Python; array broadcasting follows the
existing runtime list convention. Other or missing representations keep the
existing template. Array broadcasting and representation guards are covered
synthetically; native evidence here establishes scalar DBL behavior only.

The one skipped related test requires an unavailable external sample VI.
The upstream source patch is `../../patches/real64-divide.patch`. Generated
Python, logs, comparison reports and JUnit receipts are in
`../../evidence/real64_divide/`.

From `contributor-evidence/lv2020`, with the desired LVKit checkout selected:

```sh
python verify_numeric_fixture.py --fixture fixtures/real64_divide --output-dir /tmp/divide-check
python -m pytest -q test_divide_native.py
```

These commands consume saved native receipts and do not launch LabVIEW.
Optional recapture on Windows with LabVIEW 2020 and pywin32:

```sh
python capture_divide_labview.py --fixture fixtures/real64_divide
```

The binary fixture is published independently of the source-only upstream PR.
