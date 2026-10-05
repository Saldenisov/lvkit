"""Strict JSON encodings for numeric oracle comparisons."""

from __future__ import annotations

import math


def encode(value):
    if isinstance(value, float):
        if math.isnan(value):
            return {"float": "nan"}
        if math.isinf(value):
            return {"float": "-inf" if value < 0 else "inf"}
        if value == 0.0 and math.copysign(1.0, value) < 0:
            return {"float": "-0.0"}
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    return value


def decode(value):
    if isinstance(value, dict) and set(value) == {"float"}:
        return float(value["float"])
    if isinstance(value, list):
        return [decode(item) for item in value]
    return value
