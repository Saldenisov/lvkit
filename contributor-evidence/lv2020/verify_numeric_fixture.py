"""Generate and execute a numeric fixture, comparing against native receipts."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import lvkit
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
    result = subprocess.run(command, capture_output=True, text=True)
    (output / "conversion.log").write_text(
        result.stdout + result.stderr, encoding="utf-8"
    )
    if result.returncode:
        raise RuntimeError(f"Conversion failed; see {output / 'conversion.log'}")
    modules = [
        path
        for path in (output / "generated").rglob("*.py")
        if path.name != "__init__.py"
    ]
    if len(modules) != 1:
        raise ValueError(f"Expected one generated VI module, found {len(modules)}")
    module_spec = importlib.util.spec_from_file_location("numeric_fixture", modules[0])
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    function = getattr(module, spec["function"])
    expected = {case["id"]: case["outputs"] for case in golden["cases"]}
    comparisons = []
    for case in spec["cases"]:
        inputs = {name: decode(value) for name, value in case["inputs"].items()}
        before = copy.deepcopy(case["inputs"])
        actual, error = {}, None
        try:
            actual = {
                name: encode(value)
                for name, value in function(**inputs)._asdict().items()
            }
        except Exception as failure:
            error = f"{type(failure).__name__}: {failure}"
        unchanged = {name: encode(value) for name, value in inputs.items()} == before
        for name in spec["outputs"]:
            comparisons.append(
                {
                    "case": case["id"],
                    "output": name,
                    "expected": expected[case["id"]][name],
                    "actual": actual.get(name),
                    "error": error,
                    "input_unchanged": unchanged,
                    "passed": error is None
                    and unchanged
                    and actual.get(name) == expected[case["id"]][name],
                }
            )
    payload = {
        "fixture_id": spec["id"],
        "vi_sha256": digest,
        "lvkit_loaded_from": lvkit.__file__,
        "generated_module": str(modules[0]),
        "generated_sha256": hashlib.sha256(modules[0].read_bytes()).hexdigest(),
        "conversion_command": command,
        "passed": sum(case["passed"] for case in comparisons),
        "total": len(comparisons),
        "comparisons": comparisons,
    }
    (output / "report.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, allow_nan=False))
    raise SystemExit(0 if payload["passed"] == payload["total"] else 1)


if __name__ == "__main__":
    main()
