"""Test agent decorator."""

import pytest
from unittest.mock import Mock, MagicMock
from agent_tracer.decorators.agent import traced_agent


class TestTracedAgent:
    """Test traced_agent decorator functionality."""

    @pytest.mark.asyncio
    async def test_basic_agent_tracing(self):
        """Test basic agent tracing without errors."""
        mock_trace_client = Mock()
        mock_trace_client.start_trace.return_value = "trace-123"

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        @traced_agent(mock_trace_client)
        class TestAgent:
            def __init__(self):
                pass

            async def run(self, task):
                return {"status": "success"}

        agent = TestAgent()
        result = await agent.run({"input": "test"})

        # Agent executed successfully
        assert result == {"status": "success"}

        # Trace was started
        mock_trace_client.start_trace.assert_called_once()
        assert mock_trace_client.start_trace.call_args[1]["trigger_type"] == "agent_task"

        # Span was created
        mock_trace_client.span.assert_called_once()

        # Trace was completed
        mock_trace_client.complete_trace.assert_called_once()
        assert mock_trace_client.complete_trace.call_args[1]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_agent_handles_errors(self):
        """Test agent decorator handles errors properly."""
        mock_trace_client = Mock()
        mock_trace_client.start_trace.return_value = "trace-123"

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        @traced_agent(mock_trace_client)
        class FailingAgent:
            def __init__(self):
                pass

            async def run(self, task):
                raise ValueError("Test error")

        agent = FailingAgent()

        # Agent should raise the error
        with pytest.raises(ValueError, match="Test error"):
            await agent.run({"input": "test"})

        # Trace was started
        mock_trace_client.start_trace.assert_called_once()

        # Trace was completed with error status
        mock_trace_client.complete_trace.assert_called_once()
        assert mock_trace_client.complete_trace.call_args[1]["status"] == "failed"
        assert "ValueError" in str(mock_trace_client.complete_trace.call_args[1]["summary"])

    @pytest.mark.asyncio
    async def test_agent_with_decision_result(self):
        """Test agent decorator extracts decisions from result."""
        mock_trace_client = Mock()
        mock_trace_client.start_trace.return_value = "trace-123"

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        class DecisionResult:
            def __init__(self):
                self.reasoning = "Test reasoning"
                self.confidence = 0.95
                self.criteria = []

        @traced_agent(mock_trace_client)
        class DecisionAgent:
            def __init__(self):
                pass

            async def run(self, task):
                return DecisionResult()

        agent = DecisionAgent()
        result = await agent.run({"input": "test"})

        # Result is correct
        assert result.reasoning == "Test reasoning"

        # Decision was extracted
        mock_trace_client.add_decision.assert_called_once()
        decision_call = mock_trace_client.add_decision.call_args[1]
        assert decision_call['name'] == "Agent Decision"
        assert decision_call['reasoning'] == "Test reasoning"
        assert decision_call['final_score'] == 0.95

    @pytest.mark.asyncio
    async def test_agent_fail_safe_mode(self):
        """Test agent decorator in fail-safe mode."""
        mock_trace_client = Mock()
        # Make start_trace fail
        mock_trace_client.start_trace.side_effect = Exception("Tracing error")

        @traced_agent(mock_trace_client, fail_safe=True)
        class RobustAgent:
            def __init__(self):
                pass

            async def run(self, task):
                return {"status": "success"}

        agent = RobustAgent()
        # Should not raise despite tracing error
        result = await agent.run({"input": "test"})

        # Agent still works
        assert result == {"status": "success"}
