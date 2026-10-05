"""Generated integer cases match independently recorded LabVIEW outputs."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

import pytest
from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from lvkit.graph.models import CaseStructureNode
from numeric_values import encode

FIXTURE = Path(__file__).parent / "fixtures" / "case_default_zero"
SPEC = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
GOLD = json.loads((FIXTURE / "golden_labview.json").read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in SPEC["cases"]}


@lru_cache(maxsize=1)
def loaded_fixture():
    vi = FIXTURE / SPEC["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == GOLD["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    nodes = [n for n in graph.iter_nodes(key) if isinstance(n, CaseStructureNode)]
    assert len(nodes) == 1
    code = build_module(graph.get_vi_context(key), SPEC["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    return nodes[0], namespace[SPEC["function"]]


def test_native_first_frame_is_default_and_retains_zero_range():
    case, _ = loaded_fixture()
    assert [frame.is_default for frame in case.frames] == [True, False]
    assert [frame.selector_value for frame in case.frames] == ["0", "1"]
    assert [[(r.start, r.end) for r in f.selector_ranges] for f in case.frames] == [
        [(0, 0)],
        [(1, 1)],
    ]


@pytest.mark.parametrize("case", GOLD["cases"], ids=lambda case: case["id"])
def test_generated_integer_case_matches_native(case):
    provided = CASES[case["id"]]["inputs"].copy()
    _, function = loaded_fixture()
    result = function(**provided)
    assert {name: encode(value) for name, value in result._asdict().items()} == case[
        "outputs"
    ]
    assert provided == CASES[case["id"]]["inputs"]
