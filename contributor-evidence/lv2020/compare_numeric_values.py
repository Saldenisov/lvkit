"""Compare strict JSON numeric values with explicit finite tolerances."""

from __future__ import annotations

import math

from numeric_values import decode


def matches(actual, expected, *, rel_tol=1e-14, abs_tol=1e-14):
    actual, expected = decode(actual), decode(expected)
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(
                matches(a, e, rel_tol=rel_tol, abs_tol=abs_tol)
                for a, e in zip(actual, expected)
            )
        )
    if not isinstance(actual, (int, float)):
        return False
    if math.isnan(expected):
        return math.isnan(actual)
    if math.isinf(expected):
        return actual == expected
    if expected == 0.0:
        return actual == 0.0 and math.copysign(1.0, actual) == math.copysign(
            1.0, expected
        )
    return math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol)
