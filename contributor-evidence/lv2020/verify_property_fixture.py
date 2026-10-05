"""Execute generated explicit Property Node code against native receipts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import lvkit
from property_adapter import NumericReference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    fixture, output = args.fixture.resolve(), args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    gold = json.loads((fixture / "golden_labview.json").read_text(encoding="utf-8"))
    for name, digest in gold["native_files_sha256"].items():
        assert hashlib.sha256((fixture / name).read_bytes()).hexdigest() == digest
    command = [sys.executable, "-m", "lvkit", "generate", str(fixture / spec["vi_file"]),
               "-o", str(output / "generated"), "--load-mode", "minimal", "--no-auto-vilib"]
    conversion = subprocess.run(command, capture_output=True, text=True)
    (output / "conversion.log").write_text(conversion.stdout + conversion.stderr, encoding="utf-8")
    assert conversion.returncode == 0, conversion.stderr
    modules = [p for p in (output / "generated").rglob("*.py") if p.name != "__init__.py"]
    assert len(modules) == 1
    module_spec = importlib.util.spec_from_file_location("property_fixture", modules[0])
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    function = getattr(module, spec["function"])
    expected = {case["id"]: case for case in gold["cases"]}
    comparisons = []
    for case in spec["cases"]:
        ref = NumericReference(spec["reference"]["initial_value"])
        inputs = case["inputs"].copy()
        actual, error = {}, None
        try:
            actual = function(digital_in=ref, **inputs)._asdict()
        except Exception as failure:
            error = f"{type(failure).__name__}: {failure}"
        wanted = expected[case["id"]]
        events = [["write", inputs["value"]], ["read", inputs["value"]]]
        checks = {"result": actual == wanted["outputs"] and error is None,
                  "target_state": ref.stored_value == wanted["target_after"] and error is None,
                  "event_order": ref.events == events and error is None}
        comparisons.append({"id": case["id"], "expected_outputs": wanted["outputs"], "actual_outputs": actual,
                            "expected_target": wanted["target_after"], "actual_target": ref.stored_value,
                            "expected_events": events, "actual_events": ref.events, "error": error,
                            "input_unchanged": inputs == case["inputs"], "checks": checks})
    payload = {"fixture_id": spec["id"], "vi_sha256": gold["vi_sha256"],
               "lvkit_loaded_from": lvkit.__file__, "conversion_command": command,
               "generated_module": str(modules[0]), "generated_sha256": hashlib.sha256(modules[0].read_bytes()).hexdigest(),
               "passed": sum(all(c["checks"].values()) and c["input_unchanged"] for c in comparisons),
               "total": len(comparisons), "comparisons": comparisons}
    (output / "report.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"passed": payload["passed"], "total": payload["total"], "checks": {name: sum(c["checks"][name] for c in comparisons) for name in ("result", "target_state", "event_order")}}, indent=2))
    raise SystemExit(0 if payload["passed"] == payload["total"] else 1)


if __name__ == "__main__":
    main()
