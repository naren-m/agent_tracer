"""Decorator for tracing LLM calls with context capture."""

import functools
from agent_tracer import TraceClient
from utils.fail_safe import FailSafeTraceClient


def traced_llm_call(trace_client: TraceClient, fail_safe: bool = True):
    """Decorator for tracing LLM calls with context capture and decision extraction.

    Captures context BEFORE the call (if agent has LLMContextCaptureMixin),
    extracts decision AFTER the call (if result is AgentDecision),
    and logs alternatives if available.

    Args:
        trace_client: TraceClient instance
        fail_safe: If True, tracing errors won't break the LLM call

    Usage:
        class MyAgent(LLMContextCaptureMixin):
            @traced_llm_call(trace_client)
            async def call_llm(self, prompt):
                return AgentDecision(...)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Wrap in fail-safe if requested
            tracer = FailSafeTraceClient(trace_client) if fail_safe else trace_client

            with tracer.span(f"LLM Call: {func.__name__}", "llm"):
                # Capture context BEFORE call (if agent has mixin)
                if args and hasattr(args[0], '_capture_context'):
                    try:
                        context = args[0]._capture_context(args[1:], kwargs)
                        tracer.add_artifact(
                            "LLM Context",
                            "context",
                            context.model_dump() if hasattr(context, 'model_dump') else str(context)
                        )
                    except Exception:
                        pass  # Don't fail on context capture

                # Execute LLM call
                result = await func(*args, **kwargs)

                # Extract decision AFTER call (if result is AgentDecision)
                if hasattr(result, 'reasoning'):
                    try:
                        tracer.add_decision(
                            name=f"LLM Decision: {func.__name__}",
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

                        # Log alternatives if available
                        if hasattr(result, 'alternatives'):
                            try:
                                tracer.add_artifact(
                                    "Decision Alternatives",
                                    "alternatives",
                                    [alt.model_dump() if hasattr(alt, 'model_dump') else str(alt)
                                     for alt in result.alternatives]
                                )
                            except Exception:
                                pass  # Don't fail on alternatives logging

                    except Exception:
                        pass  # Don't fail on decision extraction

                return result

        return wrapper
    return decorator
