"""Division emission selected from the primitive's resolved numeric types."""

from __future__ import annotations

from lvkit.graph.models import PrimitiveNode
from lvkit.models import LVType, LVTypeKind
from lvkit.primitive_resolver import ResolvedPrimitive

from . import register_op


def _is_real64(lv_type: LVType | None) -> bool:
    if lv_type is None:
        return False
    if lv_type.kind == LVTypeKind.ARRAY:
        return _is_real64(lv_type.element_type)
    return (
        lv_type.kind == LVTypeKind.PRIMITIVE and lv_type.underlying_type == "NumFloat64"
    )


@register_op("DIVIDE")
def divide(node: PrimitiveNode, resolved: ResolvedPrimitive) -> str:
    if node.terminals and all(_is_real64(term.lv_type) for term in node.terminals):
        return "_lv.real64_divide(in_2, in_1)"
    return "in_2 / in_1"
