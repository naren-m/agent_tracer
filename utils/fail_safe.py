"""Fail-safe wrapper for TraceClient that never breaks agents."""
import logging
import contextlib
from typing import Optional, Any


class FailSafeTraceClient:
    """TraceClient wrapper that catches all exceptions."""

    def __init__(self, inner_client, logger: Optional[logging.Logger] = None):
        """Initialize fail-safe wrapper.

        Args:
            inner_client: The actual TraceClient instance to wrap
            logger: Optional logger for recording failures
        """
        self._client = inner_client
        self._logger = logger or logging.getLogger(__name__)
        self._failed = False

    def _safe_call(self, method_name: str, *args, **kwargs) -> Optional[Any]:
        """Execute trace operation safely.

        Args:
            method_name: Name of the method to call on inner client
            *args: Positional arguments to pass
            **kwargs: Keyword arguments to pass

        Returns:
            Result of the operation, or None if it failed
        """
        if self._failed:
            return None  # Skip if already failed

        try:
            method = getattr(self._client, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            self._logger.warning(f"Trace operation {method_name} failed: {e}")
            self._failed = True  # Don't try again this trace
            return None

    def start_trace(self, *args, **kwargs):
        """Start a trace (fail-safe)."""
        return self._safe_call('start_trace', *args, **kwargs)

    def complete_trace(self, *args, **kwargs):
        """Complete a trace (fail-safe)."""
        return self._safe_call('complete_trace', *args, **kwargs)

    def add_decision(self, *args, **kwargs):
        """Add a decision (fail-safe)."""
        return self._safe_call('add_decision', *args, **kwargs)

    def add_step(self, *args, **kwargs):
        """Add a step (fail-safe)."""
        return self._safe_call('add_step', *args, **kwargs)

    def add_artifact(self, *args, **kwargs):
        """Add an artifact (fail-safe)."""
        return self._safe_call('add_artifact', *args, **kwargs)

    def span(self, *args, **kwargs):
        """Create a span context (fail-safe).

        Returns:
            Context manager for the span, or nullcontext if failed
        """
        if self._failed:
            return contextlib.nullcontext()

        try:
            return self._client.span(*args, **kwargs)
        except Exception as e:
            self._logger.warning(f"Span creation failed: {e}")
            self._failed = True
            return contextlib.nullcontext()
