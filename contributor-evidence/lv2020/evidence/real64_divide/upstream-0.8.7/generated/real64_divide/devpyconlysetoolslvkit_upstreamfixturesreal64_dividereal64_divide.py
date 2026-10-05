from __future__ import annotations
from typing import Any, NamedTuple

class Real64DivideResult(NamedTuple):
    quotient: float

def real64_divide(numerator: float=0.0, denominator: float=0.0) -> Real64DivideResult:
    return Real64DivideResult(quotient=numerator / denominator)