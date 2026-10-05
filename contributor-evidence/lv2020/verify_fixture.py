"""Convert a fixture with the selected checkout and compare native golden outputs.

Run with that checkout's src directory on PYTHONPATH. LabVIEW is not required.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    fixture = args.fixture.resolve()
    output = args.output_dir.resolve()
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    golden = json.loads((fixture / "golden_labview.json").read_text(encoding="utf-8"))
    vi_path = fixture / spec["vi_file"]
    digest = hashlib.sha256(vi_path.read_bytes()).hexdigest()
    if golden["fixture_id"] != spec["id"] or golden["vi_sha256"] != digest:
        raise ValueError("Golden data does not belong to this VI")
    expected = {case["id"]: case["outputs"] for case in golden["cases"]}
    if set(expected) != {case["id"] for case in spec["cases"]}:
        raise ValueError("Spec and golden case identifiers differ")
    output.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "lvkit",
        "generate",
        str(vi_path),
        "-o",
        str(output / "generated"),
        "--load-mode",
        "minimal",
        "--no-auto-vilib",
    ]
    run = subprocess.run(command, capture_output=True, text=True)
    (output / "conversion.log").write_text(run.stdout + run.stderr, encoding="utf-8")
    if run.returncode:
        raise RuntimeError(f"Conversion failed; see {output / 'conversion.log'}")
    modules = [
        path
        for path in (output / "generated").rglob("*.py")
        if path.name != "__init__.py"
    ]
    if len(modules) != 1:
        raise ValueError(f"Expected one generated VI module, got {modules}")
    module_spec = importlib.util.spec_from_file_location(
        "fixture_generated", modules[0]
    )
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    function = getattr(module, spec["function"])
    results = []
    for case in spec["cases"]:
        inputs = copy.deepcopy(case["inputs"])
        try:
            actual = dict(function(**inputs)._asdict())
            unchanged = inputs == case["inputs"]
            passed = actual == expected[case["id"]] and unchanged
            record = {"actual": actual, "input_unchanged": unchanged}
        except Exception as error:
            passed = False
            record = {"error": f"{type(error).__name__}: {error}"}
        results.append(
            {
                "id": case["id"],
                "passed": passed,
                "expected": expected[case["id"]],
                **record,
            }
        )
    import lvkit

    payload = {
        "fixture_id": spec["id"],
        "vi_sha256": digest,
        "lvkit_loaded_from": str(Path(lvkit.__file__).resolve()),
        "generated_module": str(modules[0]),
        "generated_sha256": hashlib.sha256(modules[0].read_bytes()).hexdigest(),
        "conversion_command": command,
        "passed": sum(case["passed"] for case in results),
        "total": len(results),
        "cases": results,
    }
    (output / "report.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "passed": payload["passed"],
                "total": payload["total"],
                "report": str(output / "report.json"),
            }
        )
    )
    return 0 if payload["passed"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
