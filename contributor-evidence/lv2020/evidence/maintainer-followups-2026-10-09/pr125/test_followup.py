"""Replay all 13 saved native Index Array cases with three storage permutations.

The parsed connector indices are unchanged. LabVIEW is not rerun.
"""

import hashlib
import json
import os
import random
from pathlib import Path

import pytest

from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from lvkit.graph.models import PrimitiveNode
from numeric_values import decode, encode


@pytest.mark.parametrize("order", ["reverse", "rotate", "shuffle"])
def test_native_index_array_ignores_terminal_storage_order(order):
    root = Path(os.environ["LVKIT_EVIDENCE_ROOT"]) / "fixtures" / "expanded_index_array"
    spec = json.loads((root / "spec.json").read_text(encoding="utf-8"))
    gold = json.loads((root / "golden_labview.json").read_text(encoding="utf-8"))
    vi = root / spec["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == gold["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    nodes = [node for node in graph.iter_nodes(key) if isinstance(node, PrimitiveNode)]
    assert len(nodes) == 1 and nodes[0].node_type == "aIndx"
    terminals = list(nodes[0].terminals)
    identity = {term.id: term.index for term in terminals}
    if order == "reverse":
        terminals.reverse()
    elif order == "rotate":
        terminals = terminals[3:] + terminals[:3]
    else:
        random.Random(20261009).shuffle(terminals)
    nodes[0].terminals = terminals
    assert {term.id: term.index for term in terminals} == identity
    code = build_module(graph.get_vi_context(key), spec["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    fn = namespace[spec["function"]]
    cases = {case["id"]: case for case in spec["cases"]}
    assert len(gold["cases"]) == 13
    for case in gold["cases"]:
        provided = cases[case["id"]]["inputs"]
        inputs = {name: decode(value) for name, value in provided.items()}
        result = fn(**inputs)
        assert {name: encode(value) for name, value in result._asdict().items()} == case["outputs"]
        assert {name: encode(value) for name, value in inputs.items()} == provided
