# Maintainer follow-up validation — 2026-10-09

All ten requested follow-ups pass the focused selections at their exact PR
heads: **663 source tests, 91 saved-fixture checks and 19 supplemental checks
passed; 66 source tests skipped; no failures**. Ruff passes and Pyright reports
0 errors and 0 warnings on every checkout. These are independently tested PR
heads, not a full-suite or combined-merge result.

| PR | Tested head | Source passed | Source skipped | Fixture checks passed | Supplemental passed |
| --- | --- | ---: | ---: | ---: | ---: |
| #119 | `39eadc9` | 21 | 0 | 4 | 0 |
| #120 | `831d57d` | 59 | 0 | 3 | 0 |
| #121 | `0211785` | 25 | 0 | 1 | 1 |
| #122 | `0335a19` | 71 | 0 | 24 | 6 |
| #123 | `9684746` | 29 | 0 | 13 | 6 |
| #124 | `896e7dc` | 104 | 1 | 9 | 0 |
| #125 | `a9cc441` | 33 | 0 | 13 | 3 |
| #126 | `daae506` | 47 | 0 | 8 | 0 |
| #128 | `805f928` | 220 | 65 | 8 | 0 |
| #129 | `e1ce777` | 54 | 0 | 8 | 3 |

Python 3.12.14 and the project's locked development dependencies were used on
Windows x64. Each checkout was clean and pinned to the recorded head. The
pytest runner blocked outbound network access. `summary.json` records source
selections and exact skip reasons; each `prNN/` contains logs, JUnit receipts,
commands and the tested SHA. The 66 skips require external sample VIs/corpora
that are absent from these checkouts; all saved-fixture checks ran.

## What the native evidence establishes

Generated Python was compared with the previously captured LabVIEW 2020
outputs in the frozen evidence bundle at
`d91b647bd26379e30b8dc9f850cbbbdb0daff3c6`. VI hashes were checked before
conversion. **LabVIEW was not rerun for this validation.** Fixture-check counts
also include graph metadata and annotation checks; they are not counts of new
native measurements. Existing captures and capture scripts were left unchanged.

The original enum VI covers enum saved defaults, not ring controls. Nonfinite
native evidence covers scalar constants, not array/cluster constants. Native
Divide and Log10 captures are DBL, not SGL/EXT precision measurements. The
SubVI caller check is synthetic and reads the actual converted native callee
result. Property Node tests use an explicit reference adapter, not hardware or
a native wired-error fixture. Additional representations and aggregate cases
are checked through source/supplemental tests.

## Supplemental checks

- #121: the generated caller field binding successfully reads the actual
  native callee's `output_status` value, agreeing with its saved output.
- #122: six executable typed-graph tests exercise mixed input representations,
  floating output coercion, scalar/array paths, signed infinity and NaN at zero.
- #123: six generated-module tests cover SGL, EXT and I32 inputs in 1D/2D arrays,
  including zero/negative inputs and unchanged input arrays.
- #125: three terminal-storage permutations (reverse, rotate, deterministic
  shuffle) each replay all 13 existing native cases: 39 successful case replays.
  Connector identities and indices are preserved.
- #129: three wired-error configurations each execute in both normal/reversed
  terminal storage order, verify property write/read order and confirm Python
  exceptions propagate from a failing reference adapter.

Supplemental sources are in the corresponding `prNN/test_followup.py` files.
They add no production-source changes and require no new LabVIEW execution.

## Reproduce

Use a disposable LVKit checkout at the full `head` from `summary.json` and
Python 3.12. Set `$bundle` to the extracted `contributor-evidence/lv2020`
directory. Commands for #125 are shown below; the other exact selections are
recorded in their reports. Running the published tests requires no LabVIEW.

```powershell
$bundle = 'C:\path\to\contributor-evidence\lv2020'
$env:LVKIT_EVIDENCE_ROOT = $bundle
$env:PYTHONPATH = "$PWD;$bundle"
uv run pytest -q -o addopts= tests/test_expanded_index_array.py
uv run pytest -q -o addopts= --confcutdir="$bundle" "$bundle\test_index_native.py"
$checks = "$bundle\evidence\maintainer-followups-2026-10-09\pr125"
uv run pytest -q -o addopts= --confcutdir="$checks" "$checks\test_followup.py"
uv run ruff check .
uv run pyright src
```

The machine-local absolute command paths in the receipts describe the actual
run. They need to be replaced with the reader's checkout, bundle and output
paths when replaying them. Per-file SHA-256 values are included in the bundle's
`manifest.json`.
