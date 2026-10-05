"""LabVIEW-free regression: real VI -> graph -> Python -> native golden values."""

from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path

import pytest
from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode

FIXTURES = [
    Path(__file__).parent / "fixtures" / name
    for name in ("array_add_literal", "enum_saved_default")
]
CASES = [
    (fixture, case)
    for fixture in FIXTURES
    for case in json.loads((fixture / "spec.json").read_text(encoding="utf-8"))["cases"]
]


@lru_cache(maxsize=2)
def generated_function(fixture):
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    golden = json.loads((fixture / "golden_labview.json").read_text(encoding="utf-8"))
    vi = fixture / spec["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == golden["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    code = build_module(graph.get_vi_context(key), spec["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    expected = {case["id"]: case["outputs"] for case in golden["cases"]}
    return namespace[spec["function"]], expected


@pytest.mark.parametrize(
    "fixture,case",
    CASES,
    ids=[f"{fixture.name}/{case['id']}" for fixture, case in CASES],
)
def test_real_vi_matches_native_labview(fixture, case):
    function, expected = generated_function(fixture)
    inputs = copy.deepcopy(case["inputs"])
    result = function(**inputs)
    assert dict(result._asdict()) == expected[case["id"]]
    assert inputs == case["inputs"]
