"""Generated output-name mapping against a native LabVIEW 2020 receipt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lvkit.codegen.builder import build_module
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode

FIXTURE = Path(__file__).parent / "fixtures" / "underscore_output"


def test_underscore_output_matches_native_value():
    spec = json.loads((FIXTURE / "spec.json").read_text(encoding="utf-8"))
    golden = json.loads((FIXTURE / "golden_labview.json").read_text(encoding="utf-8"))
    vi = FIXTURE / spec["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == golden["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    code = build_module(graph.get_vi_context(key), spec["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    result = namespace[spec["function"]]()._asdict()
    assert result == {"output_status": golden["cases"][0]["outputs"]["_status"]}
