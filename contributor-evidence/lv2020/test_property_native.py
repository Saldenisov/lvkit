"""Execute the native leaf's generated code against saved LabVIEW outputs."""

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
from lvkit.graph.op_walk import correlate_property_terminals
from property_adapter import NumericReference

FIXTURE = Path(__file__).parent / "fixtures" / "property_write_read"
SPEC = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
GOLD = json.loads((FIXTURE / "golden_labview.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def loaded_fixture():
    for name, digest in GOLD["native_files_sha256"].items():
        assert hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() == digest
    graph = InMemoryVIGraph()
    vi = FIXTURE / SPEC["vi_file"]
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    nodes = [n for n in graph.iter_nodes(key) if isinstance(n, PrimitiveNode) and n.node_type == "propNode"]
    assert len(nodes) == 1
    code = build_module(graph.get_vi_context(key), SPEC["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    return nodes[0], namespace[SPEC["function"]]


def test_native_property_rows_are_write_then_read():
    node, _ = loaded_fixture()
    rows = correlate_property_terminals(node.properties or [], node.terminals, node.property_value_terminal_ids)
    assert [(prop.name, term.direction) for prop, term in rows] == [("Value", "input"), ("Value", "output")]


@pytest.mark.parametrize("case", GOLD["cases"], ids=lambda case: case["id"])
def test_generated_write_read_matches_native_result_state_and_order(case):
    _, function = loaded_fixture()
    ref = NumericReference(case["target_before"])
    inputs = case["effective_inputs"].copy()
    result = function(digital_in=ref, **inputs)
    assert result._asdict() == case["outputs"]
    assert ref.stored_value == case["target_after"]
    assert ref.events == [["write", inputs["value"]], ["read", inputs["value"]]]
    assert inputs == case["effective_inputs"]
