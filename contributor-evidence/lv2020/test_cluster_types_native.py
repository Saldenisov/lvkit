"""Anonymous cluster annotations agree with native positional tuple values."""

from __future__ import annotations

import hashlib
import json
from functools import cache
from pathlib import Path
from typing import get_type_hints

import pytest
from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from lvkit.models import LVTypeKind
from numeric_values import decode, encode

FIXTURE = Path(__file__).parent / "fixtures" / "anonymous_cluster_identity"
SPEC = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
GOLD = json.loads((FIXTURE / "golden_labview.json").read_text(encoding="utf-8"))


@cache
def generated():
    vi = FIXTURE / SPEC["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == GOLD["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    context = graph.get_vi_context(key)
    for terminal in [*context.inputs, *context.outputs]:
        assert terminal.lv_type.kind == LVTypeKind.CLUSTER
        assert not terminal.lv_type.typedef_name and not terminal.lv_type.classname
        assert len(terminal.lv_type.fields) == 2
    source = build_module(context, SPEC["vi_file"], graph=graph)
    namespace = {}
    exec(compile(source, str(vi), "exec"), namespace)
    return namespace[SPEC["function"]], namespace


@pytest.mark.parametrize("case", GOLD["cases"], ids=lambda case: case["id"])
def test_native_cluster_output_values(case):
    inputs = {
        name: tuple(decode(value)) for name, value in case["effective_inputs"].items()
    }
    function, _ = generated()
    result = function(**inputs).cluster_out
    assert isinstance(result, tuple)
    assert encode(result) == case["outputs"]["cluster_out"]
    assert {name: encode(value) for name, value in inputs.items()} == case[
        "effective_inputs"
    ]


def test_native_cluster_parameter_annotation():
    function, namespace = generated()
    assert get_type_hints(function, globalns=namespace)["cluster_in"] == tuple | None


def test_native_cluster_result_annotation():
    function, namespace = generated()
    result_type = get_type_hints(function, globalns=namespace)["return"]
    assert get_type_hints(result_type, globalns=namespace)["cluster_out"] is tuple
