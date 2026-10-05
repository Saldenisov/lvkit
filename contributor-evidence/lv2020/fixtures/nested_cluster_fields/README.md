# Nested anonymous cluster field reads and updates

`nested_cluster_fields.vi` was independently authored in LabVIEW 2020 (64-bit).
Its anonymous cluster has the layout `(marker, (left, right))`. Two branches
consume that input: Unbundle by Name reads the original `inner.right`, and
Bundle by Name replaces `inner.right` with a separate DBL control. The updated
cluster and original scalar are exposed on the connector pane. No subVI,
typedef, class or application binding is present.

Native LabVIEW 20.0.1f1 execution captured eight explicit-input cases, covering
asymmetric values, negative values, zeros, an unchanged replacement, signed
zeros, nonfinite values and large/small finite magnitudes. Capture checks exact
input transfer, input preservation and a stable saved VI hash.

## Defect and fix

Both saved nMux list terminals have field index `3`. The depth-first field order
includes intermediate cluster fields: `marker`, `inner`, `inner.left`,
`inner.right`. Therefore index `3` identifies tuple path `(1, 1)`.

On unmodified v0.8.7 (`27ce18682e3f402e43368be9c0cd19ec669ffba4`), anonymous
unbundling treats that saved index as a top-level tuple subscript; bundling emits
an attribute assignment on the tuple. The native fixture fails first with
`AttributeError: 'tuple' object has no attribute 'right'`. Independent synthetic
read cases also expose wrong values and `IndexError`.

The patch maps saved indices to nested positional paths using resolved type
fields. Anonymous reads use those paths. Anonymous updates rebuild the changed
tuple branches, preserving the input cluster and untouched scalar values.
Named cluster attribute handling retains its current path. Missing/invalid
indices, unresolved update values and paths through named descendants fail
explicitly instead of guessing a positional representation.

| Check | v0.8.7 | Patched |
|---|---:|---:|
| New generator regression cases | 23 failed, 8 passed | 31 passed |
| New tuple-update helper cases | Helper absent | 16 passed |
| New cases + related codegen/type/AST builder tests | — | 194 passed, 7 skipped |
| Native output comparisons (8 cases, 2 outputs) | 0/16 | 16/16 |
| Offline native fixture pytest | 8 failed | 8 passed |

Generator tests independently cover every depth-first field in three cluster
shapes, parent-cluster replacement, multiple scalar updates, untouched inputs,
explicit metadata failures and preservation of named attribute handling.
Helper tests cover tuple updates, branch identity and invalid paths/types.

## Reproduction without LabVIEW

Install the tested LVKit checkout's development dependencies using Python 3.12.
`BUNDLE` is the directory containing the `fixtures` folder and helper scripts.

```powershell
$env:PYTHONPATH = "$CHECKOUT\src"
python "$BUNDLE\verify_nested_cluster_fixture.py" --fixture "$BUNDLE\fixtures\nested_cluster_fields" --output-dir "$RESULTS\nested-cluster"
python -m pytest "$BUNDLE\test_nested_cluster_native.py" -q -o addopts= --confcutdir="$BUNDLE"
```

The verifier supplies positional tuples, including nested clusters. It compares
exact tagged JSON, preserving nonfinite classification and signed zero.
`spec.json` describes the interface and cases; `golden_labview.json` stores actual
native outputs and VI/capture/helper hashes. The companion evidence includes
generated Python, conversion logs, comparison reports and untouched JUnit XML.

## Bounds

Native evidence covers one nested anonymous cluster with three DBL leaves and
one selected-field update. Deeper shapes and multiple updates are synthetic
tests. Saved cluster defaults, omitted inputs, anonymous interface annotations,
named descendant representation and overlapping parent/child updates are outside
this native qualification. The helper preserves unchanged branch identities;
it does not deep-copy mutable leaves such as arrays. This patch does not change
named aggregate mutation behavior or the existing annotation contract.
