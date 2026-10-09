"""Execute wired-error Property Nodes and verify Python exception propagation.

Synthetic reference adapter only; no driver or native error-path claim.
"""

import pytest

from tests.test_property_terminal_order import connect, execute, fixture


@pytest.mark.parametrize("ports", [("error_in",), ("error_out",), ("error_in", "error_out")])
def test_wired_errors_preserve_accesses_and_python_exceptions(ports):
    for reverse in (False, True):
        node, ctx, namespace = fixture([("Value", "input"), ("Value", "output")], reverse=reverse)
        for port in ports:
            direction = "input" if port == "error_in" else "output"
            connect(ctx, port, direction)
        ctx.bind("peer_error_in", "incoming_error")
        namespace["incoming_error"] = (False, 0, "")
        assert execute(node, ctx, namespace) == {"row_1": 1000}
        assert namespace["ref"].events == [("write", "value", 1000), ("read", "value", 1000)]

        class FailingReference:
            def __setattr__(self, name, value):
                raise RuntimeError("fixture property write failed")

        node, ctx, namespace = fixture([("Value", "input"), ("Value", "output")], reverse=reverse)
        for port in ports:
            connect(ctx, port, "input" if port == "error_in" else "output")
        ctx.bind("peer_error_in", "incoming_error")
        namespace["incoming_error"] = (False, 0, "")
        namespace["ref"] = FailingReference()
        with pytest.raises(RuntimeError, match="fixture property write failed"):
            execute(node, ctx, namespace)
