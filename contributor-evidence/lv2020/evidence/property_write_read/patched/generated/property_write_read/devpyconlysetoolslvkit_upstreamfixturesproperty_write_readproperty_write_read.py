from __future__ import annotations
from typing import Any, NamedTuple

class PropertyWriteReadResult(NamedTuple):
    result: int

def property_write_read(digital_in: Any=None, value: int=0) -> PropertyWriteReadResult:
    digital_in.value = value
    digital_in_value = digital_in.value
    return PropertyWriteReadResult(result=digital_in_value)