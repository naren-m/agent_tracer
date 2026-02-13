"""Test function decorator."""

import pytest
from unittest.mock import Mock, MagicMock
from agent_tracer.decorators.function import traced_function


class TestTracedFunction:
    """Test traced_function decorator functionality."""

    @pytest.mark.asyncio
    async def test_basic_function_tracing(self):
        """Test basic function tracing."""
        mock_trace_client = Mock()

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        @traced_function(mock_trace_client)
        async def my_function(x, y):
            return x + y

        result = await my_function(2, 3)

        # Function executed correctly
        assert result == 5

        # Span was created
        mock_trace_client.span.assert_called_once()
        assert "Function: my_function" in str(mock_trace_client.span.call_args)

    @pytest.mark.asyncio
    async def test_custom_span_name(self):
        """Test function tracing with custom span name."""
        mock_trace_client = Mock()

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        @traced_function(mock_trace_client, span_name="Custom Operation")
        async def my_function(x):
            return x * 2

        result = await my_function(5)

        # Function executed correctly
        assert result == 10

        # Span was created with custom name
        mock_trace_client.span.assert_called_once()
        assert "Custom Operation" in str(mock_trace_client.span.call_args)
