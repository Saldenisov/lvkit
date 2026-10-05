"""Read authored LLB member bytes with the source stream explicitly kept open."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from lvkit import extractor


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    args = parser.parse_args()
    fixture = args.fixture.resolve()
    spec = json.loads((fixture / "spec.json").read_text(encoding="utf-8"))
    assert spec["id"] == "llb_stream_lifetime"
    archive = fixture / spec["vi_file"]
    original = digest(archive.read_bytes())
    options = extractor._make_read_po(
        xml="",
        rsrc=str(archive),
        filebase=archive.stem,
        keep_names=True,
        raw_connectors=False,
    )
    members, blocks = {}, {}
    with archive.open("rb") as stream:
        resource = extractor._lv_rsrc.VI(
            options, rsrc_fh=stream, text_encoding=extractor.labview_text_encoding()
        )
        for ident in ("UCRF", "CPRF", "ZCRF"):
            block = resource.get(ident)
            if block is None:
                continue
            blocks[ident] = len(block.sections)
            for index, section in block.sections.items():
                if not section.name_text:
                    continue
                name = section.name_text.decode(resource.textEncoding)
                if name not in spec["members"]:
                    continue
                data = block.getData(section_num=index).read()
                members[name] = {
                    "sha256": digest(data),
                    "size": len(data),
                    "block": ident,
                    "section": index,
                }
    assert set(members) == set(spec["members"]), members
    assert digest(archive.read_bytes()) == original
    payload = {
        "fixture_id": spec["id"],
        "archive_sha256": original,
        "source_script": Path(__file__).name,
        "source_script_sha256": digest(Path(__file__).read_bytes()),
        "method": "pylabview VI/getData while original filesystem stream remains open; independent of _open_llb_vi/extract_llb",
        "blocks": blocks,
        "members": members,
    }
    (fixture / "archive_inventory.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
