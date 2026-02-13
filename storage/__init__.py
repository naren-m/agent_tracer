"""Storage module for agent traces."""

from agent_tracer.storage.storage_backend import TraceStorageBackend, TraceNotFoundError

__all__ = ["TraceStorageBackend", "TraceNotFoundError"]
