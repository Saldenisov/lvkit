"""``SvgBackend.render()``'s root ``<svg>``: explicit ``width``/``height``
matching ``viewBox``, so a bare inline SVG (no width/height, only viewBox)
never falls to a browser's default replaced-element sizing -- which stretches
it to its container's full width and scales height to match, harmless-looking
for a wide block diagram but a 10x-oversized page for a tall, narrow front
panel (issue #101, 2026-09-28: a 128x582 front panel rendered at 1369x6224
CSS px in both `lvkit docs` and the interactive viewer)."""

from __future__ import annotations

import re

from lvkit.render.backend import SvgBackend


def _svg_tag(svg: str) -> str:
    (tag,) = re.findall(r"<svg\b[^>]*>", svg)
    return tag


def test_root_svg_width_height_match_viewbox() -> None:
    backend = SvgBackend()
    svg = backend.render((10.0, 20.0, 138.0, 602.0))
    tag = _svg_tag(svg)
    assert 'width="128"' in tag
    assert 'height="582"' in tag
    assert 'viewBox="10 20 128 582"' in tag


def test_root_svg_width_height_track_a_wide_bounds_too() -> None:
    """Not just the tall/narrow case -- the normal wide-diagram shape."""
    backend = SvgBackend()
    svg = backend.render((0.0, 0.0, 713.0, 249.0))
    tag = _svg_tag(svg)
    assert 'width="713"' in tag
    assert 'height="249"' in tag
