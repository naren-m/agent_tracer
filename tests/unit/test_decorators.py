"""Test tracing decorators."""

import pytest
from unittest.mock import Mock, AsyncMock


@pytest.mark.asyncio
async def test_traced_agent_decorator_wraps_run_method():
    """Test decorator wraps agent run method with tracing."""
    from unittest.mock import MagicMock
    from agent_tracer.decorators import traced_agent

    mock_trace_client = Mock()
    mock_trace_client.start_trace.return_value = "trace_123"

    # Create proper context manager mock
    span_mock = MagicMock()
    span_mock.__enter__ = MagicMock(return_value=None)
    span_mock.__exit__ = MagicMock(return_value=False)
    mock_trace_client.span.return_value = span_mock

    @traced_agent(mock_trace_client)
    class TestAgent:
        async def run(self, task):
            return {"result": "success"}

    agent = TestAgent()
    result = await agent.run({"task": "test"})

    # Agent still works
    assert result == {"result": "success"}

    # Trace was created
    mock_trace_client.start_trace.assert_called_once()
    mock_trace_client.complete_trace.assert_called_once()


@pytest.mark.asyncio
async def test_traced_agent_handles_errors():
    """Test decorator traces errors properly."""
    from unittest.mock import MagicMock
    from agent_tracer.decorators import traced_agent

    mock_trace_client = Mock()
    mock_trace_client.start_trace.return_value = "trace_123"

    # Create proper context manager mock
    span_mock = MagicMock()
    span_mock.__enter__ = MagicMock(return_value=None)
    span_mock.__exit__ = MagicMock(return_value=False)  # Don't swallow exceptions
    mock_trace_client.span.return_value = span_mock

    @traced_agent(mock_trace_client)
    class TestAgent:
        async def run(self, task):
            raise ValueError("Test error")

    agent = TestAgent()

    with pytest.raises(ValueError):
        await agent.run({"task": "test"})

    # Error was traced
    mock_trace_client.complete_trace.assert_called_once()
    call_kwargs = mock_trace_client.complete_trace.call_args[1]
    assert call_kwargs.get('status') == 'failed'


@pytest.mark.asyncio
async def test_traced_agent_injects_callbacks_for_langgraph():
    """Test that @traced_agent auto-injects tracing callbacks for LangGraph agents."""
    from unittest.mock import MagicMock
    from agent_tracer.decorators import traced_agent

    trace_client = Mock()
    trace_client.start_trace.return_value = "trace_123"

    # Create proper context manager mock
    span_mock = MagicMock()
    span_mock.__enter__ = MagicMock(return_value=None)
    span_mock.__exit__ = MagicMock(return_value=False)
    trace_client.span.return_value = span_mock

    @traced_agent(trace_client)
    class TestLangGraphAgent:
        def __init__(self):
            self.callbacks = []  # LangGraph agents have this

        async def run(self, input_data):
            # Check that callback was injected
            return {"callbacks_count": len(self.callbacks)}

    agent = TestLangGraphAgent()

    # Callback should be auto-injected
    assert len(agent.callbacks) == 1
    assert hasattr(agent.callbacks[0], 'on_chain_start')
