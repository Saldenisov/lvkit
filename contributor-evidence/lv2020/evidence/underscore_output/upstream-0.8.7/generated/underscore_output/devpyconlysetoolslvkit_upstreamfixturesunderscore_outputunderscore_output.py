from __future__ import annotations
from typing import Any, NamedTuple

class UnderscoreOutputResult(NamedTuple):
    _status: float

def underscore_output() -> UnderscoreOutputResult:
    return UnderscoreOutputResult(_status=42.0)