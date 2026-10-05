from __future__ import annotations
from typing import Any, NamedTuple

class NonfiniteConstantsResult(NamedTuple):
    nan_result: float
    positive_inf: float
    negative_inf: float

def nonfinite_constants() -> NonfiniteConstantsResult:
    return NonfiniteConstantsResult(nan_result=nan, positive_inf=inf, negative_inf=-inf)