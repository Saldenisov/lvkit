"""Regression: a while/for loop's inner-node collection must catch a nested
flat sequence the same way case.py/sequence.py/event.py already do (see
test_frame_zplane.py) -- LabVIEW lists a nested flat sequence's inner
``sequenceFrame`` in the loop body's ``nodeList`` but the ``flatSequence``
structure itself ONLY in ``zPlaneList``.

Real case (issue #107): RT_v1.vi's Timed Loop has a nested flat sequence
(``Analogue capture`` / ``Time Information`` / ``TCP Stream``) orphaned to
root (``node.parent`` never stamped), so the loop's own opaque background --
painted as a "sibling" at a different point in the document -- covered the
flat sequence and everything inside it. loop.py previously did its own
hand-rolled ``nodeList``-only walk instead of reusing the already-fixed
``frame_inner_node_uids`` helper.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from lvkit.parser.nodes.loop import extract_loops


def _while_loop(nodelist: str, zplane: str) -> ET.Element:
    xml = f"""
    <root>
      <SL__arrayElement class="whileLoop" uid="698">
        <termList></termList>
        <diagramList>
          <SL__arrayElement class="diag" uid="702">
            <nodeList>{nodelist}</nodeList>
            <zPlaneList>{zplane}</zPlaneList>
          </SL__arrayElement>
        </diagramList>
      </SL__arrayElement>
    </root>
    """
    return ET.fromstring(xml)


def test_zplane_only_flat_sequence_is_captured_in_a_loop():
    root = _while_loop(
        # nodeList uniquely carries the flat seq's inner frame (+ anything else)
        '<SL__arrayElement class="sequenceFrame" uid="10969"/>',
        # zPlaneList uniquely carries the flatSequence STRUCTURE itself
        '<SL__arrayElement class="flatSequence" uid="3192"/>',
    )
    loops = extract_loops(root)
    assert len(loops) == 1
    uids = loops[0].inner_node_uids
    assert "10969" in uids  # nodeList member preserved (unchanged behaviour)
    assert "3192" in uids  # the flatSequence STRUCTURE is no longer orphaned


def test_no_double_count_when_in_both_lists():
    root = _while_loop(
        '<SL__arrayElement class="select" uid="20"/>',
        '<SL__arrayElement class="select" uid="20"/>',
    )
    loops = extract_loops(root)
    assert loops[0].inner_node_uids == ["20"]


def test_ordinary_loop_body_unaffected():
    root = _while_loop(
        '<SL__arrayElement class="prim" uid="10"/>'
        '<SL__arrayElement class="sRN" uid="856"/>',
        "",
    )
    loops = extract_loops(root)
    assert loops[0].inner_node_uids == ["10", "856"]
