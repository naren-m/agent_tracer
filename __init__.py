"""Agent Tracer - Generic tracing library for AI agent systems."""

__version__ = "0.2.0"

# Core schemas and client
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
    # Storage backend may not be available if dependencies missing
    TraceStorageBackend = None
    TraceNotFoundError = None

# Decorators
from agent_tracer.decorators.agent_decorator import agent
from agent_tracer.decorators.llm_decorators import traced_llm_call, traced_anthropic, traced_openai
from agent_tracer.decorators.decision_decorator import traced_decision
from agent_tracer.decorators.generic_decorators import traced

# Models
from agent_tracer.models.decision_models import AgentDecision, DecisionCriteria, Alternative

# Context management
from agent_tracer.context.context_propagation import (
    set_current_trace_id,
    get_current_trace_id,
    get_span_stack,
)
from agent_tracer.context.context_capture import capture_context

# Utilities
from agent_tracer.utils.fail_safe import FailSafeTraceClient

__all__ = [
    # Core
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
    # Decorators
    "agent",
    "traced_llm_call",
    "traced_anthropic",
    "traced_openai",
    "traced_decision",
    "traced",
    # Models
    "AgentDecision",
    "DecisionCriteria",
    "Alternative",
    # Context
    "set_current_trace_id",
    "get_current_trace_id",
    "get_span_stack",
    "capture_context",
    # Utilities
    "FailSafeTraceClient",
]
