from __future__ import annotations
from typing import Any, NamedTuple

class FirstResult(NamedTuple):
    result: float

def first(value: float=0.0) -> FirstResult:
    return FirstResult(result=value)