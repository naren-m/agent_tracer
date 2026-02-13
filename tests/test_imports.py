"""Test that all public API items can be imported."""

import pytest


def test_import_decorators():
    """Test importing decorator functions."""
    from agent_tracer import agent, traced_llm_call, traced_anthropic, traced_openai, traced_decision, traced

    assert agent is not None
    assert traced_llm_call is not None
    assert traced_anthropic is not None
    assert traced_openai is not None
    assert traced_decision is not None
    assert traced is not None
    assert callable(agent)
    assert callable(traced_llm_call)
    assert callable(traced_anthropic)
    assert callable(traced_openai)
    assert callable(traced_decision)
    assert callable(traced)


def test_import_models():
    """Test importing data models."""
    from agent_tracer import AgentDecision, DecisionCriteria, Alternative

    assert AgentDecision is not None
    assert DecisionCriteria is not None
    assert Alternative is not None


def test_import_utilities():
    """Test importing utility classes."""
    from agent_tracer import FailSafeTraceClient

    assert FailSafeTraceClient is not None


def test_import_context_functions():
    """Test importing context management functions."""
    from agent_tracer import (
        set_current_trace_id,
        get_current_trace_id,
        get_span_stack,
        capture_context,
    )

    assert set_current_trace_id is not None
    assert get_current_trace_id is not None
    assert get_span_stack is not None
    assert capture_context is not None
    assert callable(set_current_trace_id)
    assert callable(get_current_trace_id)
    assert callable(get_span_stack)
    assert callable(capture_context)


def test_import_core():
    """Test importing core components."""
    from agent_tracer import TraceClient, Trace, Span, Step, Artifact

    assert TraceClient is not None
    assert Trace is not None
    assert Span is not None
    assert Step is not None
    assert Artifact is not None


def test_version_info():
    """Test that version information is available."""
    import agent_tracer

    assert hasattr(agent_tracer, "__version__")
    assert isinstance(agent_tracer.__version__, str)
    assert agent_tracer.__version__ == "0.2.0"


def test_import_from_package():
    """Test importing everything from package root."""
    from agent_tracer import (
        TraceClient,
        Trace,
        Span,
        Step,
        Artifact,
        agent,
        traced_llm_call,
        traced_anthropic,
        traced_openai,
        traced_decision,
        traced,
        AgentDecision,
        DecisionCriteria,
        Alternative,
        set_current_trace_id,
        get_current_trace_id,
        get_span_stack,
        capture_context,
        FailSafeTraceClient,
    )

    items = [
        TraceClient,
        Trace,
        Span,
        Step,
        Artifact,
        agent,
        traced_llm_call,
        traced_anthropic,
        traced_openai,
        traced_decision,
        traced,
        AgentDecision,
        DecisionCriteria,
        Alternative,
        set_current_trace_id,
        get_current_trace_id,
        get_span_stack,
        capture_context,
        FailSafeTraceClient,
    ]

    for item in items:
        assert item is not None
