from __future__ import annotations
from typing import Any, NamedTuple
from lvkit.runtime import lv as _lv

class ExpandedIndexArrayResult(NamedTuple):
    first: float
    second: float
    third: float

def expanded_index_array(values: list[float] | None=None, start: int=0) -> ExpandedIndexArrayResult:
    values = values or []
    element_0, out_3, out_5 = _lv.index_array(values, start, 0.0)
    return ExpandedIndexArrayResult(first=element_0, second=out_3, third=out_5)