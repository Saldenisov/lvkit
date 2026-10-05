from __future__ import annotations
from typing import Any, NamedTuple

class AnonymousClusterIdentityResult(NamedTuple):
    cluster_out: tuple

def anonymous_cluster_identity(cluster_in: tuple | None=None) -> AnonymousClusterIdentityResult:
    return AnonymousClusterIdentityResult(cluster_out=cluster_in)