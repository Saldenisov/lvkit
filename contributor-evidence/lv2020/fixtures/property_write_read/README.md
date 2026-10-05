# Explicit Property Node write/read order

Two independent VIs were authored in LabVIEW 2020, 64-bit, for this regression.
The harness owns one U32 Numeric control named `target`, a strict reference to
that control, a U32 input `value`, a U32 indicator `result`, and the leaf call.
The leaf was created by selecting only the explicit Property Node and choosing
Edit > Create SubVI. It has an explicit strict Numeric reference input
`Digital in`, U32 `value`, and U32 `result` on its generated connector pane.
No application VI, sample, class, typedef or driver was copied. No extracted
icon or rendered NI artwork is published.

The single Property Node contains two ordered rows for the same property:

1. Write `Value` from the supplied U32.
2. Read `Value` into the result.

The harness provides a real control reference during native execution. Only
the leaf is translated and executed in Python. `NumericReference` is an explicit
test adapter with a `value` attribute, stored state and an event log. This fixture
qualifies ordered attribute access with an explicit object; it does not implement
VI Server, reference constants, implicit control bindings, or hardware APIs.

## Native observation

`golden_labview.json` records actual LabVIEW **20.0.1f1** execution for seven
U32 inputs, including 0, 1, both sides of the signed 32-bit boundary and U32 max.
Every case starts with target 123456789. The result and final target equal the
supplied value. Input transfer and preservation are checked, as are both saved
VI hashes. The capture helper's hash is part of the receipt.

Immediate COM reads sometimes returned the reset indicator value after
`Run(True)`, while the target already contained the new value. The qualified
capture therefore uses fixed 200 ms and 50 ms delays, independent of expected
values, and requires the last two observations to agree. Immediate and delayed
observations are retained for every case. This establishes stable observations
in this environment; it does not establish a universal COM timing bound.

The extracted graph independently records the first property value terminal
as input index 4 and the second as output index 5. Fixed reference/error ports
occupy indices 0–3. `stored_properties.json` records the exact saved identities,
ordered rows and hashes of structural XML exports.

## Baseline and patch

Baseline: v0.8.7 / main, `27ce18682e3f402e43368be9c0cd19ec669ffba4`.

The baseline emits:

```python
digital_in_value = digital_in.value
digital_in.value = value
return PropertyWriteReadResult(result=digital_in_value)
```

The patch emits the write before the read. It uses the existing
`correlate_property_terminals` graph API rather than selecting the next wired
input/output. It also gives repeated reads distinct snapshots and handles the
fixed reference output separately. Unsupported bindings, wired error channels,
unwired write defaults and incomplete identities raise `CodeGenError`.

| Check | Baseline | Patched |
|---|---:|---:|
| Native output values | 1/7 | 7/7 |
| Native final target state | 7/7 | 7/7 |
| Adapter write/read order | 0/7 | 7/7 |
| All three checks per case | 0/7 | 7/7 |
| Offline native pytest, including stored rows | 7 failed, 1 passed | 8 passed |
| New synthetic regression cases | 35 failed, 2 passed | 37 passed |
| Existing related selection | 74 passed, 3 skipped | Including new cases: 111 passed, 3 skipped |

The one baseline output match is the input equal to the initial value; its event
order remains wrong. Synthetic cases cover interleaved repeated reads/writes,
multiple property names, reversed terminal storage, wired reference output,
unwired read side effects, Refnum/error-cluster property values, and rejected
incomplete/unsupported nodes. Three related driver tests require absent sample
VIs. Ruff passes; Pyright reports 0 errors and 0 warnings. Original JUnit receipts
are retained. No full-suite or upstream CI success is claimed.

## Reproduce without LabVIEW

Use the source PR with its locked development environment. Set `EVIDENCE` to
this bundle's `contributor-evidence/lv2020` directory and `FIXTURE` to
`$EVIDENCE/fixtures/property_write_read`. Point `PYTHONPATH` at the chosen
checkout's `src` and use separate output/cache directories for each checkout.

```sh
python "$EVIDENCE/verify_property_fixture.py" --fixture "$FIXTURE" --output-dir /tmp/property-patched
python -m pytest -o addopts= "$EVIDENCE/test_property_native.py" --confcutdir "$EVIDENCE" -q
python -m pytest -o addopts= tests/test_property_terminal_order.py -q
```

The saved-output verification requires no LabVIEW. Reacquiring the oracle
requires the original two VIs, Windows, LabVIEW 2020 and pywin32:

```sh
python "$EVIDENCE/capture_property_labview.py" --fixture "$FIXTURE"
```

I32-to-U32 coercion, property exceptions/error propagation, implicit state,
hardware behavior and the harness's Python translation are outside this fix.
The source change is independent of the other LVKit contributions.
