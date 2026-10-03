from __future__ import annotations

from dataclasses import dataclass

from ....parser.layout import Rect
from ...backend import Backend
from ...style import Theme
from .base import DrawerHeaderGlyphBase, _draw_drawer_row, draw_drawer_header


@dataclass(frozen=True)
class XNodeGlyph(DrawerHeaderGlyphBase):
    """An FPGA Interface XNode (class="xNode", #107): Open/Close FPGA VI
    Reference, Read/Write Control, Invoke Method, etc. Reuses the Property/
    Invoke-node drawer convention -- a header naming the node's own real
    class (``class_name``, from its ``<displayName>``), then one row per
    terminal EXCLUDING the reference (Refnum-typed) and error
    (``is_error_cluster``) pass-through pair, which thread the box edges
    from their own real heap geometry, same as any Property/Invoke node's
    permDCOList pair -- never drawn here. See ``_xnode_glyph`` (render/
    nodes.py) for how ``rows``/``method`` are built.

    ``method`` (an "Invoke Method" node's specific invoked method, e.g.
    "Run", "Wait on IRQ") draws as an extra row directly under the header,
    with NO arrows -- it is selected internally, never wired, exactly like
    InvokeNodeGlyph's own method row. Empty for every other XNode class
    (Open/Close FPGA VI Reference, Read/Write Control have no such row)."""

    method: str = ""
    # (terminal label, show_left, show_right)
    rows: tuple[tuple[str, bool, bool], ...] = ()

    def draw(self, backend: Backend, bounds: Rect, theme: Theme) -> None:
        x1, y1, x2, y2 = bounds
        stroke = getattr(theme, self.stroke_attr)
        text_fill = getattr(theme, self.text_attr)
        backend.rect(
            x1,
            y1,
            x2,
            y2,
            fill=getattr(theme, self.fill_attr),
            stroke=stroke,
            stroke_width=1.2,
        )
        rows = self.rows
        extra = 1 if self.method else 0
        cell_h = (y2 - y1) / (len(rows) + 1 + extra)
        lsize = max(5.0, min(9.0, cell_h * 0.62) - 1.0)

        hy2 = draw_drawer_header(
            backend,
            x1,
            x2,
            y1,
            cell_h,
            is_implicit=self.is_implicit,
            target_name=self.target_name,
            class_name=self.class_name,
            bar_color=self.bar_color,
            stroke=stroke,
            text_fill=text_fill,
            lsize=lsize,
        )

        if self.method:
            my2 = hy2 + cell_h
            _draw_drawer_row(
                backend,
                x1,
                x2,
                hy2,
                my2,
                self.method,
                show_left=False,
                show_right=False,
                text_fill=text_fill,
                lsize=lsize,
            )
            backend.line(x1, my2, x2, my2, stroke=stroke, stroke_width=1.0)
            hy2 = my2

        for i, (label, show_left, show_right) in enumerate(rows):
            ry1 = hy2 + i * cell_h
            ry2 = hy2 + (i + 1) * cell_h
            if i > 0:
                backend.line(x1, ry1, x2, ry1, stroke=stroke, stroke_width=1.0)
            _draw_drawer_row(
                backend,
                x1,
                x2,
                ry1,
                ry2,
                label,
                show_left=show_left,
                show_right=show_right,
                text_fill=text_fill,
                lsize=lsize,
            )
