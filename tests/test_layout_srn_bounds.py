"""Regression (#107): an sRN (shift-register node)'s OWN ``<bounds>`` is a
translation for out-of-diagram terminal REFERENCES, not a real page position
(see ``_visit``'s own comment in ``parser/layout.py`` -- it already avoids
using this box as the origin for the sRN's children). It must also stay OUT
of ``Layout.node_bounds`` -- the union ``Layout.scene_bounds()`` takes for the
whole diagram's viewBox -- or a LabVIEW-internal placeholder value unrelated
to anything actually drawn silently balloons the page by tens of thousands of
units (a real corpus VI's scene went from ~4000x1300 to ~27000x13500 from
exactly one such sRN).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from lvkit.parser.layout import build_layout_from_root


def test_srn_own_bounds_excluded_from_node_bounds():
    # A degenerate, far-flung sRN bounds (LabVIEW's real convention for this
    # tag -- see #107) alongside an ordinary, real node with sane bounds.
    root = ET.fromstring(
        """
        <root>
          <nodeList>
            <SL__arrayElement class="sRN" uid="996">
              <bounds>(-25250, -12378, -25250, -12378)</bounds>
              <termList></termList>
            </SL__arrayElement>
          </nodeList>
          <zPlaneList>
            <SL__arrayElement class="prim" uid="p1">
              <bounds>(0, 0, 20, 10)</bounds>
              <termList></termList>
            </SL__arrayElement>
          </zPlaneList>
        </root>
        """
    )
    layout = build_layout_from_root(root)
    assert "996" not in layout.node_bounds
    assert "p1" in layout.node_bounds
    # Padded around the one real node (p1) -- nowhere near the sRN's
    # degenerate (-25250, -12378) corner, which would blow this out to a
    # ~25000-unit-wide scene if it weren't excluded.
    x1, y1, x2, y2 = layout.scene_bounds()
    assert x2 - x1 < 200
    assert y2 - y1 < 200


def test_non_srn_own_bounds_still_recorded():
    # Sanity: the exclusion is specific to class="sRN", not a blanket
    # nodeList-vs-zPlaneList distinction -- a decompose-structure border tab
    # (also found in nodeList) keeps its own bounds.
    root = ET.fromstring(
        """
        <root>
          <nodeList>
            <SL__arrayElement class="decomposeClusterNode" uid="d1">
              <bounds>(0, 0, 15, 8)</bounds>
              <termList></termList>
            </SL__arrayElement>
          </nodeList>
        </root>
        """
    )
    layout = build_layout_from_root(root)
    assert "d1" in layout.node_bounds
