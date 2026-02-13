"""Decorator for tracing regular async functions."""

import functools
from typing import Optional
from agent_tracer.core.trace_client import TraceClient


def traced_function(trace_client: TraceClient, span_name: Optional[str] = None):
    """Decorator for tracing regular async functions.

    Args:
        trace_client: TraceClient instance
        span_name: Optional custom span name

    Usage:
        @traced_function(trace_client)
        async def my_function(arg):
            return result
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            name = span_name or f"Function: {func.__name__}"

            with trace_client.span(name, "function"):
                return await func(*args, **kwargs)

        return wrapper
    return decorator
