from __future__ import annotations
from typing import Any, NamedTuple
from lvkit.runtime import lv as _lv

class ArrayAddLiteralResult(NamedTuple):
    result: list[float]

def array_add_literal(bank: list[float] | None=None) -> ArrayAddLiteralResult:
    bank = bank or []
    sum_ = _lv.add([0.0, _lv.neg(2.0), _lv.neg(2.0)], bank)
    return ArrayAddLiteralResult(result=sum_)