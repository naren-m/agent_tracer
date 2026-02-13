"""Decorator for tracing tool executions."""

import functools
from agent_tracer.core.trace_client import TraceClient


def traced_tool(trace_client: TraceClient):
    """Decorator for tracing tool executions.

    Args:
        trace_client: TraceClient instance

    Usage:
        @traced_tool(trace_client)
        async def search_web(query):
            return results
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with trace_client.span(f"Tool: {func.__name__}", "tool"):
                result = await func(*args, **kwargs)

                # Log as step
                trace_client.add_step(
                    name=func.__name__,
                    step_type="tool_execution",
                    input_data={"args": args, "kwargs": kwargs},
                    output_data={"result": result}
                )

                return result

        return wrapper
    return decorator
