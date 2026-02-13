"""Generic trace client - works with any agent system."""

import contextvars
import json
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Optional

from .schemas import Trace, TriggerInfo
from .utils import utc_now_iso, calculate_duration_ms

# Thread-safe context variables for trace and span management
_current_trace: contextvars.ContextVar = contextvars.ContextVar('current_trace', default=None)
_span_stack: contextvars.ContextVar = contextvars.ContextVar('span_stack', default=None)

# Storage threshold: artifacts smaller than this are stored inline as JSON.
# Larger artifacts are uploaded to external storage with a preview.
INLINE_ARTIFACT_MAX_BYTES = 10_000
ARTIFACT_PREVIEW_LENGTH = 500

FAILED_SPAN_STATUSES = ("failed", "timeout")


def _require_active_span(span_stack: list) -> dict:
    """Return the current active span or raise if none exists."""
    if not span_stack:
        raise ValueError(
            "No active span. Use the span() context manager before adding steps or artifacts."
        )
    return span_stack[-1]


class TraceClient:
    """Generic trace client for any agent system (RCA, monitoring, CI/CD, etc.).

    Thread-safe: Each thread/async task maintains its own trace context using contextvars.
    """

    def __init__(self, storage_backend):
        self.storage = storage_backend
        # Note: current_trace and span_stack are now managed via context variables,
        # not instance variables, making this client thread-safe

    def get_current_trace(self) -> Optional[Dict]:
        """Get the current trace from context (useful for testing/debugging)."""
        return _current_trace.get()

    def get_span_stack(self) -> Optional[list]:
        """Get the current span stack from context (useful for testing/debugging)."""
        return _span_stack.get()

    def start_trace(self, trigger_type: str, triggered_by: str,
                    metadata: Dict[str, Any], trace_type: str = "agent_execution") -> str:
        """Start a new trace and persist its initial metadata.

        Args:
            trigger_type: What initiated the trace (e.g. "manual", "webhook", "alert").
            triggered_by: Email, system name, or identifier of the initiator.
            metadata: Arbitrary dict of agent-system-specific data.
            trace_type: Classification of the trace (defaults to "agent_execution").

        Returns:
            The unique trace_id for this trace.
        """
        trace_id = f"trace_{uuid.uuid4()}"

        trigger_info = TriggerInfo(
            type=trigger_type,
            source=triggered_by,
            triggered_by=triggered_by,
        )

        trace = Trace(
            trace_id=trace_id,
            trace_type=trace_type,
            trigger=trigger_info,
            metadata=metadata,
        )

        trace_dict = trace.model_dump(mode='json')
        _current_trace.set(trace_dict)
        _span_stack.set([])
        self.storage.write_trace_metadata(trace_id, trace_dict)

        return trace_id

    @contextmanager
    def span(self, name: str, span_type: str, agent_metadata: Optional[Dict] = None):
        """Context manager that creates, tracks, and finalizes a span.

        Yields a mutable span dict. On success the span is marked "completed";
        on exception it is marked "failed" with error details, and the exception
        is re-raised.

        Thread-safe: Uses context variables to isolate trace state per thread/task.
        """
        current_trace = _current_trace.get()
        if not current_trace:
            raise ValueError("No active trace. Call start_trace() first.")

        span_stack = _span_stack.get()
        if span_stack is None:
            span_stack = []
            _span_stack.set(span_stack)

        span_id = f"span_{uuid.uuid4().hex[:12]}"
        parent_span_id = span_stack[-1]["span_id"] if span_stack else None

        span_data = {
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "trace_id": current_trace["trace_id"],
            "name": name,
            "type": span_type,
            "status": "running",
            "start_time": utc_now_iso(),
            "agent_metadata": agent_metadata or {},
            "steps": [],
            "artifacts": [],
            "output": {},
        }

        span_stack.append(span_data)

        try:
            yield span_data
            span_data["status"] = "completed"
        except Exception as e:
            span_data["status"] = "failed"
            span_data["error"] = {
                "message": str(e),
                "type": type(e).__name__,
            }
            raise
        finally:
            span_data["end_time"] = utc_now_iso()
            span_data["duration_ms"] = calculate_duration_ms(
                datetime.fromisoformat(span_data["start_time"]),
                datetime.fromisoformat(span_data["end_time"]),
            )

            current_trace["spans"].append(span_data)
            span_stack.pop()
            self.storage.write_span(current_trace["trace_id"], span_data)

    def add_step(self, name: str, step_type: str, input_data: Dict, output_data: Dict) -> Dict:
        """Add a completed step to the current active span."""
        span_stack = _span_stack.get()
        if span_stack is None:
            span_stack = []
        current_span = _require_active_span(span_stack)

        step_data = {
            "step_id": f"step_{uuid.uuid4().hex[:12]}",
            "span_id": current_span["span_id"],
            "step_type": step_type,
            "name": name,
            "status": "completed",
            "start_time": utc_now_iso(),
            "input": input_data,
            "output": output_data,
        }

        current_span["steps"].append(step_data)
        return step_data

    def add_artifact(self, name: str, artifact_type: str, content: Any,
                     metadata: Optional[Dict] = None) -> str:
        """Add an artifact to the current active span.

        Small artifacts (< INLINE_ARTIFACT_MAX_BYTES) are stored inline.
        Larger artifacts are uploaded to external storage with a text preview.

        Returns:
            The unique artifact_id.
        """
        current_trace = _current_trace.get()
        if not current_trace:
            raise ValueError("No active trace")

        span_stack = _span_stack.get()
        if span_stack is None:
            span_stack = []
        current_span = _require_active_span(span_stack)

        artifact_id = f"artifact_{uuid.uuid4().hex[:12]}"
        is_structured = isinstance(content, (dict, list))
        content_str = json.dumps(content) if is_structured else str(content)
        size_bytes = len(content_str.encode("utf-8"))

        artifact_data = {
            "artifact_id": artifact_id,
            "trace_id": current_trace["trace_id"],
            "span_id": current_span["span_id"],
            "name": name,
            "artifact_type": artifact_type,
            "content_type": "application/json" if is_structured else "text/plain",
            "metadata": metadata or {},
            "created_at": _utc_now_iso(),
        }

        if size_bytes < INLINE_ARTIFACT_MAX_BYTES:
            artifact_data["storage"] = {"strategy": "inline", "size_bytes": size_bytes}
            artifact_data["content"] = content
        else:
            location = self.storage.upload_artifact(
                current_trace["trace_id"],
                artifact_id,
                content_str,
            )
            artifact_data["storage"] = {
                "strategy": "external_ref",
                "location": location,
                "size_bytes": size_bytes,
            }
            artifact_data["content"] = None
            artifact_data["preview"] = content_str[:ARTIFACT_PREVIEW_LENGTH]

        current_span["artifacts"].append(artifact_data)
        return artifact_id

    def add_decision(self, name: str, reasoning: str, criteria: list, final_score: float) -> Dict:
        """Add a decision step with reasoning, criteria, and a confidence score."""
        decision_logic = {
            "reasoning": reasoning,
            "criteria": criteria,
            "final_score": final_score,
        }
        return self.add_step(
            name=name,
            step_type="decision",
            input_data={"criteria": criteria},
            output_data={
                **decision_logic,
                "decision_logic": decision_logic,
            },
        )

    def complete_trace(self, status: str, summary: Dict[str, Any]) -> str:
        """Finalize the trace with a status, compute summary metrics, and persist.

        Returns:
            The trace_id of the completed trace.
        """
        current_trace = _current_trace.get()
        if not current_trace:
            raise ValueError("No active trace to complete")

        current_trace["status"] = status
        current_trace["completed_at"] = utc_now_iso()
        current_trace["duration_ms"] = calculate_duration_ms(
            datetime.fromisoformat(current_trace["created_at"]),
            datetime.fromisoformat(current_trace["completed_at"]),
        )

        current_trace["summary"].update(summary)
        spans = current_trace["spans"]
        current_trace["summary"]["total_spans"] = len(spans)
        current_trace["summary"]["failed_spans"] = sum(
            1 for s in spans if s["status"] in FAILED_SPAN_STATUSES
        )

        # Set root_span_id to the span with no parent (top-level span)
        root_spans = [s for s in spans if s.get("parent_span_id") is None]
        if root_spans:
            current_trace["root_span_id"] = root_spans[0]["span_id"]

        self.storage.finalize_trace(current_trace["trace_id"], current_trace)

        return current_trace["trace_id"]
