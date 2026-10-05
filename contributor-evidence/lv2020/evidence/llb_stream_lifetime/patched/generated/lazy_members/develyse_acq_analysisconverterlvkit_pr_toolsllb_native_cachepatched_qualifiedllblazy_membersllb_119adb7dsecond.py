from __future__ import annotations
from typing import Any, NamedTuple

class SecondResult(NamedTuple):
    result: float

def second(value: float=0.0) -> SecondResult:
    return SecondResult(result=value)