from __future__ import annotations
from typing import Any, NamedTuple
from lvkit.runtime import lv as _lv

class Real64Log10ArrayResult(NamedTuple):
    log_values: list[float]

def real64_log10_array(values: list[float] | None=None) -> Real64Log10ArrayResult:
    values = values or []
    logx = _lv.log10(values)
    return Real64Log10ArrayResult(log_values=logx)