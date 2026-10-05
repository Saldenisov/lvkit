# DBL array Logarithm Base 10

`real64_log10_array.vi` was authored independently in LabVIEW 2020 (64-bit).
One 1D DBL array control (`values`) feeds Logarithm Base 10; its output feeds
the 1D DBL array indicator `log_values`. Both arrays are connected to the VI's
connector pane. The fixture has no subVIs or application dependencies.

The parsed primitive is 1210, with output index 0 and input index 1. Native
execution in LabVIEW 20.0.1f1 captured 13 cases: empty/singleton arrays,
powers and nonpowers of ten, signed zeros, negative values, NaN, both
infinities, mixed classifications, finite extremes and the smallest positive
DBL subnormal. The capture script verifies every transferred input, checks
inputs after execution and verifies the VI's disk SHA-256 stays unchanged.

## Before and after

Unmodified v0.8.7 (`27ce18682e3f402e43368be9c0cd19ec669ffba4`) cannot generate
this VI: primitive 1210 has no executable template and raises
`PrimitiveResolutionNeeded`. The existing runtime `lv.log10` also raises
`TypeError` for a list. The patch adds the neutral `LOG10` operation, a typed
DBL handler and recursive list support in the runtime helper.

| Check | v0.8.7 | Patched |
|---|---:|---:|
| Native VI output comparisons | 0/13; conversion failed | 13/13 |
| New synthetic regression cases | 32 failed | 32 passed |
| New cases plus related existing tests | — | 92 passed |
| Saved native receipt pytest cases | 13 failed | 13 passed |

The 32 synthetic cases comprise 13 generated scalar cases, six generated
array cases, ten representation/missing-type rejection controls and three
runtime array cases. Existing Formula Node runtime tests also pass.

## Reproduction without LabVIEW

Clone LVKit, install its development dependencies with Python 3.12, then set
`PYTHONPATH` to that checkout's `src`. `BUNDLE` below is the directory containing
this README's parent `fixtures` directory and the verification helpers.

```powershell
$env:PYTHONPATH = "$CHECKOUT\src"
python "$BUNDLE\verify_log10_fixture.py" --fixture "$BUNDLE\fixtures\real64_log10_array" --output-dir "$RESULTS\log10"
python -m pytest "$BUNDLE\test_log10_native.py" -q -o addopts= --confcutdir="$BUNDLE"
```

`spec.json` defines inputs, output, cases and comparison tolerances.
`golden_labview.json` contains actual native output values, LabVIEW version,
capture time, VI SHA-256 and capture/helper script hashes. Tagged values
represent NaN, infinities and negative zero in strict JSON.
`evidence/real64_log10_array` contains the original conversion logs,
baseline/patched reports, emitted Python and untouched JUnit receipts.

## Bounds

Finite nonzero values use relative and absolute tolerances of `1e-14`;
nonfinite classification, infinity sign, zero sign and array lengths are
checked explicitly. No claim is made about NaN payload/sign or FP status
flags. Native evidence covers 1D DBL arrays in LabVIEW 2020. Scalar and
multidimensional list paths have synthetic tests. SGL, extended real,
integer, complex and missing terminal types are rejected during generation
rather than assigned unverified DBL semantics.
