"""Test tool decorator."""

import pytest
from unittest.mock import Mock, MagicMock
from agent_tracer.decorators.tool import traced_tool


class TestTracedTool:
    """Test traced_tool decorator functionality."""

    @pytest.mark.asyncio
    async def test_basic_tool_tracing(self):
        """Test basic tool tracing."""
        mock_trace_client = Mock()

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        @traced_tool(mock_trace_client)
        async def search_web(query):
            return {"results": [query]}

        result = await search_web("test query")

        # Tool executed correctly
        assert result == {"results": ["test query"]}

        # Span was created
        mock_trace_client.span.assert_called_once()
        assert "Tool: search_web" in str(mock_trace_client.span.call_args)

        # Step was logged
        mock_trace_client.add_step.assert_called_once()
        step_call = mock_trace_client.add_step.call_args[1]
        assert step_call['name'] == 'search_web'
        assert step_call['step_type'] == 'tool_execution'

    @pytest.mark.asyncio
    async def test_tool_logs_input_output(self):
        """Test tool decorator logs input and output data."""
        mock_trace_client = Mock()

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        @traced_tool(mock_trace_client)
        async def calculator(operation, a, b):
            if operation == "add":
                return a + b
            return 0

        result = await calculator("add", 5, 3)

        # Tool executed correctly
        assert result == 8

        # Step was logged with input/output
        mock_trace_client.add_step.assert_called_once()
        step_call = mock_trace_client.add_step.call_args[1]
        assert 'input_data' in step_call
        assert 'output_data' in step_call
        assert step_call['output_data']['result'] == 8
