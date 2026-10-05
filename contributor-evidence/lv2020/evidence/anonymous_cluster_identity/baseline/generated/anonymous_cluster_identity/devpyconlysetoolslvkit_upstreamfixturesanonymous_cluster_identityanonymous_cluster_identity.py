from __future__ import annotations
from typing import Any, NamedTuple

class AnonymousClusterIdentityResult(NamedTuple):
    cluster_out: dict[str, Any]

def anonymous_cluster_identity(cluster_in: dict[str, Any]=None) -> AnonymousClusterIdentityResult:
    return AnonymousClusterIdentityResult(cluster_out=cluster_in)