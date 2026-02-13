"""Generic storage backend for Agent Trace."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_tracer.core.utils import serialize_datetime, utc_now

# Maximum number of traces returned by metadata queries
DEFAULT_QUERY_LIMIT = 100


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class TraceNotFoundError(Exception):
    """Raised when trace does not exist."""
    pass


class TraceStorageBackend:
    """Storage backend using PostgreSQL for metadata and disk for full trace JSON."""

    def __init__(self, db_conn, storage_dir: str):
        self.db = db_conn
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def write_trace_metadata(self, trace_id: str, trace: Dict[str, Any]) -> None:
        """Write trace metadata to PostgreSQL."""
        if self.db is None:
            return  # Skip database write if no connection

        cursor = self.db.cursor()

        # Handle triggered_at with proper serialization and default
        triggered_at = trace["trigger"].get("triggered_at")
        if not triggered_at:
            triggered_at = utc_now().isoformat()
        else:
            triggered_at = serialize_datetime(triggered_at)

        cursor.execute("""
            INSERT INTO agent_tracer_traces (
                trace_id, trace_type, status, trigger_type, trigger_source,
                triggered_by, triggered_at, created_at, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """, (
            trace_id,
            trace.get("trace_type", "agent_execution"),
            trace.get("status", "running"),
            trace["trigger"]["type"],
            trace["trigger"]["source"],
            trace["trigger"]["triggered_by"],
            triggered_at,
            trace["created_at"],
            json.dumps(trace["metadata"]),
        ))

        self.db.commit()

    def write_span(self, trace_id: str, span: Dict[str, Any]) -> None:
        """Write a span record to PostgreSQL."""
        if self.db is None:
            return  # Skip database write if no connection

        cursor = self.db.cursor()

        cursor.execute("""
            INSERT INTO agent_tracer_spans (
                span_id, trace_id, parent_span_id, name, span_type,
                status, start_time, end_time, duration_ms, agent_metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """, (
            span["span_id"],
            trace_id,
            span.get("parent_span_id"),
            span["name"],
            span["type"],
            span["status"],
            span["start_time"],
            span.get("end_time"),
            span.get("duration_ms"),
            json.dumps(span.get("agent_metadata", {})),
        ))

        self.db.commit()

    def upload_artifact(self, trace_id: str, artifact_id: str, content: str) -> str:
        """Upload artifact content to disk storage.

        Returns:
            A relative path to the stored artifact (portable across systems).
        """
        trace_dir = self.storage_dir / trace_id / "artifacts"
        trace_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = trace_dir / f"{artifact_id}.txt"
        artifact_path.write_text(content, encoding="utf-8")

        # Return relative path instead of file:// URI for portability
        relative_path = artifact_path.relative_to(self.storage_dir)
        return str(relative_path)

    def finalize_trace(self, trace_id: str, trace: Dict[str, Any]) -> None:
        """Update the trace record in PostgreSQL and write the full trace JSON to disk."""
        if self.db is not None:
            cursor = self.db.cursor()

            cursor.execute("""
                UPDATE agent_tracer_traces SET
                    status = %s,
                    completed_at = %s,
                    duration_ms = %s,
                    total_spans = %s,
                    failed_spans = %s,
                    summary_metrics = %s::jsonb,
                    trace_document_url = %s
                WHERE trace_id = %s
            """, (
                trace["status"],
                trace["completed_at"],
                trace["duration_ms"],
                trace["summary"]["total_spans"],
                trace["summary"]["failed_spans"],
                json.dumps(trace["summary"].get("extra", {})),
                f"{trace_id}/trace.json",  # Relative path for portability
                trace_id,
            ))

            self.db.commit()

        # Always write to disk
        trace_dir = self.storage_dir / trace_id
        trace_dir.mkdir(parents=True, exist_ok=True)

        trace_file = trace_dir / "trace.json"
        trace_file.write_text(json.dumps(trace, indent=2, cls=DateTimeEncoder), encoding="utf-8")

    def get_trace_full(self, trace_id: str) -> Dict[str, Any]:
        """Retrieve the complete trace JSON from disk.

        Raises:
            TraceNotFoundError: If trace does not exist.
        """
        trace_file = self.storage_dir / trace_id / "trace.json"

        if not trace_file.exists():
            raise TraceNotFoundError(f"Trace not found: {trace_id}")

        return json.loads(trace_file.read_text(encoding="utf-8"))

    def query_traces_by_metadata(self, metadata_key: str, metadata_value: Any) -> List[Dict[str, Any]]:
        """Query traces by a single metadata field using JSONB containment.

        Returns:
            A list of matching trace summaries (trace_id, metadata, created_at),
            ordered by most recent first.
        """
        if self.db is None:
            return []  # Cannot query without database

        cursor = self.db.cursor()

        # Use JSONB containment (@>) for proper type-safe querying
        cursor.execute("""
            SELECT trace_id, metadata, created_at
            FROM agent_tracer_traces
            WHERE metadata @> %s::jsonb
            ORDER BY created_at DESC
            LIMIT %s
        """, (json.dumps({metadata_key: metadata_value}), DEFAULT_QUERY_LIMIT))

        rows = cursor.fetchall()
        return [
            {"trace_id": row[0], "metadata": row[1], "created_at": row[2]}
            for row in rows
        ]
