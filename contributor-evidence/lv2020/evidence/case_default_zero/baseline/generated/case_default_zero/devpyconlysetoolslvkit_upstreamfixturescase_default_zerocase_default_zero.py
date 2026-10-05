from __future__ import annotations
from typing import Any, NamedTuple

class CaseDefaultZeroResult(NamedTuple):
    result: int

def case_default_zero(selector: int=0) -> CaseDefaultZeroResult:
    result = 0
    match selector:
        case 0:
            result = 10
        case _:
            result = 20
    return CaseDefaultZeroResult(result=result)