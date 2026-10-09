"""Executable typed graphs for mixed representations and coerced float output.

These are synthetic tests; they do not establish SGL/EXT precision in LabVIEW.
"""

import math

import pytest

from lvkit.codegen.builder import build_module
from lvkit.graph.models import PrimitiveNode, VIContext, Wire
from lvkit.models import FPTerminal, LVType, LVTypeKind, Terminal
from tests.helpers import build_graph


def numeric_type(underlying, rank):
    scalar = LVType(kind=LVTypeKind.PRIMITIVE, underlying_type=underlying)
    return LVType(kind=LVTypeKind.ARRAY, element_type=scalar, dimensions=rank) if rank else scalar


@pytest.mark.parametrize("x_type,y_type,q_type", [
    ("NumInt32", "NumFloat64", "NumFloat32"),
    ("NumFloat32", "NumInt32", "NumFloatExt"),
    ("NumFloatExt", "NumFloat32", "NumFloat64"),
])
@pytest.mark.parametrize("rank", [0, 1])
def test_mixed_inputs_use_coerced_output_type(x_type, y_type, q_type, rank):
    types = [numeric_type(x_type, rank), numeric_type(y_type, 0), numeric_type(q_type, rank)]
    inputs = [FPTerminal(id=f"fp:{name}", index=i, direction="input", name=name,
                        is_public=True, is_indicator=False, lv_type=types[i])
              for i, name in enumerate(("numerator", "denominator"))]
    output = FPTerminal(id="fp:quotient", index=0, direction="output", name="quotient",
                        is_public=True, is_indicator=True, lv_type=types[2])
    node = PrimitiveNode(id="divide", vi_path="Mixed Divide.vi", name="Divide", prim_id=1053,
                         terminals=[Terminal(id="x", index=2, direction="input", lv_type=types[0]),
                                    Terminal(id="y", index=1, direction="input", lv_type=types[1]),
                                    Terminal(id="q", index=0, direction="output", lv_type=types[2])])
    context = VIContext(name="Mixed Divide.vi", inputs=inputs, outputs=[output], data_flow=[
        Wire.from_terminals(from_terminal_id=source, to_terminal_id=target)
        for source, target in [(inputs[0].id, "x"), (inputs[1].id, "y"), ("q", output.id)]
    ])
    graph = build_graph(context, context.name, [node])
    code = build_module(context, context.name, graph=graph)
    assert "_lv.float_divide" in code
    namespace = {}
    exec(compile(code, context.name, "exec"), namespace)
    fn = namespace["mixed_divide"]
    zero = 0 if y_type == "NumInt32" else -0.0
    sign = 1 if y_type == "NumInt32" else -1
    values = [1, -1, 0] if rank else 1
    actual = fn(values, zero).quotient
    if rank:
        assert actual[:2] == [sign * math.inf, -sign * math.inf]
        assert math.isnan(actual[2])
        assert values == [1, -1, 0]
    else:
        assert actual == sign * math.inf
        assert math.isnan(fn(0, zero).quotient)
        assert fn(2, 4).quotient == 0.5
