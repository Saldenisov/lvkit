from __future__ import annotations
from typing import Any, NamedTuple

class NestedClusterFieldsResult(NamedTuple):
    cluster_out: dict[str, Any]
    original_right: float

def nested_cluster_fields(cluster_in: dict[str, Any]=None, replacement: float=0.0) -> NestedClusterFieldsResult:
    cluster_in.right = replacement
    return NestedClusterFieldsResult(cluster_out=cluster_in, original_right=cluster_in[3])