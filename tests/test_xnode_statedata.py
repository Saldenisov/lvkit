"""Unit tests for the XNode ``<StateData>`` string decoders (#107 follow-up):
``_xnode_state_method_name``/``_xnode_state_row_names`` in
``lvkit.parser.node_types``.

Real ``<StateData>`` is an opaque, node-kind-specific binary blob (type
descriptors, enum item lists, a resource GUID, ...) with no public format
spec -- these tests pin the two verified, narrow signals pulled out of it: a
leading method name ("Invoke Method" nodes only), and every per-row
parameter/property name, each recorded TWICE in close succession (see
``XNodeNode``'s own docstring for the real-corpus verification -- RT_v1.vi's
"Raw data to RT.Configure" node and FPGA_v1.vi's "Antenna Status"/
"Longitude" property nodes). Synthetic blobs here mirror that exact shape
(4-byte-big-endian-length-prefixed UTF-8 strings) without pasting the real
(much longer) hex dumps.
"""

from __future__ import annotations

import struct

from lvkit.parser.node_types import (
    _xnode_state_method_name,
    _xnode_state_row_names,
    _xnode_state_strings,
)


def _pack(s: str) -> bytes:
    data = s.encode("utf-8")
    return struct.pack(">I", len(data)) + data


def _hex(*parts: bytes) -> str:
    return b"".join(parts).hex()


def test_method_name_is_the_first_string():
    blob = _hex(_pack("Run"), b"\x00\x01\x02\x03", _pack("Configure FIFO"))
    assert _xnode_state_method_name(blob) == "Run"


def test_method_name_absent_blob_is_empty():
    assert _xnode_state_method_name(None) == ""
    assert _xnode_state_method_name("") == ""


def test_method_name_non_string_leading_bytes_is_empty():
    # A "Read/Write Control"/"Open FPGA VI Reference" node's leading bytes
    # aren't a string at all -- must be "", never a garbled guess.
    blob = _hex(b"\x00\x00\x00\x00\xff\xff\xff\xff")
    assert _xnode_state_method_name(blob) == ""


def test_row_names_finds_adjacent_identical_pairs():
    # Mirrors FPGA_v1.vi's real "FPGA I/O Property Node" shape: a leading
    # singleton (the "Mod4.{GUID}" resource identifier -- never paired),
    # then one pair per row, each separated by unrelated binary noise.
    blob = _hex(
        _pack("Mod4.{SOME-GUID}"),
        b"\x00" * 6,
        _pack("Antenna Status"),
        b"\xff" * 40,
        _pack("Antenna Status"),
        b"\x00" * 10,
        _pack("Satellites Available"),
        b"\xff" * 20,
        _pack("Satellites Available"),
    )
    assert _xnode_state_row_names(blob) == ["Antenna Status", "Satellites Available"]


def test_row_names_keeps_the_longer_of_a_prefix_pair():
    # Mirrors "Longitude" -> "Longitude (°)": the real display name adds
    # a unit suffix on its second occurrence -- keep that richer copy.
    blob = _hex(_pack("Longitude"), b"\x00" * 8, _pack("Longitude (°)"))
    assert _xnode_state_row_names(blob) == ["Longitude (°)"]


def test_row_names_unpaired_singleton_is_not_a_row():
    # A string with no matching second occurrence anywhere nearby (an enum
    # item, a class name, ...) is incidental metadata, not a row.
    blob = _hex(_pack("Normal"), b"\x00" * 4, _pack("Unrelated"))
    assert _xnode_state_row_names(blob) == []


def test_row_names_excludes_the_method_name_itself():
    # The invoked method is ALSO recorded as a row-name pair elsewhere in the
    # same blob (real-corpus-verified) -- XNodeHandler.parse filters it out;
    # this pins that _xnode_state_row_names alone does NOT do the filtering
    # (that's the caller's job, since only Invoke Method nodes have one).
    blob = _hex(
        _pack("Run"),
        b"\x00" * 4,
        _pack("Requested Depth"),
        b"\x00" * 4,
        _pack("Requested Depth"),
        b"\x00" * 4,
        _pack("Run"),
        b"\x00" * 4,
        _pack("Run"),
    )
    names = _xnode_state_row_names(blob)
    assert names == ["Requested Depth", "Run"]


def test_row_names_absent_blob_is_empty_list():
    assert _xnode_state_row_names(None) == []
    assert _xnode_state_row_names("") == []


def test_state_strings_ignores_non_utf8_and_non_printable_runs():
    noise = struct.pack(">I", 3) + b"\x00\x01\x02"
    blob = _hex(_pack("Valid"), b"\xff\xfe\xfd\xfc", noise)
    assert _xnode_state_strings(bytes.fromhex(blob)) == ["Valid"]
