"""Generic Agent Tracer data models - works with any agent system."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from .utils import utc_now, serialize_datetime

# Length of hex suffix used for short unique IDs (spans, steps, artifacts)
_SHORT_ID_HEX_LENGTH = 12


def _generate_short_id(prefix: str) -> str:
    """Generate a short unique ID with the given prefix (e.g. 'span', 'step', 'artifact')."""
    return f"{prefix}_{uuid.uuid4().hex[:_SHORT_ID_HEX_LENGTH]}"


# Order matters: Define models bottom-up so forward references aren't needed
# Order: TriggerInfo -> TraceSummary -> AgentMetadata -> StorageInfo -> Step -> Artifact -> Span -> Trace


class TriggerInfo(BaseModel):
    """Trigger information describing what initiated a trace."""
    type: str
    source: str
    triggered_by: str
    triggered_at: datetime = Field(default_factory=utc_now)

    @field_serializer('triggered_at', when_used='json')
    def serialize_triggered_at(self, dt: datetime) -> str:
        """Serialize datetime to ISO format string for JSON mode."""
        return serialize_datetime(dt)


class TraceSummary(BaseModel):
    """Summary metrics for a completed trace."""
    total_spans: int = 0
    failed_spans: int = 0
    extra: Dict[str, Any] = Field(default_factory=dict)  # User-defined metrics


class AgentMetadata(BaseModel):
    """Agent-specific metadata for spans."""
    agent_type: str
    timeout_limit_ms: Optional[int] = None
    retry_count: int = 0
    extra: Dict[str, Any] = Field(default_factory=dict)  # User-defined fields


class StorageInfo(BaseModel):
    """Storage location and size information for an artifact."""
    strategy: str
    location: Optional[str] = None
    size_bytes: int
    checksum: Optional[str] = None


class Step(BaseModel):
    """A single action within a span."""
    step_id: str = Field(default_factory=lambda: _generate_short_id("step"))
    span_id: str
    step_type: str

    name: str
    status: str = "completed"

    start_time: datetime = Field(default_factory=utc_now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None

    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)

    decision_logic: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None

    @field_serializer('start_time', 'end_time', when_used='json')
    def serialize_step_times(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string for JSON mode."""
        return serialize_datetime(dt)


class Artifact(BaseModel):
    """Artifact attached to a span or step."""
    artifact_id: str = Field(default_factory=lambda: _generate_short_id("artifact"))
    trace_id: str
    span_id: str
    step_id: Optional[str] = None

    name: str
    artifact_type: str
    content_type: str = "text/plain"

    storage: StorageInfo
    content: Optional[Any] = None
    preview: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)  # Domain-specific data
    tags: List[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=utc_now)

    @field_serializer('created_at', when_used='json')
    def serialize_artifact_created_at(self, dt: datetime) -> str:
        """Serialize datetime to ISO format string for JSON mode."""
        return serialize_datetime(dt)


class Span(BaseModel):
    """An execution span representing an agent or phase."""
    span_id: str = Field(default_factory=lambda: _generate_short_id("span"))
    parent_span_id: Optional[str] = None
    trace_id: str

    name: str
    type: str
    status: str = "running"

    start_time: datetime = Field(default_factory=utc_now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None

    agent_metadata: Optional[AgentMetadata] = None

    steps: List[Step] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)

    output: Dict[str, Any] = Field(default_factory=dict)

    @field_serializer('start_time', 'end_time', when_used='json')
    def serialize_span_times(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string for JSON mode."""
        return serialize_datetime(dt)


class Trace(BaseModel):
    """Top-level trace representing an agent system execution."""

    trace_id: str = Field(default_factory=lambda: f"trace_{uuid.uuid4()}")
    trace_type: str = "agent_execution"
    status: str = "running"

    created_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    trigger: TriggerInfo
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Domain-specific data

    root_span_id: Optional[str] = None
    spans: List[Span] = Field(default_factory=list)  # Properly typed now!

    summary: TraceSummary = Field(default_factory=TraceSummary)

    @field_serializer('created_at', 'completed_at', when_used='json')
    def serialize_trace_times(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string for JSON mode."""
        return serialize_datetime(dt)


# No model_rebuild() needed anymore - classes are properly ordered!
