"""Shared utility functions for Agent Tracer."""

from datetime import datetime, timezone
from typing import Any, Optional


def utc_now() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Return the current UTC datetime as an ISO 8601 string."""
    return utc_now().isoformat()


def serialize_datetime(dt: Any) -> Optional[str]:
    """Convert datetime to ISO format string.

    Args:
        dt: A datetime object or ISO string or None

    Returns:
        ISO format string or None if input is None
    """
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    if isinstance(dt, str):
        return dt  # Already serialized
    return str(dt)  # Fallback


def calculate_duration_ms(start: datetime, end: datetime) -> int:
    """Calculate duration between two datetimes in milliseconds.

    Args:
        start: Start datetime
        end: End datetime

    Returns:
        Duration in milliseconds
    """
    return int((end - start).total_seconds() * 1000)
