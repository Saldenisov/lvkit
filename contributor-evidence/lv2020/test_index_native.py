"""Expanded 1D Index Array matches the saved LabVIEW 2020 oracle."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

import pytest
from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from lvkit.graph.models import PrimitiveNode
from lvkit.models import LVTypeKind
from numeric_values import decode, encode

FIXTURE = Path(__file__).parent / "fixtures" / "expanded_index_array"
SPEC = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
GOLD = json.loads((FIXTURE / "golden_labview.json").read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in SPEC["cases"]}


@lru_cache(maxsize=1)
def generated_function():
    vi = FIXTURE / SPEC["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == GOLD["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    nodes = [node for node in graph.iter_nodes(key) if isinstance(node, PrimitiveNode)]
    assert len(nodes) == 1 and nodes[0].node_type == "aIndx"
    terminals = nodes[0].terminals
    assert len(terminals) == 7
    assert terminals[0].lv_type.kind == LVTypeKind.ARRAY
    assert terminals[0].lv_type.dimensions == 1
    assert [term.direction for term in terminals] == [
        "input", "output", "input", "output", "input", "output", "input"
    ]
    assert graph.terminal_is_wired(terminals[2].id)
    assert not graph.terminal_is_wired(terminals[4].id)
    assert not graph.terminal_is_wired(terminals[6].id)
    code = build_module(graph.get_vi_context(key), SPEC["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    return namespace[SPEC["function"]]


@pytest.mark.parametrize("case", GOLD["cases"], ids=lambda case: case["id"])
def test_generated_index_matches_native(case):
    provided = CASES[case["id"]]["inputs"]
    inputs = {name: decode(value) for name, value in provided.items()}
    result = generated_function()(**inputs)
    assert {name: encode(value) for name, value in result._asdict().items()} == case["outputs"]
    assert {name: encode(value) for name, value in inputs.items()} == provided
