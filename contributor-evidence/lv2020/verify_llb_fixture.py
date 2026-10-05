"""Extract/convert an authored LLB and compare both members to native outputs."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import lvkit
from lvkit import extractor
from numeric_values import decode, encode


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--cache-dir", type=Path)
    args = parser.parse_args()
    fixture, output = args.fixture.resolve(), args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    golden = json.loads((fixture / "golden_labview.json").read_text(encoding="utf-8"))
    assert spec["id"] == "llb_stream_lifetime"
    archive = fixture / spec["vi_file"]
    assert digest(archive) == golden["archive_sha256"]
    cache = args.cache_dir.resolve() if args.cache_dir else output / "cache"
    if cache.exists():
        raise ValueError(
            "Use a new output directory: native qualification requires a cold cache"
        )
    os.environ["LVKIT_CACHE_DIR"] = str(cache)
    extracted = extractor.extract_llb(archive)
    inventory = {}
    for member in spec["members"]:
        path = extracted / member
        actual = digest(path) if path.is_file() else None
        inventory[member] = {
            "sha256": actual,
            "expected": golden["member_sha256"][member],
            "passed": actual == golden["member_sha256"][member],
        }
    command = [
        sys.executable,
        "-m",
        "lvkit",
        "generate",
        str(archive),
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
    comparisons, modules = [], {}
    for member in spec["members"]:
        stem = Path(member).stem
        candidates = [
            path
            for path in (output / "generated").rglob("*.py")
            if any(
                isinstance(node, ast.FunctionDef) and node.name == stem
                for node in ast.parse(path.read_text(encoding="utf-8")).body
            )
        ]
        function, failure = None, None
        if not inventory[member]["passed"]:
            failure = (
                "Member missing or extracted bytes differ from independent inventory"
            )
        elif result.returncode:
            failure = f"Conversion exited {result.returncode}"
        elif len(candidates) != 1:
            failure = f"Expected one module defining {stem}, found {len(candidates)}"
        else:
            path = candidates[0]
            modules[member] = {"path": str(path), "sha256": digest(path)}
            module_spec = importlib.util.spec_from_file_location(
                "llb_fixture_" + stem, path
            )
            assert module_spec and module_spec.loader
            module = importlib.util.module_from_spec(module_spec)
            try:
                module_spec.loader.exec_module(module)
                function = getattr(module, stem)
            except Exception as exc:
                failure = f"{type(exc).__name__}: {exc}"
        for case in (item for item in golden["cases"] if item["member"] == member):
            inputs = {
                name: decode(value) for name, value in case["effective_inputs"].items()
            }
            actual, error = None, failure
            if function is not None:
                try:
                    actual = {
                        name: encode(value)
                        for name, value in function(**inputs)._asdict().items()
                    }
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
            unchanged = {name: encode(value) for name, value in inputs.items()} == case[
                "effective_inputs"
            ]
            comparisons.append(
                {
                    "member": member,
                    "case": case["id"],
                    "expected": case["outputs"],
                    "actual": actual,
                    "error": error,
                    "input_unchanged": unchanged,
                    "passed": error is None and unchanged and actual == case["outputs"],
                }
            )
    assert digest(archive) == golden["archive_sha256"]
    payload = {
        "fixture_id": spec["id"],
        "archive_sha256": golden["archive_sha256"],
        "lvkit_loaded_from": lvkit.__file__,
        "cache_directory": str(cache),
        "inventory": inventory,
        "members_matched": sum(item["passed"] for item in inventory.values()),
        "members_total": len(inventory),
        "generated": modules,
        "conversion_command": command,
        "conversion_returncode": result.returncode,
        "passed": sum(item["passed"] for item in comparisons),
        "total": len(comparisons),
        "comparisons": comparisons,
    }
    (output / "report.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                key: payload[key]
                for key in (
                    "fixture_id",
                    "members_matched",
                    "members_total",
                    "passed",
                    "total",
                    "conversion_returncode",
                )
            },
            indent=2,
        )
    )
    raise SystemExit(
        0
        if payload["passed"] == payload["total"]
        and all(item["passed"] for item in inventory.values())
        else 1
    )


if __name__ == "__main__":
    main()
