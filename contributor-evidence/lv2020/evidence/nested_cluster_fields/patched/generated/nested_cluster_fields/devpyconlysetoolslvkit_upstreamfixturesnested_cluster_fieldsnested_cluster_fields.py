from __future__ import annotations
from typing import Any, NamedTuple
from lvkit.runtime.positional_cluster import replace_fields

class NestedClusterFieldsResult(NamedTuple):
    cluster_out: dict[str, Any]
    original_right: float

def nested_cluster_fields(cluster_in: dict[str, Any]=None, replacement: float=0.0) -> NestedClusterFieldsResult:
    cluster = replace_fields(cluster_in, (((1, 1), replacement),))
    return NestedClusterFieldsResult(cluster_out=cluster, original_right=cluster_in[1][1])