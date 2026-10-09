"""Synthetic non-DBL array inputs execute through generated log10 modules."""

import math

import pytest

from tests.test_log10 import assert_numeric, fingerprint, generated_log10


@pytest.mark.parametrize("input_type", ["NumFloat32", "NumFloatExt", "NumInt32"])
@pytest.mark.parametrize("rank", [1, 2])
def test_other_real_array_types(input_type, rank):
    values = [1, 10, 100, 0, -1]
    expected = [0.0, 1.0, 2.0, -math.inf, math.nan]
    if rank == 2:
        values, expected = [values, []], [expected, []]
    before = fingerprint(values)
    result = generated_log10(rank, input_type=input_type)(values).log_values
    assert_numeric(result, expected)
    assert fingerprint(values) == before
