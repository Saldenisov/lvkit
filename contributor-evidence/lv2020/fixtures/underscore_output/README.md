# Leading underscore in an output label: LabVIEW 2020 evidence

`underscore_output.vi` was newly authored in LabVIEW 2020 SP1 64-bit
(`20.0.1f1`). One DBL constant, 42, connects directly to an indicator labelled
`_status` and one connector-pane output. There are no inputs, subVIs, hardware
dependencies or arithmetic primitives.

The VI's SHA-256 is
`1b5e43caec48f9a9bcb5dd8d01557150d0bb0506a9ce38603617fbc0704127be`.
`spec.json` defines the native label, Python result-field mapping and exact
comparison. `golden_labview.json` records the actual native output, execution
version, capture time and capture-script hashes.

Baseline: upstream v0.8.7/current main,
`27ce18682e3f402e43368be9c0cd19ec669ffba4`; Python 3.12.14 on Windows,
using the repository's locked development dependencies.

| Check | Clean baseline | Independent patch |
| --- | --- | --- |
| New synthetic cases | 13 failed, 8 passed | 21 passed |
| Native VI comparison | Module import raises `ValueError` for `_status` | `output_status == 42.0`, 1/1 match |
| New and existing context/AST cases | New-case receipt above | 121 passed, 1 skipped |
| Native pytest comparison | 1 failed | 1 passed |
| Ruff on source checkout | Not repeated | Passed |
| Pyright on source checkout | Not repeated | 0 errors, 0 warnings |

The patch applies a shared field-name rule to the result class and return
keywords. Labels whose normalized Python name begins with `_` receive an
`output` prefix. Other names retain existing normalization. Collisions are
rejected during generation rather than emitting an ambiguous result class.
Error-cluster outputs are excluded before collision checking.

Synthetic tests execute the generated modules, verify returned values and
cover eight underscore cases, seven existing naming behaviors, five collision
cases and one error-cluster exclusion. The native fixture establishes one
label and one exact numeric value; it does not establish all LabVIEW naming
or Unicode behavior. The focused skip requires an unavailable external VI.

The standalone patch is `../../patches/result-field-names.patch`. Conversion
logs, generated Python, comparison reports and JUnit files are in
`../../evidence/underscore_output/`.

From `contributor-evidence/lv2020`, with the desired LVKit checkout selected:

```sh
python verify_result_field_fixture.py --fixture fixtures/underscore_output --output-dir /tmp/result-field-check
python -m pytest -q test_result_field_native.py
```

These commands use the saved native receipt and do not launch LabVIEW.
Optional native recapture on Windows with LabVIEW 2020 and pywin32:

```sh
python capture_underscore_labview.py --fixture fixtures/underscore_output
```

The binary fixture and capture tooling are kept in this companion evidence
bundle, separately from the upstream source-only PR.
