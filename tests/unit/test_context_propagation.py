"""Test async context propagation using contextvars."""

import asyncio
import pytest


def test_trace_context_propagates_across_async_calls():
    """Test trace_id propagates through async call chains."""
    from agent_tracer.context_propagation import (
        set_current_trace_id,
        get_current_trace_id,
    )

    async def outer_async_function():
        """Outer async function that sets trace ID."""
        set_current_trace_id("trace-123")
        result = await inner_async_function()
        return result

    async def inner_async_function():
        """Inner async function that reads trace ID."""
        return get_current_trace_id()

    # Run async code and verify trace ID propagated
    trace_id = asyncio.run(outer_async_function())
    assert trace_id == "trace-123"


def test_trace_context_isolated_across_concurrent_tasks():
    """Test trace contexts are isolated between concurrent async tasks."""
    from agent_tracer.context_propagation import (
        set_current_trace_id,
        get_current_trace_id,
    )

    async def task_with_trace(trace_id: str, delay: float) -> str:
        """Async task that sets its own trace ID."""
        set_current_trace_id(trace_id)
        await asyncio.sleep(delay)
        return get_current_trace_id()

    async def run_concurrent_tasks():
        """Run multiple tasks concurrently with different trace IDs."""
        results = await asyncio.gather(
            task_with_trace("trace-A", 0.01),
            task_with_trace("trace-B", 0.02),
            task_with_trace("trace-C", 0.01),
        )
        return results

    # Each task should maintain its own trace ID
    results = asyncio.run(run_concurrent_tasks())
    assert results == ["trace-A", "trace-B", "trace-C"]


def test_trace_context_returns_none_when_unset():
    """Test get_current_trace_id returns None when not set."""
    from agent_tracer.context_propagation import get_current_trace_id

    # Should return None in fresh context
    assert get_current_trace_id() is None


def test_span_stack_maintains_hierarchy():
    """Test span stack maintains parent-child relationships."""
    from agent_tracer.context_propagation import (
        push_span,
        pop_span,
        get_current_span,
        get_span_stack,
    )

    async def parent_operation():
        """Parent operation with nested spans."""
        push_span("parent-span")

        # Should be at top of stack
        assert get_current_span() == "parent-span"
        assert get_span_stack() == ["parent-span"]

        await child_operation()

        # After child returns, should be back to parent
        assert get_current_span() == "parent-span"

        popped = pop_span()
        assert popped == "parent-span"
        assert get_current_span() is None

    async def child_operation():
        """Child operation with its own span."""
        push_span("child-span")

        # Should see full hierarchy
        assert get_current_span() == "child-span"
        assert get_span_stack() == ["parent-span", "child-span"]

        await grandchild_operation()

        # After grandchild returns, should be back to child
        assert get_current_span() == "child-span"

        popped = pop_span()
        assert popped == "child-span"

    async def grandchild_operation():
        """Grandchild operation with deepest span."""
        push_span("grandchild-span")

        # Should see full 3-level hierarchy
        assert get_current_span() == "grandchild-span"
        assert get_span_stack() == ["parent-span", "child-span", "grandchild-span"]

        popped = pop_span()
        assert popped == "grandchild-span"

    # Run the hierarchy
    asyncio.run(parent_operation())


def test_span_stack_isolated_across_concurrent_tasks():
    """Test span stacks are isolated between concurrent async tasks."""
    from agent_tracer.context_propagation import (
        push_span,
        pop_span,
        get_span_stack,
    )

    async def task_with_spans(task_id: str, delay: float) -> list:
        """Async task that creates its own span hierarchy."""
        push_span(f"{task_id}-parent")
        await asyncio.sleep(delay / 2)

        push_span(f"{task_id}-child")
        await asyncio.sleep(delay / 2)

        stack = get_span_stack().copy()

        pop_span()  # child
        pop_span()  # parent

        return stack

    async def run_concurrent_tasks():
        """Run multiple tasks concurrently with different spans."""
        results = await asyncio.gather(
            task_with_spans("A", 0.02),
            task_with_spans("B", 0.01),
            task_with_spans("C", 0.02),
        )
        return results

    # Each task should have its own isolated span stack
    results = asyncio.run(run_concurrent_tasks())
    assert results == [
        ["A-parent", "A-child"],
        ["B-parent", "B-child"],
        ["C-parent", "C-child"],
    ]


def test_span_stack_returns_empty_when_unset():
    """Test get_span_stack returns empty list when no spans."""
    from agent_tracer.context_propagation import get_span_stack

    # Should return empty list in fresh context
    assert get_span_stack() == []


def test_pop_span_returns_none_when_empty():
    """Test pop_span returns None when stack is empty."""
    from agent_tracer.context_propagation import pop_span

    # Should return None when no spans
    assert pop_span() is None


def test_get_current_span_returns_none_when_empty():
    """Test get_current_span returns None when stack is empty."""
    from agent_tracer.context_propagation import get_current_span

    # Should return None when no spans
    assert get_current_span() is None
