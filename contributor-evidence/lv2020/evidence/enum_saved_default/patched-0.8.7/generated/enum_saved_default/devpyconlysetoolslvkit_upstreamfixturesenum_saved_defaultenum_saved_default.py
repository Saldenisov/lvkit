from __future__ import annotations
from typing import Any, NamedTuple

class EnumSavedDefaultResult(NamedTuple):
    result: int

def enum_saved_default(mode: int=1) -> EnumSavedDefaultResult:
    return EnumSavedDefaultResult(result=mode)