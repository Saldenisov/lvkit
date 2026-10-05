from __future__ import annotations
from typing import Any, NamedTuple
from lvkit.runtime import lv as _lv

class Real64DivideResult(NamedTuple):
    quotient: float

def real64_divide(numerator: float=0.0, denominator: float=0.0) -> Real64DivideResult:
    quotient = _lv.real64_divide(numerator, denominator)
    return Real64DivideResult(quotient=quotient)