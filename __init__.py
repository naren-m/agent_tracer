"""Agent Tracer - Generic tracing library for AI agent systems."""

__version__ = "0.1.0"

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

try:
    from agent_tracer.storage.storage_backend import TraceStorageBackend, TraceNotFoundError
except ImportError:
    # Storage backend may not be available if dependencies missing
    TraceStorageBackend = None
    TraceNotFoundError = None

__all__ = [
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
]
