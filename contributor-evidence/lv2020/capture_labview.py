"""Capture outputs of the self-contained fixture in installed LabVIEW 2020.

Requires Windows, LabVIEW 2020 and pywin32. No project VI is opened or saved.
NI documents _FlagAsMethod for Run at:
https://knowledge.ni.com/KnowledgeArticleDetails?id=kA0VU0000008tNV0AY&l=en-US
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()
    fixture = args.fixture.resolve()
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    if spec["id"] not in {"array_add_literal", "enum_saved_default"}:
        raise ValueError("Only the two authored fixtures are supported")
    vi_path = fixture / spec["vi_file"]
    digest = sha256(vi_path)

    import pythoncom
    import win32com.client
    import win32com.client.dynamic

    app = win32com.client.dynamic.Dispatch("LabVIEW.Application")
    if not str(app.Version).startswith("20.0."):
        raise RuntimeError(f"Expected LabVIEW 2020, got {app.Version}")
    app._FlagAsMethod("GetVIReference")
    reference = app.GetVIReference(str(vi_path))
    vi = win32com.client.dynamic.Dispatch(reference._oleobj_)
    vi._FlagAsMethod(
        "SetControlValue", "GetControlValue", "Run", "ReinitializeAllToDefault"
    )
    results = []
    for case in spec["cases"]:
        vi.ReinitializeAllToDefault()
        for name, value in case["inputs"].items():
            control_type = spec["inputs"][name]["type"]
            if control_type == "array<float64>":
                variant = win32com.client.VARIANT(
                    pythoncom.VT_ARRAY | pythoncom.VT_R8, value
                )
            elif control_type == "enum<uint16>":
                variant = win32com.client.VARIANT(pythoncom.VT_UI2, value)
            else:
                raise ValueError(f"Unsupported fixture input: {control_type}")
            vi.SetControlValue(name, variant)
        before = {}
        for name, control in spec["inputs"].items():
            value = vi.GetControlValue(name)
            before[name] = (
                list(value) if control["type"] == "array<float64>" else int(value)
            )
            expected_input = case["inputs"].get(name, control.get("saved_default"))
            if before[name] != expected_input:
                raise AssertionError(
                    f"Input/default transfer failed: {case['id']}/{name}"
                )
        vi.Run(True)
        outputs = {}
        for name, control in spec["outputs"].items():
            value = vi.GetControlValue(name)
            outputs[name] = (
                list(value) if control["type"] == "array<float64>" else int(value)
            )
        for name, value in before.items():
            after = vi.GetControlValue(name)
            after = list(after) if isinstance(value, list) else int(after)
            if after != value:
                raise AssertionError(f"Input changed: {case['id']}/{name}")
        results.append(
            {"id": case["id"], "effective_inputs": before, "outputs": outputs}
        )
    if sha256(vi_path) != digest:
        raise AssertionError("VI changed on disk during capture")
    payload = {
        "schema_version": 1,
        "fixture_id": spec["id"],
        "vi_sha256": digest,
        "oracle": {
            "kind": "native_labview_execution",
            "version": str(app.Version),
            "application_directory": str(app.ApplicationDirectory),
            "python": platform.python_version(),
            "captured_utc": datetime.now(timezone.utc).isoformat(),
            "method": (
                "ReinitializeAllToDefault / SetControlValue / "
                "Run(wait_until_done=True) / GetControlValue"
            ),
            "source_script": "capture_labview.py",
            "source_script_sha256": sha256(Path(__file__)),
        },
        "cases": results,
    }
    output = fixture / "golden_labview.json"
    output.write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"output": str(output), "vi_sha256": digest, "native_cases": len(results)}
        )
    )


if __name__ == "__main__":
    main()
