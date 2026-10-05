"""Capture the native write/read leaf via its independently authored harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import pythoncom
import win32com.client
import win32com.client.dynamic
from numeric_values import encode


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    fixture = parser.parse_args().fixture.resolve()
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    assert spec["id"] == "property_write_read"
    hashes = {name: digest(fixture / name) for name in (spec["vi_file"], spec["harness_file"])}
    app = win32com.client.dynamic.Dispatch("LabVIEW.Application")
    assert str(app.Version).startswith("20.0."), app.Version
    app._FlagAsMethod("GetVIReference")
    reference = app.GetVIReference(str(fixture / spec["harness_file"]))
    vi = win32com.client.dynamic.Dispatch(reference._oleobj_)
    vi._FlagAsMethod("ReinitializeAllToDefault", "SetControlValue", "GetControlValue", "Run")
    results = []
    for case in spec["cases"]:
        vi.ReinitializeAllToDefault()
        vi.SetControlValue("target", win32com.client.VARIANT(pythoncom.VT_UI4, spec["reference"]["initial_value"]))
        vi.SetControlValue("value", win32com.client.VARIANT(pythoncom.VT_UI4, case["inputs"]["value"]))
        before = {"value": encode(vi.GetControlValue("value"))}
        target_before = vi.GetControlValue("target")
        assert before == case["inputs"], (case["id"], "input transfer", before)
        assert target_before == spec["reference"]["initial_value"]
        vi.Run(True)
        immediate = {"result": vi.GetControlValue("result"), "target": vi.GetControlValue("target")}
        # Run(True) can precede publication of the indicator to this COM client.
        # Fixed delays are independent of expected values; retain all observations.
        time.sleep(0.2)
        settled = {"result": vi.GetControlValue("result"), "target": vi.GetControlValue("target")}
        time.sleep(0.05)
        confirmation = {"result": vi.GetControlValue("result"), "target": vi.GetControlValue("target")}
        assert settled == confirmation, (case["id"], "COM observation not stable")
        outputs = {"result": encode(confirmation["result"])}
        target_after = confirmation["target"]
        assert vi.GetControlValue("value") == before["value"], "Numeric input changed"
        results.append({"id": case["id"], "effective_inputs": before, "outputs": outputs, "target_before": target_before, "target_after": target_after,
                        "com_observations": {"immediate": immediate, "after_200_ms": settled, "after_250_ms": confirmation}})
    assert hashes == {name: digest(fixture / name) for name in hashes}, "Saved VI changed"
    payload = {
        "schema_version": 1, "fixture_id": spec["id"],
        "vi_sha256": hashes[spec["vi_file"]], "native_files_sha256": hashes,
        "oracle": {"kind": "native_labview_execution", "version": str(app.Version),
                   "python": platform.python_version(), "captured_utc": datetime.now(timezone.utc).isoformat(),
                   "method": "Native harness / ReinitializeAllToDefault / VT_UI4 SetControlValue / Run(True) / fixed 200 ms delay / GetControlValue / 50 ms stable confirmation",
                   "source_script": Path(__file__).name, "source_script_sha256": digest(Path(__file__)),
                   "numeric_encoding_script_sha256": digest(Path(__file__).with_name("numeric_values.py"))},
        "cases": results,
    }
    (fixture / "golden_labview.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
