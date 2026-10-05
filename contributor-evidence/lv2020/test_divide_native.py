"""DBL Divide matches saved LabVIEW 2020 outputs for 24 scalar cases."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

import pytest
from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from numeric_values import decode, encode

FIXTURE = Path(__file__).parent / "fixtures" / "real64_divide"
SPEC = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
GOLD = json.loads((FIXTURE / "golden_labview.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def generated_function():
    vi = FIXTURE / SPEC["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == GOLD["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    code = build_module(graph.get_vi_context(key), SPEC["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    return namespace[SPEC["function"]]


@pytest.mark.parametrize("case", GOLD["cases"], ids=lambda case: case["id"])
def test_generated_divide_matches_native(case):
    inputs = {name: decode(value) for name, value in case["effective_inputs"].items()}
    result = generated_function()(**inputs).quotient
    assert encode(result) == case["outputs"]["quotient"]
    assert {name: encode(value) for name, value in inputs.items()} == case[
        "effective_inputs"
    ]
