"""Three native numeric classifications from the newly authored VI."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

import pytest
from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from numeric_values import encode

FIXTURE = Path(__file__).parent / "fixtures" / "nonfinite_constants"


@lru_cache(maxsize=1)
def generated_result():
    spec = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
    golden = json.loads((FIXTURE / "golden_labview.json").read_text(encoding="utf-8"))
    vi = FIXTURE / spec["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == golden["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    code = build_module(graph.get_vi_context(key), spec["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    return namespace[spec["function"]]()._asdict(), golden["cases"][0]["outputs"]


@pytest.mark.parametrize("output", ["nan_result", "positive_inf", "negative_inf"])
def test_nonfinite_native_output(output):
    actual, expected = generated_result()
    assert encode(actual[output]) == expected[output]
