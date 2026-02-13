"""Test fail-safe trace client wrapper."""

import pytest
from unittest.mock import Mock, MagicMock
from agent_tracer.utils.fail_safe import FailSafeTraceClient


class TestFailSafeTraceClient:
    """Test FailSafeTraceClient functionality."""

    def test_suppresses_errors(self):
        """Test that fail-safe wrapper suppresses tracing errors."""
        mock_client = Mock()
        mock_client.start_trace.side_effect = Exception("Tracing error")

        wrapper = FailSafeTraceClient(mock_client)

        # Should not raise
        result = wrapper.start_trace("test_trigger")

        # Should return None on error
        assert result is None

        # Should mark as failed
        assert wrapper._failed is True

    def test_returns_on_success(self):
        """Test that fail-safe wrapper returns results on success."""
        mock_client = Mock()
        mock_client.start_trace.return_value = "trace-123"

        wrapper = FailSafeTraceClient(mock_client)

        result = wrapper.start_trace("test_trigger")

        # Should return actual result
        assert result == "trace-123"

        # Should not mark as failed
        assert wrapper._failed is False

    def test_skip_after_failure(self):
        """Test that subsequent calls are skipped after failure."""
        mock_client = Mock()
        mock_client.start_trace.side_effect = Exception("Tracing error")

        wrapper = FailSafeTraceClient(mock_client)

        # First call triggers error
        wrapper.start_trace("test_trigger")

        # Reset mock to ensure it's not called again
        mock_client.reset_mock()

        # Second call should be skipped
        result = wrapper.add_step("test_step")
        assert result is None
        mock_client.add_step.assert_not_called()

    def test_all_methods_wrapped(self):
        """Test that all TraceClient methods are wrapped."""
        mock_client = Mock()

        wrapper = FailSafeTraceClient(mock_client)

        # Test each method
        wrapper.start_trace("trigger")
        mock_client.start_trace.assert_called_once()

        wrapper.complete_trace("status", {})
        mock_client.complete_trace.assert_called_once()

        wrapper.add_decision("name", "reasoning")
        mock_client.add_decision.assert_called_once()

        wrapper.add_step("name", "type")
        mock_client.add_step.assert_called_once()

        wrapper.add_artifact("name", "type", "data")
        mock_client.add_artifact.assert_called_once()

    def test_span_context_manager(self):
        """Test that span returns nullcontext on error."""
        mock_client = Mock()

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_client.span.return_value = span_mock

        wrapper = FailSafeTraceClient(mock_client)

        # Should return actual span on success
        with wrapper.span("test_span", "type") as span:
            assert span is None  # The __enter__ returns None

        # Now make it fail
        mock_client.span.side_effect = Exception("Span error")

        # Should return nullcontext on error (doesn't raise)
        with wrapper.span("test_span", "type") as span:
            pass  # Should not raise

    def test_custom_logger(self):
        """Test that custom logger is used."""
        mock_client = Mock()
        mock_client.start_trace.side_effect = Exception("Tracing error")

        mock_logger = Mock()
        wrapper = FailSafeTraceClient(mock_client, logger=mock_logger)

        wrapper.start_trace("trigger")

        # Should log warning
        mock_logger.warning.assert_called_once()
        assert "start_trace" in str(mock_logger.warning.call_args)
