"""Tests for LangChain callback handler integration."""

import pytest
from unittest.mock import MagicMock, patch
from integrations.langchain import ComprehensiveTracingCallback
from models.decision_models import AgentDecision
from context.context_propagation import get_current_trace_id, get_span_stack


@pytest.fixture
def callback():
    """Create a callback instance for testing."""
    mock_trace_client = MagicMock()
    # Create a mock span context manager
    mock_span = MagicMock()
    mock_span.__enter__ = MagicMock(return_value=mock_span)
    mock_span.__exit__ = MagicMock(return_value=None)
    mock_trace_client.span.return_value = mock_span

    # Disable fail-safe wrapping for testing
    return ComprehensiveTracingCallback(trace_client=mock_trace_client, fail_safe=False)


@pytest.fixture
def mock_trace_context():
    """Mock trace context setup."""
    with patch("integrations.langchain.set_current_trace_id") as mock_set_trace:
        yield {
            "set_trace": mock_set_trace,
        }


def test_callback_traces_chain_start(callback, mock_trace_context):
    """Test that on_chain_start captures node execution."""
    serialized = {"name": "research_node"}
    inputs = {"query": "analyze data"}
    run_id = "test-run-123"

    callback.on_chain_start(
        serialized=serialized,
        inputs=inputs,
        run_id=run_id
    )

    # Verify trace ID was set (since no existing trace)
    mock_trace_context["set_trace"].assert_called_once()

    # Verify trace_client methods were called
    assert callback.trace_client.start_trace.called
    assert callback.trace_client.span.called

    # Verify span was created with correct parameters
    span_call = callback.trace_client.span.call_args
    assert span_call[0][0] == "research_node"  # span name
    assert span_call[0][1] == "node"  # span type


def test_callback_traces_llm_start(callback, mock_trace_context):
    """Test that on_llm_start captures LLM context."""
    serialized = {"name": "ChatOpenAI"}
    prompts = ["Analyze this data and make a decision"]
    run_id = "test-llm-456"

    callback.on_llm_start(
        serialized=serialized,
        prompts=prompts,
        run_id=run_id
    )

    # Verify LLM span was created
    assert callback.trace_client.span.called
    span_call = callback.trace_client.span.call_args
    assert span_call[0][0] == "ChatOpenAI"  # span name
    assert span_call[0][1] == "llm"  # span type


def test_callback_traces_llm_end_with_decision(callback, mock_trace_context):
    """Test that on_llm_end parses response to AgentDecision."""
    # First, start an LLM call to create a span
    run_id = "test-llm-789"
    callback.on_llm_start(
        serialized={"name": "ChatOpenAI"},
        prompts=["test prompt"],
        run_id=run_id
    )

    # Mock LLM response with decision-like content
    response = MagicMock()
    response.generations = [
        [MagicMock(text="I will approve the deployment because tests passed. High confidence.")]
    ]

    callback.on_llm_end(
        response=response,
        run_id=run_id
    )

    # Verify span was created
    assert callback.trace_client.span.called

    # Verify artifacts were added (decision data)
    assert callback.trace_client.add_artifact.called


def test_callback_handles_errors_gracefully():
    """Test that callback errors don't crash the agent."""
    # Create a callback with fail-safe enabled and a mock that raises errors
    mock_trace_client = MagicMock()
    mock_trace_client.span.side_effect = Exception("Test error")

    # Create callback with fail-safe enabled
    callback = ComprehensiveTracingCallback(trace_client=mock_trace_client, fail_safe=True)

    # Should not raise because callback has fail-safe error handling
    callback.on_chain_start(
        serialized={"name": "test"},
        inputs={},
        run_id="test-123"
    )


def test_callback_manages_span_stack(callback, mock_trace_context):
    """Test that callback properly manages nested spans."""
    # Start chain (outer span)
    callback.on_chain_start(
        serialized={"name": "workflow"},
        inputs={},
        run_id="run-1"
    )

    # Start LLM (inner span)
    callback.on_llm_start(
        serialized={"name": "ChatOpenAI"},
        prompts=["test"],
        run_id="run-2"
    )

    # Verify both spans were created
    assert callback.trace_client.span.call_count == 2

    # End LLM (exit inner span)
    response = MagicMock()
    response.generations = [[MagicMock(text="result")]]
    callback.on_llm_end(response=response, run_id="run-2")

    # End chain (exit outer span)
    callback.on_chain_end(outputs={}, run_id="run-1")

    # Verify both run_ids were tracked and cleaned up
    assert len(callback._run_id_to_span) == 0  # All spans should be cleaned up


def test_parse_decision_from_text():
    """Test decision parsing logic."""
    from integrations.langchain import _parse_decision_from_text

    text = "I will approve the deployment because all tests passed. I'm very confident in this decision."
    decision = _parse_decision_from_text(text)

    assert isinstance(decision, AgentDecision)
    assert "approve" in decision.action.lower()
    assert decision.confidence > 0.5
    assert len(decision.reasoning) > 0


def test_parse_decision_handles_low_confidence():
    """Test parsing of uncertain decisions."""
    from integrations.langchain import _parse_decision_from_text

    text = "I might consider rejecting this. Maybe not sure."
    decision = _parse_decision_from_text(text)

    assert decision.confidence < 0.7  # Lower confidence


def test_parse_decision_handles_unparseable_text():
    """Test fallback for unparseable text."""
    from integrations.langchain import _parse_decision_from_text

    text = "Random text without clear structure"
    decision = _parse_decision_from_text(text)

    # Should still create valid AgentDecision with defaults
    assert isinstance(decision, AgentDecision)
    assert decision.action == "unknown"
