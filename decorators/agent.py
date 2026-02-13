"""Decorator for adding tracing to agent classes."""

import functools
from typing import Optional
from agent_tracer.core.trace_client import TraceClient
from agent_tracer.utils.fail_safe import FailSafeTraceClient
from agent_tracer.context.propagation import set_current_trace_id


def traced_agent(trace_client: TraceClient, fail_safe: bool = True):
    """Decorator that adds tracing to Agent classes.

    Args:
        trace_client: TraceClient instance for logging
        fail_safe: If True, tracing errors won't break the agent

    Usage:
        @traced_agent(trace_client)
        class MyAgent(Agent):
            async def run(self, task):
                return result
    """
    def decorator(agent_class):
        # Wrap __init__ to inject callbacks for LangGraph agents
        original_init = agent_class.__init__

        @functools.wraps(original_init)
        def wrapped_init(self, *args, **kwargs):
            # Call original __init__
            original_init(self, *args, **kwargs)

            # If this is a LangGraph agent (has callbacks attribute), inject our callback
            if hasattr(self, 'callbacks') and isinstance(self.callbacks, list):
                try:
                    from agent_tracer.integrations.langchain import ComprehensiveTracingCallback

                    # Create callback instance with the trace client
                    callback = ComprehensiveTracingCallback(trace_client)

                    # Insert at the front so it sees all events
                    self.callbacks.insert(0, callback)
                except ImportError:
                    # LangChain integration not available, skip
                    pass

        agent_class.__init__ = wrapped_init

        # Wrap run method with tracing
        original_run = agent_class.run

        @functools.wraps(original_run)
        async def traced_run(self, task, **kwargs):
            # Wrap in fail-safe if requested
            tracer = FailSafeTraceClient(trace_client) if fail_safe else trace_client

            trace_id = None
            try:
                # Start trace
                trace_id = tracer.start_trace(
                    trigger_type="agent_task",
                    triggered_by=task.get("sender", "unknown") if isinstance(task, dict) else "unknown",
                    metadata={
                        "agent": agent_class.__name__,
                        "task_type": type(task).__name__
                    }
                )

                # Set context for nested calls
                if trace_id:
                    set_current_trace_id(trace_id)

                with tracer.span(f"{agent_class.__name__} Execution", "agent"):
                    # Capture context if available
                    if hasattr(self, '_capture_context'):
                        try:
                            context = self._capture_context((), {'task': task})
                            tracer.add_artifact(
                                "Pre-Execution Context",
                                "context",
                                context.model_dump() if hasattr(context, 'model_dump') else str(context)
                            )
                        except Exception:
                            pass  # Don't fail on context capture

                    # Run agent
                    result = await original_run(self, task, **kwargs)

                    # Extract decision if result is AgentDecision
                    if hasattr(result, 'reasoning'):
                        try:
                            tracer.add_decision(
                                name="Agent Decision",
                                reasoning=result.reasoning,
                                criteria=[
                                    {
                                        "factor": c.factor,
                                        "score": c.score,
                                        "weight": c.weight
                                    }
                                    for c in getattr(result, 'criteria', [])
                                ],
                                final_score=getattr(result, 'confidence', 1.0)
                            )
                        except Exception:
                            pass  # Don't fail on decision extraction

                # Span exited - now complete trace
                tracer.complete_trace(
                    status="completed",
                    summary={"result": "success"}
                )
                return result

            except Exception as e:
                # Agent failed - trace the error
                if trace_id:
                    tracer.complete_trace(
                        status="failed",
                        summary={"error": str(e), "type": type(e).__name__}
                    )
                raise

        agent_class.run = traced_run
        return agent_class

    return decorator
