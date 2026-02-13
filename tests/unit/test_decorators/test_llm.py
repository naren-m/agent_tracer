"""Test LLM call decorator."""

import pytest
from unittest.mock import Mock, MagicMock
from agent_tracer.decorators.llm import traced_llm_call
from agent_tracer.context.capture import LLMContextCaptureMixin


class AgentDecision:
    """Mock AgentDecision class for testing."""

    def __init__(self, reasoning, confidence=1.0, criteria=None, alternatives=None):
        self.reasoning = reasoning
        self.confidence = confidence
        self.criteria = criteria or []
        self.alternatives = alternatives or []


class DecisionCriterion:
    """Mock decision criterion."""

    def __init__(self, factor, score, weight):
        self.factor = factor
        self.score = score
        self.weight = weight


class TestTracedLLMCall:
    """Test traced_llm_call decorator functionality."""

    @pytest.mark.asyncio
    async def test_captures_context_and_extracts_decision(self):
        """Test LLM decorator captures context before call and extracts decision after."""
        mock_trace_client = Mock()

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        class TestAgent(LLMContextCaptureMixin):
            @traced_llm_call(mock_trace_client)
            async def call_llm(self, prompt):
                return AgentDecision(
                    reasoning="Test reasoning",
                    confidence=0.95,
                    criteria=[
                        DecisionCriterion("relevance", 0.9, 0.5),
                        DecisionCriterion("accuracy", 0.85, 0.5)
                    ]
                )

        agent = TestAgent()
        result = await agent.call_llm("test prompt")

        # Result is returned correctly
        assert result.reasoning == "Test reasoning"
        assert result.confidence == 0.95

        # Context was captured (artifact added before call)
        assert mock_trace_client.add_artifact.call_count >= 1
        context_call = mock_trace_client.add_artifact.call_args_list[0]
        assert context_call[0][0] == "LLM Context"
        assert context_call[0][1] == "context"

        # Decision was extracted (add_decision called after call)
        mock_trace_client.add_decision.assert_called_once()
        decision_call = mock_trace_client.add_decision.call_args[1]
        assert decision_call['name'] == "LLM Decision: call_llm"
        assert decision_call['reasoning'] == "Test reasoning"
        assert decision_call['final_score'] == 0.95
        assert len(decision_call['criteria']) == 2

    @pytest.mark.asyncio
    async def test_logs_alternatives(self):
        """Test LLM decorator logs alternatives if available."""
        mock_trace_client = Mock()

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        class TestAgent(LLMContextCaptureMixin):
            @traced_llm_call(mock_trace_client)
            async def call_llm(self, prompt):
                return AgentDecision(
                    reasoning="Primary choice",
                    alternatives=["Alternative 1", "Alternative 2"]
                )

        agent = TestAgent()
        await agent.call_llm("test prompt")

        # Alternatives were logged (should have 2 artifacts: context + alternatives)
        assert mock_trace_client.add_artifact.call_count == 2
        alternatives_call = mock_trace_client.add_artifact.call_args_list[1]
        assert alternatives_call[0][0] == "Decision Alternatives"
        assert alternatives_call[0][1] == "alternatives"

    @pytest.mark.asyncio
    async def test_works_without_context_mixin(self):
        """Test LLM decorator works without LLMContextCaptureMixin."""
        mock_trace_client = Mock()

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        class BasicAgent:
            @traced_llm_call(mock_trace_client, fail_safe=False)
            async def call_llm(self, prompt):
                return AgentDecision(reasoning="Test")

        agent = BasicAgent()
        result = await agent.call_llm("test prompt")

        # Still works
        assert result.reasoning == "Test"

        # Decision was extracted
        mock_trace_client.add_decision.assert_called_once()

        # No context artifact (agent doesn't have mixin)
        # Fail-safe wrapper may add artifact, so check it's not called with context
        if mock_trace_client.add_artifact.called:
            # Should not be LLM Context
            for call in mock_trace_client.add_artifact.call_args_list:
                assert call[0][0] != "LLM Context"

    @pytest.mark.asyncio
    async def test_fail_safe_mode(self):
        """Test LLM decorator doesn't break on tracing errors."""
        mock_trace_client = Mock()
        mock_trace_client.add_artifact.side_effect = Exception("Tracing error")

        # Create proper context manager mock
        span_mock = MagicMock()
        span_mock.__enter__ = MagicMock(return_value=None)
        span_mock.__exit__ = MagicMock(return_value=False)
        mock_trace_client.span.return_value = span_mock

        class TestAgent(LLMContextCaptureMixin):
            @traced_llm_call(mock_trace_client, fail_safe=True)
            async def call_llm(self, prompt):
                return AgentDecision(reasoning="Test")

        agent = TestAgent()
        result = await agent.call_llm("test prompt")

        # LLM call still succeeds despite tracing errors
        assert result.reasoning == "Test"
