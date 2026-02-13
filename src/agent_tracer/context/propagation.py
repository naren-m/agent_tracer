"""Async-safe context propagation using contextvars.

This module provides thread-safe and async-safe context propagation for trace IDs
and span hierarchies using Python's contextvars module.
"""

from contextvars import ContextVar
from typing import Optional, List


# Context variables for trace ID and span stack
_current_trace_id: ContextVar[Optional[str]] = ContextVar(
    "current_trace_id", default=None
)
_span_stack: ContextVar[List[str]] = ContextVar("span_stack", default=None)


def set_current_trace_id(trace_id: str) -> None:
    """Set the current trace ID in the async context.

    Args:
        trace_id: The trace ID to set for the current context
    """
    _current_trace_id.set(trace_id)


def get_current_trace_id() -> Optional[str]:
    """Get the current trace ID from the async context.

    Returns:
        The current trace ID, or None if not set
    """
    return _current_trace_id.get()


def push_span(span_id: str) -> None:
    """Push a new span onto the span stack.

    Args:
        span_id: The span ID to push onto the stack
    """
    stack = _span_stack.get()
    if stack is None:
        stack = []
    else:
        # Create a copy to avoid mutating shared state
        stack = stack.copy()

    stack.append(span_id)
    _span_stack.set(stack)


def pop_span() -> Optional[str]:
    """Pop the current span from the span stack.

    Returns:
        The popped span ID, or None if the stack is empty
    """
    stack = _span_stack.get()
    if stack is None or len(stack) == 0:
        return None

    # Create a copy to avoid mutating shared state
    stack = stack.copy()
    span_id = stack.pop()
    _span_stack.set(stack)

    return span_id


def get_current_span() -> Optional[str]:
    """Get the current (top) span from the span stack.

    Returns:
        The current span ID, or None if the stack is empty
    """
    stack = _span_stack.get()
    if stack is None or len(stack) == 0:
        return None

    return stack[-1]


def get_span_stack() -> List[str]:
    """Get the full span stack showing the hierarchy.

    Returns:
        A copy of the span stack, or an empty list if not set
    """
    stack = _span_stack.get()
    if stack is None:
        return []

    # Return a copy to prevent external mutation
    return stack.copy()
