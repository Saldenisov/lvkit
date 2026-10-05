"""Convert an authored log10 VI and compare with saved native outputs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import lvkit
from compare_numeric_values import matches
from numeric_values import decode, encode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    fixture, output = args.fixture.resolve(), args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    golden = json.loads((fixture / "golden_labview.json").read_text(encoding="utf-8"))
    assert spec["id"] == "real64_log10_array"
    vi = fixture / spec["vi_file"]
    digest = hashlib.sha256(vi.read_bytes()).hexdigest()
    assert digest == golden["vi_sha256"], "VI does not match native receipt"
    command = [
        sys.executable,
        "-m",
        "lvkit",
        "generate",
        str(vi),
        "-o",
        str(output / "generated"),
        "--load-mode",
        "minimal",
        "--no-auto-vilib",
    ]
    conversion = subprocess.run(command, capture_output=True, text=True)
    (output / "conversion.log").write_text(
        conversion.stdout + conversion.stderr, encoding="utf-8"
    )
    modules = [
        path
        for path in (output / "generated").rglob("*.py")
        if path.name != "__init__.py"
    ]
    function, setup_error = None, None
    if conversion.returncode:
        setup_error = (
            f"Conversion failed (exit {conversion.returncode}); see conversion.log"
        )
    elif len(modules) != 1:
        setup_error = f"Expected one generated VI module, found {len(modules)}"
    else:
        try:
            module_spec = importlib.util.spec_from_file_location(
                "numeric_fixture", modules[0]
            )
            assert module_spec is not None and module_spec.loader is not None
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            function = getattr(module, spec["function"])
        except Exception as failure:
            setup_error = f"{type(failure).__name__}: {failure}"
    expected = {case["id"]: case["outputs"] for case in golden["cases"]}
    comparisons = []
    for case in spec["cases"]:
        inputs = {name: decode(value) for name, value in case["inputs"].items()}
        actual, error, unchanged = {}, setup_error, None
        if function is not None:
            try:
                actual = {
                    name: encode(value)
                    for name, value in function(**inputs)._asdict().items()
                }
            except Exception as failure:
                error = f"{type(failure).__name__}: {failure}"
            unchanged = {name: encode(value) for name, value in inputs.items()} == case[
                "inputs"
            ]
        for name, policy in spec["outputs"].items():
            target = expected[case["id"]][name]
            passed = (
                error is None
                and unchanged
                and matches(
                    actual.get(name),
                    target,
                    rel_tol=policy["relative_tolerance"],
                    abs_tol=policy["absolute_tolerance"],
                )
            )
            comparisons.append(
                {
                    "case": case["id"],
                    "output": name,
                    "expected": target,
                    "actual": actual.get(name),
                    "error": error,
                    "input_unchanged": unchanged,
                    "passed": bool(passed),
                }
            )
    payload = {
        "fixture_id": spec["id"],
        "vi_sha256": digest,
        "lvkit_loaded_from": lvkit.__file__,
        "generated_module": str(modules[0]) if len(modules) == 1 else None,
        "generated_sha256": hashlib.sha256(modules[0].read_bytes()).hexdigest()
        if len(modules) == 1
        else None,
        "conversion_command": command,
        "conversion_returncode": conversion.returncode,
        "comparison_policy": spec["outputs"],
        "passed": sum(case["passed"] for case in comparisons),
        "total": len(comparisons),
        "comparisons": comparisons,
    }
    (output / "report.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "passed": payload["passed"],
                "total": payload["total"],
                "conversion_returncode": conversion.returncode,
                "setup_error": setup_error,
            }
        )
    )
    raise SystemExit(0 if payload["passed"] == payload["total"] else 1)


if __name__ == "__main__":
    main()
