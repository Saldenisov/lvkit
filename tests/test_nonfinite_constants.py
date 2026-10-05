"""Generated scalar numeric constants must execute without injected names."""

from __future__ import annotations

import math

import pytest

from lvkit.codegen.context import _decode_numeric_constant, _format_constant
from lvkit.graph.models import Constant
from lvkit.models import LVType, LVTypeKind


def assert_number(expression, expected):
    actual = eval(expression, {"__builtins__": {"float": float}})
    if math.isnan(expected):
        assert math.isnan(actual)
    else:
        assert actual == expected
        assert math.copysign(1.0, actual) == math.copysign(1.0, expected)


@pytest.mark.parametrize("underlying", ["NumFloat32", "NumFloat64"])
@pytest.mark.parametrize(
    "value,expected",
    [
        ("NaN", math.nan),
        ("inf", math.inf),
        ("-inf", -math.inf),
        ("-0.0", -0.0),
        ("2.5", 2.5),
    ],
)
def test_decimal_float_expression_executes(value, expected, underlying):
    assert_number(_decode_numeric_constant(value, underlying), expected)


@pytest.mark.parametrize(
    "underlying,value,expected",
    [
        ("NumFloat64", "7FF8000000000000", math.nan),
        ("NumFloat64", "7FF0000000000000", math.inf),
        ("NumFloat64", "FFF0000000000000", -math.inf),
        ("NumFloat32", "7FC00000", math.nan),
        ("NumFloat32", "7F800000", math.inf),
        ("NumFloat32", "FF800000", -math.inf),
    ],
)
def test_hex_nonfinite_expression_executes(underlying, value, expected):
    assert_number(_decode_numeric_constant(value, underlying), expected)


@pytest.mark.parametrize("underlying", [None, "NumFloat32", "NumFloat64"])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, -0.0, 2.5])
def test_decoded_float_expression_executes(underlying, value):
    lv_type = LVType(kind=LVTypeKind.PRIMITIVE, underlying_type=underlying)
    assert_number(
        _format_constant(Constant(id="constant", value=value, lv_type=lv_type)), value
    )


@pytest.mark.parametrize(
    "value,expected", [("nan", math.nan), ("inf", math.inf), ("-inf", -math.inf)]
)
def test_untyped_numeric_text_executes(value, expected):
    assert_number(_format_constant(Constant(id="constant", value=value)), expected)


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_string_constants_remain_text(value):
    lv_type = LVType(kind=LVTypeKind.PRIMITIVE, underlying_type="String")
    expression = _format_constant(Constant(id="constant", value=value, lv_type=lv_type))
    assert eval(expression, {"__builtins__": {}}) == value
