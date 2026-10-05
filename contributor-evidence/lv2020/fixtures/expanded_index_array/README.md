# Expanded one-dimensional Index Array

`expanded_index_array.vi` was independently authored in LabVIEW 2020 (64-bit).
A one-dimensional DBL array control (`values`) and I32 index control (`start`)
feed an Index Array node expanded to three rows. The first index is wired;
the next two indices are unwired. All three DBL outputs (`first`, `second`,
`third`) appear on the connector pane. No subVI or application binding is used.

Native LabVIEW 20.0.1f1 execution captured 13 cases, covering saved empty
defaults, explicit empty and singleton arrays, offsets, negative indices,
indices beyond the array, nonfinite elements and signed zero. Each case has
three outputs. Capture checks input transfer and input preservation and confirms
the saved VI remains byte-identical on disk.

## Defect and fix

On unmodified v0.8.7 (`27ce18682e3f402e43368be9c0cd19ec669ffba4`), the generated
function attempts to unpack one indexed scalar into three output variables.
Every native case raises `TypeError: cannot unpack non-iterable float object`.

The patch emits each saved output/index pair separately for source-declared
one-dimensional arrays. An unwired first index starts at zero; later unwired
indices advance from the preceding row. Wired indices restart that progression.
Unwired outputs do not remove their index rows. The array expression is evaluated
once; the existing runtime helper supplies the existing element-type defaults
for out-of-range indices. Other ranks retain their template path.

| Check | v0.8.7 | Patched |
|---|---:|---:|
| Native output comparisons (13 cases, 3 outputs) | 0/39 | 39/39 |
| New synthetic regression cases | 30 failed, 3 passed | 33 passed |
| New cases + array ops/primitive resolutions/AST builder tests | — | 170 passed, 1 skipped |
| Offline native fixture pytest | 13 failed | 13 passed |

The synthetic cases additionally cover independent wired indices, unwired
outputs, empty/unwired arrays, scalar element defaults (I32, U8, Boolean,
String), single evaluation of an array expression, rank-boundary preservation
and explicit failures for invalid rows or unresolved wired inputs.

## Reproduction without LabVIEW

Install the tested LVKit checkout's development dependencies using Python 3.12.
`BUNDLE` is the directory containing the `fixtures` folder and helper scripts.

```powershell
$env:PYTHONPATH = "$CHECKOUT\src"
python "$BUNDLE\verify_numeric_fixture.py" --fixture "$BUNDLE\fixtures\expanded_index_array" --output-dir "$RESULTS\index-array"
python -m pytest "$BUNDLE\test_index_native.py" -q -o addopts= --confcutdir="$BUNDLE"
```

`spec.json` describes the interface, saved defaults and inputs;
`golden_labview.json` contains actual native outputs and capture provenance.
Comparisons use exact tagged JSON, preserving NaN/infinity classification and
the sign of zero. The companion evidence contains the binary VI, generated
Python, conversion logs, comparison reports and untouched JUnit receipts.

## Bounds

Native evidence covers one DBL array, three wired outputs, a wired first I32
index and two unwired subsequent indices in LabVIEW 2020. The additional wiring
and scalar-type variants are synthetic tests. This patch does not qualify
expanded multidimensional indexing, integer overflow of implicit indices or
default construction for complex element types. No runtime helper is changed.
