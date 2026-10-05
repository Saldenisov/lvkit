"""Updates of anonymous nested clusters represented as positional tuples."""

from __future__ import annotations


def replace_fields(
    cluster: tuple, updates: tuple[tuple[tuple[int, ...], object], ...]
) -> tuple:
    """Apply ordered field updates by rebuilding changed tuple branches.

    The input cluster is never mutated. Unchanged branches and leaf values
    retain their identities; this helper does not deep-copy mutable leaves.
    """
    if not isinstance(cluster, tuple):
        raise TypeError("anonymous cluster must be a tuple")
    result = cluster
    for path, value in updates:
        if not path or any(type(index) is not int or index < 0 for index in path):
            raise ValueError("nonempty nonnegative cluster index path required")
        index, *tail = path
        if index >= len(result):
            raise IndexError(path)
        if tail:
            branch = result[index]
            if not isinstance(branch, tuple):
                raise TypeError("anonymous cluster must be a tuple")
            replacement = replace_fields(branch, ((tuple(tail), value),))
        else:
            replacement = value
        result = result[:index] + (replacement,) + result[index + 1 :]
    return result
