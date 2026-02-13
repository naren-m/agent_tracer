"""Test fail-safe tracing wrapper."""
import pytest
from unittest.mock import Mock


def test_fail_safe_catches_trace_errors():
    """Test that trace errors don't propagate."""
    from agent_tracer.fail_safe import FailSafeTraceClient

    # Create mock client that raises errors
    mock_client = Mock()
    mock_client.start_trace.side_effect = Exception("Storage failed")

    fail_safe = FailSafeTraceClient(mock_client)

    # Should not raise
    result = fail_safe.start_trace("test", "test", {})
    assert result is None  # Failed gracefully


def test_fail_safe_stops_after_first_failure():
    """Test that subsequent calls are skipped after failure."""
    from agent_tracer.fail_safe import FailSafeTraceClient

    mock_client = Mock()
    mock_client.start_trace.side_effect = Exception("Failed")

    fail_safe = FailSafeTraceClient(mock_client)

    # First call fails
    fail_safe.start_trace("test", "test", {})

    # Second call should be skipped
    mock_client.add_decision = Mock()
    fail_safe.add_decision("test", "test", [], 1.0)

    # Should not have been called
    mock_client.add_decision.assert_not_called()


def test_fail_safe_successful_operations():
    """Test that operations work when client doesn't fail."""
    from agent_tracer.fail_safe import FailSafeTraceClient

    mock_client = Mock()
    mock_client.start_trace.return_value = "trace_123"
    mock_client.add_decision.return_value = None

    fail_safe = FailSafeTraceClient(mock_client)

    # Should work normally
    result = fail_safe.start_trace("test", "test", {})
    assert result == "trace_123"

    # Subsequent calls should also work
    fail_safe.add_decision("trace_123", "choice", ["a", "b"], 1.0)
    mock_client.add_decision.assert_called_once()


def test_fail_safe_span_context():
    """Test that span context works fail-safe."""
    from agent_tracer.fail_safe import FailSafeTraceClient

    mock_client = Mock()
    mock_span = Mock()
    mock_client.span.return_value = mock_span

    fail_safe = FailSafeTraceClient(mock_client)

    # Should return span context
    result = fail_safe.span("test", "span")
    assert result == mock_span


def test_fail_safe_span_context_on_error():
    """Test that span context returns nullcontext on error."""
    from agent_tracer.fail_safe import FailSafeTraceClient
    import contextlib

    mock_client = Mock()
    mock_client.span.side_effect = Exception("Span failed")

    fail_safe = FailSafeTraceClient(mock_client)

    # Should return nullcontext, not raise
    with fail_safe.span("test", "span"):
        pass  # Should work without error


def test_fail_safe_all_methods_covered():
    """Test that all TraceClient methods are wrapped."""
    from agent_tracer.fail_safe import FailSafeTraceClient

    mock_client = Mock()
    fail_safe = FailSafeTraceClient(mock_client)

    # Test all methods exist and are callable
    methods = ['start_trace', 'complete_trace', 'add_decision', 'add_step', 'add_artifact', 'span']
    for method in methods:
        assert hasattr(fail_safe, method)
        assert callable(getattr(fail_safe, method))
