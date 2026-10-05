"""Capture numeric outputs from newly authored LabVIEW 2020 fixture VIs."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import pythoncom
import win32com.client
import win32com.client.dynamic
from numeric_values import decode, encode

AUTHORED_FIXTURES = {"nonfinite_constants"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()
    fixture = args.fixture.resolve()
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    if spec["id"] not in AUTHORED_FIXTURES:
        raise ValueError("Only explicitly authored numeric fixtures are supported")
    path = fixture / spec["vi_file"]
    original = digest(path)
    app = win32com.client.dynamic.Dispatch("LabVIEW.Application")
    if not str(app.Version).startswith("20.0."):
        raise RuntimeError(f"Expected LabVIEW 2020, got {app.Version}")
    app._FlagAsMethod("GetVIReference")
    reference = app.GetVIReference(str(path))
    vi = win32com.client.dynamic.Dispatch(reference._oleobj_)
    vi._FlagAsMethod(
        "ReinitializeAllToDefault", "SetControlValue", "GetControlValue", "Run"
    )
    results = []
    for case in spec["cases"]:
        vi.ReinitializeAllToDefault()
        for name, value in case["inputs"].items():
            kind = spec["inputs"][name]["type"]
            if kind != "float64":
                raise ValueError(f"Unsupported numeric input type: {kind}")
            vi.SetControlValue(
                name, win32com.client.VARIANT(pythoncom.VT_R8, decode(value))
            )
        before = {name: encode(vi.GetControlValue(name)) for name in spec["inputs"]}
        assert before == case["inputs"], (case["id"], "input transfer")
        vi.Run(True)
        outputs = {name: encode(vi.GetControlValue(name)) for name in spec["outputs"]}
        after = {name: encode(vi.GetControlValue(name)) for name in spec["inputs"]}
        assert after == before, (case["id"], "input changed")
        results.append(
            {"id": case["id"], "effective_inputs": before, "outputs": outputs}
        )
    assert digest(path) == original, "VI changed on disk"
    payload = {
        "schema_version": 1,
        "fixture_id": spec["id"],
        "vi_sha256": original,
        "oracle": {
            "kind": "native_labview_execution",
            "version": str(app.Version),
            "python": platform.python_version(),
            "captured_utc": datetime.now(timezone.utc).isoformat(),
            "method": (
                "ReinitializeAllToDefault / SetControlValue / "
                "Run(True) / GetControlValue"
            ),
            "source_script": Path(__file__).name,
            "source_script_sha256": digest(Path(__file__)),
            "numeric_encoding_script_sha256": digest(
                Path(__file__).with_name("numeric_values.py")
            ),
        },
        "cases": results,
    }
    (fixture / "golden_labview.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
