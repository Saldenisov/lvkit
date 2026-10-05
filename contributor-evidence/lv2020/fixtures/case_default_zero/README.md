# Saved Case Structure default at diagram zero

`case_default_zero.vi` was newly authored in LabVIEW 2020, 64-bit. An I32
connector input named `selector` feeds one Case Structure. Its first frame,
`0, Default`, sends 10 through a shared output tunnel; frame `1` sends 20.
The I32 connector output is `result`. No application VI, subVI, typedef or
class was copied. A disconnected I32 constant in the first frame has no
effect on either output.

Native LabVIEW 20.0.1f1 execution records seven inputs: 0, 1, 2, -1, 99,
I32 minimum and I32 maximum. The capture checks exact input transfer and
preservation and verifies that execution leaves the saved VI hash unchanged.
The JSON specification describes the branch contract; `golden_labview.json`
contains actual native outputs and capture-script provenance.

## Defect and change

Baseline: v0.8.7 / main `27ce18682e3f402e43368be9c0cd19ec669ffba4`.
The extracted heap contains literal ranges `(0, 0, diagram 0)` and
`(1, 1, diagram 1)`. The zero-valued `SelectDefaultCase` field is omitted.
The stored displayed label independently reads `0, Default`; the parser fix
does not use that label. This VI has no dataspace selector tables.

Baseline marks the last frame as Default. Both explicit values still return
correct results, but every other tested selector returns 20 instead of 10.
The patch recognizes the omitted zero default index for integer/string/enum
selectors, preserves literal values/ranges on default frames, and keeps the
saved default flag when a correlated dataspace table supplies explicit ranges.
The post-processing rule that assigns the last frame is removed. Boolean and
symbolic error-cluster paths are retained and exercised by related tests.

| Check | Baseline | Patched |
|---|---:|---:|
| New synthetic regression cases | 22 failed, 8 passed | 30 passed |
| Generated output comparisons against native LabVIEW | 2/7 | 7/7 |
| Offline native fixture pytest, including frame metadata | 6 failed, 2 passed | 8 passed |
| Existing related selection | 64 passed, 22 skipped | Including new cases: 94 passed, 22 skipped |

Ruff passes; Pyright `src/` reports 0 errors and 0 warnings. The 22 skips in
`test_parser_regression.py` require an unavailable sample corpus. No full-suite
or upstream CI success is claimed. Original JUnit receipts are included.
Existing VICD patch and identifier warnings appear in both conversions; this
change does not address those warnings.

## Reproduction without LabVIEW

Install the tested checkout's development dependencies with Python 3.12.
`BUNDLE` denotes the directory containing `fixtures` and the helper scripts.
Use separate result directories and caches for baseline and patched checkouts.

```powershell
$env:PYTHONPATH = "$CHECKOUT\src"
$env:LVKIT_CACHE_DIR = "$RESULTS\cache"
python "$BUNDLE\verify_numeric_fixture.py" --fixture "$BUNDLE\fixtures\case_default_zero" --output-dir "$RESULTS\conversion"
python -m pytest "$BUNDLE\test_case_native.py" -q -o addopts= --confcutdir="$BUNDLE"
```

The verifier runs the ordinary `python -m lvkit generate` command, imports the
generated module, executes all seven inputs, and compares exact integer outputs
with the saved native receipt. `inspect_case_fixture.py` exports structural XML
and stored selector facts, without exporting extracted icons or rendered NI
artwork. Baseline/patched generated Python, logs and comparison reports accompany
the fixture. No other contribution is required to execute it.

## Bounds

Native evidence covers an I32 selector with two literal frames and Default at
diagram zero in LabVIEW 2020. Synthetic tests additionally cover explicit
default indices 0/1, string and enum selectors, fully covered `FF` no-default
frames, multiple closed ranges, correlated selector tables, and displayed-frame
independence. Existing tests cover symbolic error-cluster and Boolean cases.
Table correlation, incomplete/corrupt selector metadata, empty-string handling
and range-count validation are outside this patch. The renderer's displayed
default labels are not changed.
