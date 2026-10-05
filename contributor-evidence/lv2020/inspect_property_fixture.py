"""Export structural XML and exact Property Node terminal correlations."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from lvkit.extractor import extract_vi_xml
from lvkit.graph import InMemoryVIGraph
from lvkit.graph.loading import LoadMode
from lvkit.graph.models import PrimitiveNode
from lvkit.graph.op_walk import correlate_property_terminals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads((args.fixture / "spec.json").read_text(encoding="utf-8"))
    vi = args.fixture / spec["vi_file"]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for path in extract_vi_xml(vi):
        if path is not None:
            target = args.output_dir / path.name
            shutil.copyfile(path, target)
            files[target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
    graph = InMemoryVIGraph()
    key = graph.load_vi(vi, mode=LoadMode.MINIMAL, search_paths=[])
    nodes = [n for n in graph.iter_nodes(key) if isinstance(n, PrimitiveNode) and n.node_type == "propNode"]
    assert len(nodes) == 1
    node = nodes[0]
    payload = {"vi_sha256": hashlib.sha256(vi.read_bytes()).hexdigest(),
               "node": node.model_dump(mode="json"),
               "ordered_properties": [{"name": prop.name, "terminal": term.model_dump(mode="json") if term else None}
                                      for prop, term in correlate_property_terminals(node.properties or [], node.terminals, node.property_value_terminal_ids)],
               "xml_sha256": files}
    (args.output_dir / "stored_properties.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["ordered_properties"], indent=2))


if __name__ == "__main__":
    main()
