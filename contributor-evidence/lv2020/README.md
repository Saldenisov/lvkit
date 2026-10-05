# LVKit 0.8.7: two fixes with minimal LabVIEW 2020 VIs

A newly authored LabVIEW 2020 VI exposes an executable conversion error in
LVKit 0.8.7: numeric Add becomes Python list concatenation when either operand
is a literal array. The proposed patch restores element-wise addition in the
typed numeric-template pass and preserves concatenation in the module pass.
An independent second fixture exposes a saved enum default being replaced by
zero. Its separate patch preserves the recorded ordinal based on the enum type.

## Release checked

- Repository: https://github.com/pragmatest-dev/lvkit
- Baseline: `v0.8.7`, commit `27ce18682e3f402e43368be9c0cd19ec669ffba4`.
- Comparison: `v0.8.6`, commit `d8058677e15c47094e725439bd72417fe9527754`.
- A separate, clean 0.8.7 checkout was downloaded. The existing converter used
  by the application was not upgraded by this work.
- Nested flat-sequence ownership inside a loop is already addressed by 0.8.7;
  the release includes `tests/test_loop_zplane.py`. This bundle proposes no
  additional patch for that issue.
- The numeric code generator and runtime have no changes between these tags;
  the array-literal Add defect remains reproducible in 0.8.7.
- Saved enum default `1` still becomes `0`. This is reproduced both from a
  synthetic terminal and from a second newly authored LabVIEW 2020 VI.

## Fixture 1: numeric Add

`fixtures/array_add_literal/array_add_literal.vi` was created in installed
LabVIEW 2020 SP1, 64-bit, version `20.0.1f1`, on 2026-10-05. Its diagram has
one Add primitive, one DBL array input `bank`, one literal `[0.0, -2.0, -2.0]`,
and one DBL array output `result`. Both terminals are on the connector pane.
The fixture has no subVI or hardware dependencies.

The fixture is a new isolated reproducer; no proprietary application VI is
included. The source VI and native results are supplied as a separate evidence
bundle. The source-code patch contains only the numeric fix and synthetic
regression tests, so the maintainer can decide how to admit binary fixtures
under the repository's clean-room and fixture-provenance policy.

For input `[1.0, 4.0, 5.0]`:

| Execution | Output |
| --- | --- |
| Native LabVIEW 2020 | `[1.0, 2.0, 3.0]` |
| Clean LVKit 0.8.7 | `[0.0, -2.0, -2.0, 1.0, 4.0, 5.0]` |
| LVKit 0.8.7 with proposed patch | `[1.0, 2.0, 3.0]` |

Generated expressions, produced automatically from the same `.vi`:

```python
# Clean 0.8.7
sum_ = [0.0, _lv.neg(2.0), _lv.neg(2.0)] + bank

# Proposed patch
sum_ = _lv.add([0.0, _lv.neg(2.0), _lv.neg(2.0)], bank)
```

`spec.json` defines terminal types, graph intent, comparison policy and ten
input cases. `golden_labview.json` records actual native outputs, the VI
SHA-256, application version and capture-script SHA-256. These expected
outputs were obtained by executing the VI, not by evaluating the LVKit runtime
or by copying generated Python results.

The native cases cover empty, shorter, equal-length and longer arrays,
negative numbers, fractional numbers, zeros, cancellation and large finite
values. Native agreement is established for these one-dimensional DBL cases.
NaN, infinity, signed-zero bits, other numeric representations and additional
LabVIEW versions are not established by this fixture. Synthetic tests also
exercise scalar broadcasting, both literal operand positions and 2-D arrays.

## Fixture 2: saved enum default

`fixtures/enum_saved_default/enum_saved_default.vi` was created in the same
LabVIEW 2020 instance. Its diagram is a direct wire from the connector-pane
enum control `mode` to enum indicator `result`; no arithmetic or subVI is needed.
Both have the U16 enum members `Idle=0` and `Run=1`. The input's saved default
is `Run=1`.

The parser correctly retains the input's type `UnitUInt16` and default `1`.
The parameter-default generator recognizes numeric `NumUInt*` tokens but
does not handle enum `UnitUInt*` tokens. The unmodified generated function
therefore has `mode: int=0`; the patched function has `mode: int=1`.

| Call | Native LabVIEW 2020 | Clean LVKit 0.8.7 | Proposed patch |
| --- | --- | --- | --- |
| Explicit `mode=0` | 0 | 0 | 0 |
| Omitted input after the explicit zero case | 1 | 0 | 1 |
| Explicit `mode=1` | 1 | 1 | 1 |
| Omitted input | 1 | 0 | 1 |

The native capture calls `ReinitializeAllToDefault` before each case, so an
omitted input uses the saved VI default rather than retaining the previous
front-panel value. The golden receipt records the effective native inputs.
The Python check calls the generated function with an empty argument mapping
for the omitted-input cases; it does not insert the expected default itself.

Native agreement is established for this anonymous U16 enum. Synthetic cases
exercise U8/U16/U32 enum tokens, absent underlying tokens, ordinal strings and
integers, zero, missing/invalid defaults, and an unchanged integer-primitive
control. Named typedef enums and ring controls are not established by this VI.

## Patch and mechanism

`patches/0001-numeric-add-array-literals.patch` changes
`src/lvkit/codegen/elementwise.py` and adds
`tests/test_numeric_array_literal.py`.

The existing list-concatenation guard is appropriate for the module-wide pass,
which sees Build Array and Replace Array Subset expressions. Applying that
guard to a typed numeric Add template loses arithmetic semantics. The patch
gives the numeric-template transformer its own concatenation policy. It uses
the existing broadcasting runtime; no VI names, labels, array lengths or
constant values are matched in the fix.

`patches/0002-preserve-enum-parameter-default.patch` independently changes
`src/lvkit/codegen/builder.py` and adds
`tests/test_enum_parameter_defaults.py`. An enum terminal with a recorded
default produces that integer ordinal. Missing or invalid values follow the
existing type-default fallback. The fix uses `LVTypeKind.ENUM`, not a list of
underlying-token spellings or enum labels. Each patch applies separately to
the verified v0.8.7 baseline, and both were tested together in a fresh checkout.

## CI-version verification before opening the pull requests

Additional verification used Python **3.12.14**, Windows and the repository's
locked development dependencies, matching the Python 3.12 version family in CI.
The two source patches were also checked independently against current `main`,
which still resolves to the v0.8.7 baseline above.

| Check | Result |
| --- | --- |
| New synthetic cases on clean 0.8.7 | Array: 13 failed, 2 passed; enum: 14 failed, 5 passed |
| Existing array-ops tests on clean 0.8.7 | 22 passed |
| Both patches, focused related selection including 14 native comparisons | 273 passed, 1 skipped |
| Full non-sample selection, clean 0.8.7 | 1902 passed, 7 failed, 202 skipped, 335 deselected |
| Full non-sample selection, array patch alone | 1917 passed, 7 failed, 202 skipped, 335 deselected |
| Full non-sample selection, enum patch alone | 1921 passed, 7 failed, 202 skipped, 335 deselected |
| Ruff on the combined checkout | Passed |
| Pyright on each independent patch checkout | 0 errors, 0 warnings |

All seven full-selection failures have the same test identities on clean 0.8.7
and both independent patches. They occur in `test_extraction_cache.py` (one),
`test_lv_detect.py` (one, LabVIEW is installed on this machine), and
`test_mcp_roots.py` (five, Windows/WSL path expectations). They are outside the
changed code. No full-suite passing claim is made. JUnit files and an exact
failure-identity comparison are in `evidence/python-3.12/summary.json` and the
adjacent XML receipts.

The original Python 3.11 receipts below are retained as historical evidence.
Their seven array-ops failures are a separate Python-version compatibility
issue documented in `.github/workflows/ci.yml`; all 22 of those tests pass on
Python 3.12. The single focused skip requires an unavailable external sample VI;
all 14 newly authored native comparisons execute.

## Original Python 3.11 validation receipts

| Check | Clean 0.8.7 | Proposed patch |
| --- | --- | --- |
| Fifteen new synthetic regression cases | 13 failed, 2 passed | 15 passed |
| Nineteen new enum parameter cases | 14 failed, 5 passed | 19 passed |
| Both real VIs -> graph -> Python -> native golden, fourteen cases | 12 failed, 2 passed | 14 passed |
| Numeric Add CLI conversion and execution, ten cases | 0/10 match | 10/10 match |
| Enum CLI conversion and execution, four cases | 2/4 match | 4/4 match |
| Both patches, focused related selection, 248 cases | — | 247 passed, 1 skipped |
| Initial array patch broader selection, 247 cases | See baseline note below | 239 passed, 7 failed, 1 skipped |
| Ruff check and format check on patch files | — | Passed |

The seven broader failures are pre-existing failures in
`tests/test_array_ops_codegen.py`; an independent run against clean 0.8.7
reproduced the identical seven failures (`7 failed, 15 passed`). They report
undefined `fill_value`, `cols` or `_flat`. The test helper executes fragments
with separate globals and locals, while comprehensions resolve these names
through globals. This Python 3.11 comprehension-scope issue is outside the numeric Add
patch and is not changed here. The repository's CI notes the same compatibility
limitation; see the Python 3.12 verification above. The broader suite must not be described as fully passing.

JUnit receipts are in `evidence/`:

- `upstream-0.8.7/pytest-regression.xml`: 23 failures, 2 passes across the new
  synthetic and real-VI tests.
- `upstream-0.8.7/pytest-array-ops.xml`: the seven existing harness failures.
- `patched-0.8.7/pytest-related.xml`: all 247 related outcomes.
- Each checkout's `report.json`: per-case native/Python values, unchanged-input
  checks, selected LVKit source path and generated-module SHA-256.
- Each checkout's `conversion.log` and `generated/`: conversion diagnostics
  and unedited generated Python.

Those paths refer to the `array_add_literal/` subdirectory. The
`enum_saved_default/` subdirectory contains its separate receipts:
`upstream-0.8.7/pytest-regression.xml` records 14 failures and five passes;
`patched-0.8.7/pytest-related.xml` records 123 passes and one skip, including
the enum real-VI tests and existing AST/context tests. Its CLI reports record
the four native comparisons.

`combined/pytest-baseline-native.xml` records all fourteen native comparisons
against unmodified 0.8.7. `combined/pytest-related.xml` records 247 passes and
one skip with both patches applied. This combined selection includes the new
34 synthetic cases, fourteen native comparisons, existing elementwise,
AST builder, codegen context, compound and loop tests. The known failing
`test_array_ops_codegen.py` helper is recorded separately rather than included
in this focused passing selection. No full-suite passing claim is made.
The single skipped AST-builder test requires an external sample VI that is not
available in these isolated checkouts (`Sample VI not available`). All fourteen
new real-VI comparisons execute; none are skipped.

The conversion reports contain two parser warnings:
`No parsing made for MCLVRTPatches` and
`Identifier has more than one special character`. Neither prevented this VI
from converting or executing; this patch does not fix those warnings.

## Reproduce without LabVIEW

In a disposable LVKit checkout at `v0.8.7`, install the project's dev
dependencies. Set `$bundle` to the extracted evidence directory.

```powershell
$bundle = 'C:\path\to\lvkit_upstream'
git apply --check "$bundle\patches\0001-numeric-add-array-literals.patch"
git apply --check "$bundle\patches\0002-preserve-enum-parameter-default.patch"
git apply "$bundle\patches\0001-numeric-add-array-literals.patch"
git apply "$bundle\patches\0002-preserve-enum-parameter-default.patch"
uv run pytest -q -o addopts= tests/test_numeric_array_literal.py tests/test_enum_parameter_defaults.py
uv run pytest -q -o addopts= --confcutdir="$bundle" "$bundle\test_native_fixture.py"
uv run python "$bundle\verify_fixture.py" --fixture "$bundle\fixtures\array_add_literal" --output-dir "$bundle\new-array-run"
uv run python "$bundle\verify_fixture.py" --fixture "$bundle\fixtures\enum_saved_default" --output-dir "$bundle\new-enum-run"
```

Run the native tests and verifier commands before applying the patches to reproduce the native
mismatches. `verify_fixture.py` returns exit code 1 on mismatch and 0 on full
agreement. Both the regression test and verifier check the VI's SHA-256 against
the native receipt. Generated package filenames vary with the fixture path;
the verifier discovers the emitted VI module rather than hard-coding that name.

## Refresh the native oracle

On Windows with LabVIEW 2020 and `pywin32` installed:

```powershell
python "$bundle\capture_labview.py" --fixture "$bundle\fixtures\array_add_literal"
python "$bundle\capture_labview.py" --fixture "$bundle\fixtures\enum_saved_default"
```

These commands explicitly rerun an authored fixture and rewrite its golden receipt.
The capture uses the documented ActiveX API and NI's documented
[`_FlagAsMethod` workaround](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA0VU0000008tNV0AY&l=en-US).
It verifies transferred inputs, checks input preservation and checks that the
VI's on-disk bytes remain unchanged. It does not save a VI or access the
application's large acquisition project.
The reset method is listed in NI's public
[VI Methods (ActiveX) reference](https://www.ni.com/docs/en-US/bundle/labview-api-ref/page/properties-and-methods/activex/vi-m.html).

## Additional independent fixture

[Scalar NaN and infinity constants](fixtures/nonfinite_constants/README.md):
new native LabVIEW 2020 VI, strict JSON specification, native receipts,
37 synthetic cases and an independent source patch.

[underscore_output](fixtures/underscore_output/README.md): independent native VI, specification,
baseline/patched conversions, executable tests and source patch.

[real64_divide](fixtures/real64_divide/README.md): independent native VI, specification,
baseline/patched conversions, executable tests and source patch.

[real64_log10_array](fixtures/real64_log10_array/README.md): independent native VI, specification,
baseline/patched conversions, executable tests and source patch.

[anonymous_cluster_identity](fixtures/anonymous_cluster_identity/README.md): independent native VI, specification,
baseline/patched conversions, executable tests and source patch.

[expanded_index_array](fixtures/expanded_index_array/README.md): independent native VI, specification,
baseline/patched conversions, executable tests and source patch.
