from __future__ import annotations
from typing import Any, NamedTuple
from lvkit.runtime import lv as _lv

class ExpandedIndexArrayResult(NamedTuple):
    first: float
    second: float
    third: float

def expanded_index_array(values: list[float] | None=None, start: int=0) -> ExpandedIndexArrayResult:
    values = values or []
    indexed_array = values
    array_index_0 = start
    element_0 = _lv.index_array(indexed_array, array_index_0, 0.0)
    array_index_1 = array_index_0 + 1
    element_1 = _lv.index_array(indexed_array, array_index_1, 0.0)
    array_index_2 = array_index_1 + 1
    element_2 = _lv.index_array(indexed_array, array_index_2, 0.0)
    return ExpandedIndexArrayResult(first=element_0, second=element_1, third=element_2)