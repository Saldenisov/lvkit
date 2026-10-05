"""Export only structural XML and stored selector facts for the native fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from dataclasses import asdict
from pathlib import Path

from lvkit.extractor import extract_vi_xml
from lvkit.parser.nodes.case import parse_selector_tables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    fixture = args.fixture.resolve()
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    vi = fixture / spec["vi_file"]
    bd_xml, fp_xml, main_xml = extract_vi_xml(vi)
    case_nodes = ET.parse(bd_xml).getroot().findall(".//*[@class='select']")
    assert len(case_nodes) == 1
    case = case_nodes[0]
    ranges = case.findall("SelectRangeArray32/SL__arrayElement")
    tables = parse_selector_tables(ET.parse(main_xml).getroot()) if main_xml else []
    args.output_dir.mkdir(parents=True, exist_ok=True)
    files = {}
    for path in (bd_xml, fp_xml, main_xml):
        if path is not None:
            target = args.output_dir / path.name
            shutil.copyfile(path, target)
            files[target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
    report = {
        "vi_sha256": hashlib.sha256(vi.read_bytes()).hexdigest(),
        "select_default_case_field": case.findtext("SelectDefaultCase"),
        "stored_display_label": case.findtext("selString/textRec/text"),
        "heap_ranges": [
            {
                key: int(item.findtext(key, "0"))
                for key in ("start", "end", "startRangeType", "endRangeType", "diagramIdx")
            }
            for item in ranges
        ],
        "selector_tables": [asdict(table) for table in tables],
        "xml_sha256": files,
        "scope": "Only XML was copied; no extracted icon or rendered NI artwork is exported.",
    }
    (args.output_dir / "stored_selector.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
