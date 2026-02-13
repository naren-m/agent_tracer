"""Test that all public API items can be imported from agent_tracer v0.2.0."""

import pytest


def test_import_decorators():
    """Test importing decorator functions."""
    from agent_tracer import traced_agent, traced_llm_call, traced_function, traced_tool

    assert traced_agent is not None
    assert traced_llm_call is not None
    assert traced_function is not None
    assert traced_tool is not None
    assert callable(traced_agent)
    assert callable(traced_llm_call)
    assert callable(traced_function)
    assert callable(traced_tool)


def test_import_models():
    """Test importing data models."""
    from agent_tracer import AgentDecision, DecisionCriteria, LLMContext

    assert AgentDecision is not None
    assert DecisionCriteria is not None
    assert LLMContext is not None


def test_import_utilities():
    """Test importing utility classes."""
    from agent_tracer import FailSafeTraceClient

    assert FailSafeTraceClient is not None


def test_import_context_functions():
    """Test importing context management functions."""
    from agent_tracer import (
        LLMContextCaptureMixin,
        set_current_trace_id,
        get_current_trace_id,
        get_span_stack,
    )

    assert LLMContextCaptureMixin is not None
    assert set_current_trace_id is not None
    assert get_current_trace_id is not None
    assert get_span_stack is not None
    assert callable(set_current_trace_id)
    assert callable(get_current_trace_id)
    assert callable(get_span_stack)


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


def test_import_all_public_api():
    """Test importing everything from package root."""
    from agent_tracer import (
        # Core (v0.1.0)
        TraceClient,
        Trace,
        Span,
        Step,
        Artifact,
        # Decorators (v0.2.0)
        traced_agent,
        traced_llm_call,
        traced_function,
        traced_tool,
        # Models (v0.2.0)
        AgentDecision,
        DecisionCriteria,
        LLMContext,
        # Context (v0.2.0)
        LLMContextCaptureMixin,
        set_current_trace_id,
        get_current_trace_id,
        get_span_stack,
        # Utilities (v0.2.0)
        FailSafeTraceClient,
    )

    items = [
        TraceClient, Trace, Span, Step, Artifact,
        traced_agent, traced_llm_call, traced_function, traced_tool,
        AgentDecision, DecisionCriteria, LLMContext,
        LLMContextCaptureMixin,
        set_current_trace_id, get_current_trace_id, get_span_stack,
        FailSafeTraceClient,
    ]

    for item in items:
        assert item is not None


def test_submodule_imports():
    """Test importing from submodules directly."""
    from agent_tracer.decorators import traced_agent, traced_llm_call
    from agent_tracer.models import AgentDecision, DecisionCriteria, LLMContext
    from agent_tracer.context import LLMContextCaptureMixin, get_current_trace_id
    from agent_tracer.utils import FailSafeTraceClient
    from agent_tracer.core.trace_client import TraceClient
    from agent_tracer.core.schemas import Trace, Span

    assert traced_agent is not None
    assert AgentDecision is not None
    assert LLMContextCaptureMixin is not None
    assert FailSafeTraceClient is not None
    assert TraceClient is not None
    assert Trace is not None
