from __future__ import annotations
from typing import Any, NamedTuple

class UnderscoreOutputResult(NamedTuple):
    output_status: float

def underscore_output() -> UnderscoreOutputResult:
    return UnderscoreOutputResult(output_status=42.0)