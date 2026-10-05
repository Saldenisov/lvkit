"""Anonymous nested cluster updates match native LabVIEW 2020 receipts."""

from __future__ import annotations

import hashlib
import json
from functools import cache
from pathlib import Path

import pytest
from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from lvkit.graph.models import PrimitiveNode
from numeric_values import decode, encode
from verify_nested_cluster_fixture import cluster_tuple

FIXTURE = Path(__file__).parent / "fixtures" / "nested_cluster_fields"
SPEC = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
GOLD = json.loads((FIXTURE / "golden_labview.json").read_text(encoding="utf-8"))


@cache
def generated_function():
    vi = FIXTURE / SPEC["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == GOLD["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    nodes = [node for node in graph.iter_nodes(key) if isinstance(node, PrimitiveNode)]
    assert len(nodes) == 2 and all(node.node_type == "nMux" for node in nodes)
    fields = [term for node in nodes for term in node.terminals if term.nmux_role == "list"]
    assert len(fields) == 2 and all(term.nmux_field_index == 3 for term in fields)
    code = build_module(graph.get_vi_context(key), SPEC["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    return namespace[SPEC["function"]]


@pytest.mark.parametrize("case", GOLD["cases"], ids=lambda case: case["id"])
def test_generated_cluster_matches_native(case):
    inputs = {name: decode(value) for name, value in case["effective_inputs"].items()}
    inputs["cluster_in"] = cluster_tuple(inputs["cluster_in"])
    result = generated_function()(**inputs)
    assert isinstance(result.cluster_out, tuple)
    assert isinstance(result.cluster_out[1], tuple)
    assert {name: encode(value) for name, value in result._asdict().items()} == case["outputs"]
    assert {name: encode(value) for name, value in inputs.items()} == case["effective_inputs"]
