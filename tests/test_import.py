"""Basic import tests for agent_tracer package."""

import pytest


def test_package_import():
    """Test that the agent_tracer package can be imported."""
    import agent_tracer
    assert agent_tracer is not None
    assert hasattr(agent_tracer, '__version__')


def test_version():
    """Test that version is defined and valid."""
    import agent_tracer
    assert agent_tracer.__version__ == "0.1.0"


def test_core_imports():
    """Test that core modules can be imported."""
    from agent_tracer import (
        Trace,
        Span,
        Step,
        Artifact,
        TriggerInfo,
        TraceSummary,
        StorageInfo,
        AgentMetadata,
        TraceClient,
    )

    # Verify all classes are importable
    assert Trace is not None
    assert Span is not None
    assert Step is not None
    assert Artifact is not None
    assert TriggerInfo is not None
    assert TraceSummary is not None
    assert StorageInfo is not None
    assert AgentMetadata is not None
    assert TraceClient is not None


def test_storage_imports():
    """Test that storage backend can be imported."""
    from agent_tracer import TraceStorageBackend, TraceNotFoundError

    assert TraceStorageBackend is not None
    assert TraceNotFoundError is not None


def test_trace_client_class():
    """Test that TraceClient class is properly defined."""
    from agent_tracer import TraceClient

    # Verify TraceClient is a class
    assert TraceClient is not None
    assert callable(TraceClient)

    # Verify it has expected methods
    assert hasattr(TraceClient, 'start_trace')
    assert hasattr(TraceClient, 'complete_trace')
    assert hasattr(TraceClient, 'span')
    assert hasattr(TraceClient, 'add_step')
    assert hasattr(TraceClient, 'add_artifact')
