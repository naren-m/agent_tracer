"""Agent Tracer - Universal tracing library for AI agent systems."""

__version__ = "0.2.0"

# Core schemas and client (v0.1.0 compatibility)
from agent_tracer.core.schemas import (
    Trace,
    Span,
    Step,
    Artifact,
    TriggerInfo,
    TraceSummary,
    StorageInfo,
    AgentMetadata,
)
from agent_tracer.core.trace_client import TraceClient

# Storage (optional dependency)
try:
    from agent_tracer.storage.storage_backend import TraceStorageBackend, TraceNotFoundError
except ImportError:
    TraceStorageBackend = None
    TraceNotFoundError = None

# Decorators (v0.2.0)
from agent_tracer.decorators import traced_agent, traced_llm_call, traced_function, traced_tool

# Models (v0.2.0)
from agent_tracer.models import AgentDecision, DecisionCriteria, LLMContext

# Context management (v0.2.0)
from agent_tracer.context import (
    LLMContextCaptureMixin,
    get_current_trace_id,
    set_current_trace_id,
    get_current_span,
    push_span,
    pop_span,
    get_span_stack,
)

# Utilities (v0.2.0)
from agent_tracer.utils import FailSafeTraceClient

__all__ = [
    # Core (v0.1.0)
    "Trace",
    "Span",
    "Step",
    "Artifact",
    "TriggerInfo",
    "TraceSummary",
    "StorageInfo",
    "AgentMetadata",
    "TraceClient",
    "TraceStorageBackend",
    "TraceNotFoundError",
    # Decorators (v0.2.0)
    "traced_agent",
    "traced_llm_call",
    "traced_function",
    "traced_tool",
    # Models (v0.2.0)
    "AgentDecision",
    "DecisionCriteria",
    "LLMContext",
    # Context (v0.2.0)
    "LLMContextCaptureMixin",
    "get_current_trace_id",
    "set_current_trace_id",
    "get_current_span",
    "push_span",
    "pop_span",
    "get_span_stack",
    # Utilities (v0.2.0)
    "FailSafeTraceClient",
]
