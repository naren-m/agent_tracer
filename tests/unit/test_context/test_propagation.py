"""Tests for context propagation module."""

import pytest
from contextvars import copy_context
from agent_tracer.context.propagation import (
    get_current_trace_id,
    set_current_trace_id,
)


def test_set_and_get_trace_id():
    """Test setting and getting trace ID."""
    # Run in isolated context
    ctx = copy_context()

    def run_test():
        trace_id = "test-trace-123"
        set_current_trace_id(trace_id)
        result = get_current_trace_id()
        assert result == trace_id

    ctx.run(run_test)


def test_get_trace_id_none_when_not_set():
    """Test get returns None when trace ID is not set."""
    # Run in isolated context
    ctx = copy_context()

    def run_test():
        result = get_current_trace_id()
        assert result is None

    ctx.run(run_test)
