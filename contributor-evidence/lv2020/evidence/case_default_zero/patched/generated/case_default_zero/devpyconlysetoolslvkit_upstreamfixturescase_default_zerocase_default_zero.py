from __future__ import annotations
from typing import Any, NamedTuple

class CaseDefaultZeroResult(NamedTuple):
    result: int

def case_default_zero(selector: int=0) -> CaseDefaultZeroResult:
    result = 0
    match selector:
        case 1:
            result = 20
        case _:
            result = 10
    return CaseDefaultZeroResult(result=result)