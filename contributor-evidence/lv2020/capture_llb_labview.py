"""Execute only independently authored fixture LLB members in LabVIEW 2020."""

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


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    args = parser.parse_args()
    fixture = args.fixture.resolve()
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    assert spec["id"] == "llb_stream_lifetime"
    assert spec["members"] == ["first.vi", "second.vi"]
    archive = fixture / spec["vi_file"]
    original = digest(archive)
    inventory = json.loads(
        (fixture / "archive_inventory.json").read_text(encoding="utf-8")
    )
    assert inventory["archive_sha256"] == original
    assert set(inventory["members"]) == set(spec["members"])
    app = win32com.client.dynamic.Dispatch("LabVIEW.Application")
    assert str(app.Version).startswith("20.0."), app.Version
    app._FlagAsMethod("GetVIReference")
    results = []
    for member in spec["members"]:
        reference = app.GetVIReference(str(archive / member))
        vi = win32com.client.dynamic.Dispatch(reference._oleobj_)
        vi._FlagAsMethod(
            "ReinitializeAllToDefault", "SetControlValue", "GetControlValue", "Run"
        )
        for case in spec["cases"]:
            vi.ReinitializeAllToDefault()
            vi.SetControlValue(
                "value",
                win32com.client.VARIANT(
                    pythoncom.VT_R8, decode(case["inputs"]["value"])
                ),
            )
            before = {"value": encode(vi.GetControlValue("value"))}
            assert before == case["inputs"], (member, case["id"], "input transfer")
            vi.Run(True)
            outputs = {"result": encode(vi.GetControlValue("result"))}
            assert {"value": encode(vi.GetControlValue("value"))} == before
            results.append(
                {
                    "member": member,
                    "id": case["id"],
                    "effective_inputs": before,
                    "outputs": outputs,
                }
            )
    assert digest(archive) == original, "Native execution changed saved archive"
    payload = {
        "schema_version": 1,
        "fixture_id": spec["id"],
        "vi_sha256": original,
        "archive_sha256": original,
        "member_sha256": {
            name: item["sha256"] for name, item in inventory["members"].items()
        },
        "oracle": {
            "kind": "native_labview_execution",
            "version": str(app.Version),
            "python": platform.python_version(),
            "captured_utc": datetime.now(timezone.utc).isoformat(),
            "method": "LLB member GetVIReference / ReinitializeAllToDefault / VT_R8 SetControlValue / Run(True) / GetControlValue",
            "source_script": Path(__file__).name,
            "source_script_sha256": digest(Path(__file__)),
            "numeric_encoding_script_sha256": digest(
                Path(__file__).with_name("numeric_values.py")
            ),
            "inventory_file_sha256": digest(fixture / "archive_inventory.json"),
        },
        "cases": results,
    }
    (fixture / "golden_labview.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
