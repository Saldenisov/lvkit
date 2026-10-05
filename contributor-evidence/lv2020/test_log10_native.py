"""Generated log10 matches 13 saved native LabVIEW 2020 array cases."""

from __future__ import annotations

import hashlib
import json
from functools import cache
from pathlib import Path

import pytest
from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from compare_numeric_values import matches
from numeric_values import decode, encode

FIXTURE = Path(__file__).parent / "fixtures" / "real64_log10_array"
SPEC = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
GOLD = json.loads((FIXTURE / "golden_labview.json").read_text(encoding="utf-8"))


@cache
def generated_function():
    vi = FIXTURE / SPEC["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == GOLD["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    context = graph.get_vi_context(key)
    primitive = [
        node for node in graph.iter_nodes(key) if getattr(node, "prim_id", None)
    ]
    assert len(primitive) == 1 and primitive[0].prim_id == 1210
    code = build_module(context, SPEC["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    return namespace[SPEC["function"]]


@pytest.mark.parametrize("case", GOLD["cases"], ids=lambda case: case["id"])
def test_generated_log10_matches_native(case):
    inputs = {name: decode(value) for name, value in case["effective_inputs"].items()}
    actual = encode(generated_function()(**inputs).log_values)
    policy = SPEC["outputs"]["log_values"]
    assert matches(
        actual,
        case["outputs"]["log_values"],
        rel_tol=policy["relative_tolerance"],
        abs_tol=policy["absolute_tolerance"],
    )
    assert {name: encode(value) for name, value in inputs.items()} == case[
        "effective_inputs"
    ]
