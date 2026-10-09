"""A synthetic caller binding reads the result of the actual saved native VI."""

import hashlib
import json
import os
from pathlib import Path

from lvkit.codegen.builder import build_module
from lvkit.codegen.context import CodeGenContext
from lvkit.codegen.nodes.subvi import _build_output_bindings
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from lvkit.graph.models import VINode
from lvkit.models import Terminal


def test_caller_binding_reads_native_callee_result():
    root = Path(os.environ["LVKIT_EVIDENCE_ROOT"]) / "fixtures" / "underscore_output"
    spec = json.loads((root / "spec.json").read_text(encoding="utf-8"))
    gold = json.loads((root / "golden_labview.json").read_text(encoding="utf-8"))
    vi = root / spec["vi_file"]
    assert hashlib.sha256(vi.read_bytes()).hexdigest() == gold["vi_sha256"]
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    code = build_module(graph.get_vi_context(key), spec["vi_file"], graph=graph)
    namespace = {}
    exec(compile(code, str(vi), "exec"), namespace)
    result = namespace[spec["function"]]()
    node = VINode(
        id="caller:callee", vi_path="Caller.vi", name=spec["vi_file"],
        terminals=[Terminal(id="caller:output", index=0, direction="output", name="_status")],
    )
    bindings = _build_output_bindings(node, "callee_result", None, CodeGenContext())
    assert bindings["caller:output"] == "callee_result.output_status"
    assert eval(bindings["caller:output"], {"callee_result": result}) == gold["cases"][0]["outputs"]["_status"]
