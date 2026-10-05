"""Native LLB member extraction and values are verifiable without LabVIEW."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from lvkit import extractor
from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from lvkit.graph.models import PrimitiveNode
from numeric_values import decode, encode

FIXTURE = Path(__file__).parent / "fixtures" / "llb_stream_lifetime"
SPEC = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
GOLD = json.loads((FIXTURE / "golden_labview.json").read_text(encoding="utf-8"))


@pytest.fixture
def extracted(tmp_path, monkeypatch):
    archive = FIXTURE / SPEC["vi_file"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == GOLD["archive_sha256"]
    monkeypatch.setenv("LVKIT_CACHE_DIR", str(tmp_path / "cache"))
    return extractor.extract_llb(archive)


def test_extracted_bytes_match_independent_inventory(extracted):
    actual = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in extracted.glob("*.vi")
    }
    assert actual == GOLD["member_sha256"]


@pytest.mark.parametrize(
    "case", GOLD["cases"], ids=lambda case: case["member"] + ":" + case["id"]
)
def test_generated_member_matches_native(extracted, case):
    path = extracted / case["member"]
    assert path.is_file(), "Native member absent from extraction"
    assert (
        hashlib.sha256(path.read_bytes()).hexdigest()
        == GOLD["member_sha256"][case["member"]]
    )
    graph = InMemoryVIGraph()
    key = graph.load_vi(path, mode=LoadMode.MINIMAL, search_paths=[])
    assert not any(isinstance(node, PrimitiveNode) for node in graph.iter_nodes(key))
    code = build_module(graph.get_vi_context(key), path.name, graph=graph)
    namespace = {}
    exec(compile(code, str(path), "exec"), namespace)
    function = namespace[path.stem]
    inputs = {name: decode(value) for name, value in case["effective_inputs"].items()}
    actual = {
        name: encode(value) for name, value in function(**inputs)._asdict().items()
    }
    assert actual == case["outputs"]
    assert {name: encode(value) for name, value in inputs.items()} == case[
        "effective_inputs"
    ]
