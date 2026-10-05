# LLB lazy-member stream lifetime

`lazy_members.llb` was created in LabVIEW 2020, 64-bit, and contains two newly
authored fixture VIs: `first.vi` and `second.vi`. Each wires a DBL control named
`value` directly to a DBL indicator named `result`, with both on the connector
pane. No primitive, subVI, typedef, class or application binding is present.
The second VI copies the first fixture's small self-authored diagram.

Native LabVIEW 20.0.1f1 execution captured eight explicit inputs for each
member: positive/negative finite values, positive/negative zero, positive/
negative infinity, NaN and a large finite magnitude. Input transfer and
preservation are checked, and execution leaves the saved archive hash unchanged.

## Defect and fix

Baseline: v0.8.7 / main `27ce18682e3f402e43368be9c0cd19ec669ffba4`.
`_open_llb_vi()` returns a pylabview resource after closing its filesystem
stream. Deferred member sections subsequently raise
`ValueError: seek of closed file`. The existing extraction loop suppresses
those errors and writes an extraction sentinel even for a partial result.

In this native two-member LLB, baseline extraction returns only `first.vi`.
The whole-archive generation command exits zero and emits one Python module,
silently omitting `second.vi`. The patch retains a named in-memory archive
snapshot on the resource. Both members are then extracted and converted.

`archive_inventory.json` records the exact member byte hashes using a separate
reader that keeps the original filesystem stream open throughout `getData()`.
It calls neither `_open_llb_vi()` nor `extract_llb()`, so expected hashes do not
depend on the changed lifetime behavior. `golden_labview.json` records actual
native outputs, archive/member hashes and capture/inventory provenance.
The compatibility field `vi_sha256` denotes the LLB archive hash in this fixture.

| Check | Baseline | Patched |
|---|---:|---:|
| New synthetic regression cases | 12 failed, 4 passed | 16 passed |
| Extracted native member byte hashes | 1/2 | 2/2 |
| Whole-archive CLI modules | 1 | 2 |
| Native output comparisons (2 members × 8 inputs) | 8/16; second member absent | 16/16 |
| Offline native fixture pytest | 9 failed, 8 passed | 17 passed |
| New cases + existing cache/concurrency/long-path cases | — | 1 failed, 47 passed, 4 skipped |

The existing failure is
`TestGlobalHomeGuard::test_project_root_skips_global_home_lvkit` in
`tests/test_extraction_cache.py:518`. It also fails on the untouched baseline
(1 failed, 31 passed, 4 skipped for the existing selection). Both checkouts
return the actual user-home path instead of the synthetic repository root;
the patch does not touch that classifier. Ruff passes; Pyright `src/` reports
0 errors and 0 warnings. No full-suite or upstream CI success is claimed.

Synthetic tests construct actual pylabview resource archives with UCRF, CPRF
and ZCRF blocks and arbitrary byte payloads. They read every member after open
returns, interleave two independent resources, check complete fresh extraction
and preserve the invalid-archive error contract. They require no LabVIEW.

Both native runs emit existing pylabview warnings for complex CONP/CPC2 metadata.
The independent member byte hashes and executable native comparisons establish
the qualified behavior despite those warnings; this patch does not address them.

## Reproduction without LabVIEW

Install the tested LVKit checkout's development dependencies with Python 3.12.
`BUNDLE` is the directory containing the `fixtures` folder and helper scripts.
Use a new result directory for each checkout; the verifier requires a cold cache.

```powershell
$env:PYTHONPATH = "$CHECKOUT\src"
python "$BUNDLE\verify_llb_fixture.py" --fixture "$BUNDLE\fixtures\llb_stream_lifetime" --output-dir "$RESULTS\llb"
python -m pytest "$BUNDLE\test_llb_native.py" -q -o addopts= --confcutdir="$BUNDLE"
```

The verifier calls the ordinary `python -m lvkit generate` command on the LLB.
It checks exact extracted bytes, locates each generated function by its AST
definition, executes all explicit cases and compares tagged JSON values,
including nonfinite classification and zero sign. Conversion logs, generated
modules, comparison reports and original JUnit receipts accompany the fixture.

## Bounds

Native evidence covers this two-member UCRF archive; compressed block formats
are synthetic tests. Memory usage increases by one archive snapshot for the
lifetime of the returned resource, without retaining an open filesystem handle.
Large-archive memory profiling, previously populated partial caches, cache
invalidation, corrupt-member reporting, LVzp changes and connector metadata
parsing are outside this source change. Existing partial caches must be
invalidated separately before re-extraction. Neither member requires another
code-generation PR.
