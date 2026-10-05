"""Logarithm Base 10 emission for resolved DBL scalars and arrays."""

from __future__ import annotations

from lvkit.graph.models import PrimitiveNode
from lvkit.models import LVType, LVTypeKind
from lvkit.primitive_resolver import ResolvedPrimitive

from ..base import CodeGenError
from . import register_op


def _is_real64(lv_type: LVType | None) -> bool:
    if lv_type is None:
        return False
    if lv_type.kind == LVTypeKind.ARRAY:
        return _is_real64(lv_type.element_type)
    return (
        lv_type.kind == LVTypeKind.PRIMITIVE and lv_type.underlying_type == "NumFloat64"
    )


@register_op("LOG10")
def log10(node: PrimitiveNode, resolved: ResolvedPrimitive) -> str:
    if not node.terminals or not all(
        _is_real64(term.lv_type) for term in node.terminals
    ):
        raise CodeGenError(
            "Logarithm Base 10 supports resolved DBL scalars and arrays only", node
        )
    return "_lv.log10(in_1)"
