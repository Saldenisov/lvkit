# Anonymous cluster interface annotations

`anonymous_cluster_identity.vi` was independently authored in LabVIEW 2020
(64-bit). One anonymous cluster control (`cluster_in`) is wired directly to
an anonymous cluster indicator (`cluster_out`). Each cluster contains two DBL
fields, `first` and `second`. Both clusters appear on the connector pane.
The final diagram contains no primitive, subVI, typedef or application binding.

Native LabVIEW 20.0.1f1 execution captured seven explicit-input cases covering
zeros, asymmetric positive/negative values, mixed signs, negative zero and
large/small finite magnitudes. The capture checks input transfer, checks inputs
after execution and confirms the VI remains byte-identical on disk.

## Defect and discriminating checks

On v0.8.7 (`27ce18682e3f402e43368be9c0cd19ec669ffba4`), all seven output values
already match native LabVIEW when the cluster input is supplied as a tuple.
However, the generated parameter and NamedTuple result field advertise
`dict[str, Any]`. The annotations therefore disagree with the positional tuple
representation accepted and returned by the generated code.

The patch emits `tuple | None` for top-level anonymous cluster parameters and
`tuple` for result fields. `None` accurately reflects the existing conservative
parameter default. Runtime values, default construction and the shared type
model remain unchanged.

| Check | v0.8.7 | Patched |
|---|---:|---:|
| Native explicit-input output comparisons | 7/7 | 7/7 |
| Native fixture annotation checks | 0/2 | 2/2 |
| New synthetic regression cases | 6 failed, 12 passed | 18 passed |
| New cases + AST builder/front-panel array tests | — | 116 passed, 1 skipped |
| Offline native fixture pytest | 2 failed, 7 passed | 9 passed |

The synthetic cases cover unknown/empty/one-field/two-field/mixed/nested
anonymous clusters and preserve primitive, typedef, class, array and missing
type annotation contracts. They also verify the shared `LVType.to_python`
contract is unaffected.

## Reproduction without LabVIEW

Install the tested LVKit checkout's development dependencies using Python 3.12.
`BUNDLE` is the directory containing the `fixtures` folder and helper scripts.

```powershell
$env:PYTHONPATH = "$CHECKOUT\src"
python "$BUNDLE\verify_cluster_types_fixture.py" --fixture "$BUNDLE\fixtures\anonymous_cluster_identity" --output-dir "$RESULTS\cluster-types"
python -m pytest "$BUNDLE\test_cluster_types_native.py" -q -o addopts= --confcutdir="$BUNDLE"
```

The verification report separates value comparisons from annotation checks.
`spec.json` describes the declared VI/Python interface and all inputs;
`golden_labview.json` stores actual native outputs, capture time, LabVIEW version
and the VI/capture/helper hashes. Negative zero uses strict JSON tagging.
The companion evidence includes generated Python, untouched conversion logs
and original JUnit receipts for both checkouts.

## Bounds

Every native comparison supplies an explicit tuple input. Saved cluster
defaults, omitted-input execution and nested Bundle/Unbundle behavior are
outside this patch. Native evidence covers a top-level two-DBL anonymous
cluster in LabVIEW 2020. Named typedef/class and array annotation contracts
retain their current behavior.
