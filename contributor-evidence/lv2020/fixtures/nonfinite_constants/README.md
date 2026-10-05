# Scalar NaN and infinity constants: LabVIEW 2020 evidence

`nonfinite_constants.vi` was newly authored in LabVIEW 2020 SP1 64-bit
(`20.0.1f1`). Three independent DBL constants, NaN, positive infinity and
negative infinity, connect directly to three indicators and connector-pane
outputs. No application source, subVI, hardware or arithmetic primitive is used.

`spec.json` defines the interface and expected classification. Actual native
execution outputs are in `golden_labview.json`, with the VI SHA-256, native
version, capture time and hashes of the capture and numeric-encoding scripts.
The VI SHA-256 is
`5ca55a6e8cec6ba49b76ad4ea51c8343fcee61d61b2acfd255b62918f841e18e`.

Non-finite values use strict JSON tags (`{"float": "nan"}`, `{"float": "inf"}`
and `{"float": "-inf"}`). Matching compares numeric classification and infinity
sign. NaN payload/sign and floating-point status flags are outside this check.

## Results

Baseline: upstream v0.8.7/current main,
`27ce18682e3f402e43368be9c0cd19ec669ffba4`. Python 3.12.14, Windows,
locked LVKit development dependencies.

| Check | Clean baseline | Scalar-constant patch |
| --- | --- | --- |
| New synthetic cases | 24 failed, 13 passed | 37 passed |
| Native VI outputs | 0/3; function raises `NameError: name 'nan' is not defined` | 3/3 match |
| New and existing context/AST cases | See baseline receipt for new cases | 137 passed, 1 skipped |
| Native pytest comparisons | 3 failed | 3 passed |
| Ruff on source checkout | Not repeated | Passed |
| Pyright on source checkout | Not repeated | 0 errors, 0 warnings |

The native fixture is one function call with three outputs. Baseline execution
stops at its first undefined `nan`; the three failed comparisons are not three
independent native executions. Synthetic cases separately exercise each value,
decimal/IEEE-hex encodings, decoded Python floats and DBL/SGL type metadata.
Finite values, signed zero and string constants are controls.

JUnit receipts, conversion logs, generated Python and comparison reports are in
`../../evidence/nonfinite_constants/`. The standalone source patch is
`../../patches/nonfinite-constants.patch`. Native SGL execution, aggregate
constants and other LabVIEW versions are not established by this fixture.

## Reproduction without LabVIEW

From the `contributor-evidence/lv2020` directory, with LVKit installed and the
desired source checkout selected in the environment:

```sh
python verify_numeric_fixture.py --fixture fixtures/nonfinite_constants --output-dir /tmp/nonfinite-check
python -m pytest -q test_nonfinite_native.py
```

Both commands consume the saved native receipt; they do not launch LabVIEW.
To repeat native capture, on a Windows machine with LabVIEW 2020 and pywin32:

```sh
python capture_numeric_labview.py --fixture fixtures/nonfinite_constants
```

The capture resets controls, runs the VI synchronously, reads all three outputs
and verifies that the VI's saved bytes have not changed. This evidence bundle
is separate from the upstream source-only pull request.
