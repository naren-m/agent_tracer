"""Zipkin trace exporter - converts agent_tracer format to Zipkin JSON format.

Zipkin format is simpler than Jaeger and can be directly ingested via HTTP.
Jaeger supports Zipkin format ingestion on port 9411.
"""

import json
from datetime import datetime
from typing import Any, Dict, List
import requests


class ZipkinExporter:
    """Export traces to Zipkin format for Jaeger ingestion.

    Zipkin format is simpler and can be directly sent to Jaeger's Zipkin
    endpoint (port 9411) via HTTP POST.

    Usage:
        exporter = ZipkinExporter()
        exporter.send_to_jaeger(trace_data)
    """

    def __init__(self, service_name: str = "a2a-agent"):
        """Initialize Zipkin exporter.

        Args:
            service_name: Name of the service (default: "a2a-agent")
        """
        self.service_name = service_name

    def convert_trace(self, trace_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert agent_tracer trace to Zipkin format.

        Args:
            trace_data: Trace dict from agent_tracer

        Returns:
            List of Zipkin span dicts
        """
        trace_id = self._format_trace_id(trace_data["trace_id"])
        zipkin_spans = []

        for span in trace_data.get("spans", []):
            zipkin_span = self._convert_span(span, trace_id)
            zipkin_spans.append(zipkin_span)

        return zipkin_spans

    def _convert_span(self, span: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """Convert a single span to Zipkin format.

        Args:
            span: Span dict from agent_tracer
            trace_id: Zipkin-formatted trace ID

        Returns:
            Zipkin-formatted span dict
        """
        span_id = self._format_span_id(span["span_id"])
        timestamp = self._to_microseconds(span["start_time"])
        duration = span.get("duration_ms", 0) * 1000  # Convert ms to microseconds

        # Build Zipkin span
        zipkin_span = {
            "traceId": trace_id,
            "id": span_id,
            "name": span.get("name", "unknown"),
            "timestamp": timestamp,
            "duration": duration,
            "localEndpoint": {
                "serviceName": self.service_name
            },
            "tags": {
                "span.type": span.get("type", "internal"),
                "status": span.get("status", "completed")
            }
        }

        # Add parent span if exists
        if span.get("parent_span_id"):
            zipkin_span["parentId"] = self._format_span_id(span["parent_span_id"])

        # Add agent metadata as tags
        for key, value in span.get("agent_metadata", {}).items():
            zipkin_span["tags"][f"agent.{key}"] = str(value)

        # Add error info if failed
        if span.get("status") == "failed" and span.get("error"):
            zipkin_span["tags"]["error"] = "true"
            zipkin_span["tags"]["error.message"] = span["error"].get("message", "")
            zipkin_span["tags"]["error.type"] = span["error"].get("type", "")

        # Add annotations for steps and artifacts
        annotations = []

        # Add steps as annotations
        for step in span.get("steps", []):
            step_time = self._to_microseconds(step.get("start_time", span["start_time"]))
            annotations.append({
                "timestamp": step_time,
                "value": f"step: {step.get('name', 'unknown')} ({step.get('step_type', '')})"
            })

        # Add artifacts as annotations
        for artifact in span.get("artifacts", []):
            artifact_time = self._to_microseconds(artifact.get("created_at", span["start_time"]))
            annotations.append({
                "timestamp": artifact_time,
                "value": f"artifact: {artifact.get('name', 'unknown')} ({artifact.get('artifact_type', '')})"
            })

        if annotations:
            zipkin_span["annotations"] = annotations

        return zipkin_span

    def _format_trace_id(self, trace_id: str) -> str:
        """Convert trace_id to Zipkin format (16 or 32 hex chars).

        Args:
            trace_id: Original trace ID (e.g., "trace_uuid")

        Returns:
            32-character hex string for Zipkin
        """
        # Use the UUID part directly if present
        if "trace_" in trace_id:
            trace_id = trace_id.replace("trace_", "").replace("-", "")
        return trace_id.ljust(32, '0')[:32]

    def _format_span_id(self, span_id: str) -> str:
        """Convert span_id to Zipkin format (16 hex chars).

        Args:
            span_id: Original span ID (e.g., "span_abc123")

        Returns:
            16-character hex string for Zipkin
        """
        # Extract the hex part from span_id
        if "span_" in span_id:
            hex_part = span_id.replace("span_", "")
            return hex_part.ljust(16, '0')[:16]
        return span_id.ljust(16, '0')[:16]

    def _to_microseconds(self, timestamp: str) -> int:
        """Convert ISO timestamp to microseconds since epoch.

        Args:
            timestamp: ISO 8601 timestamp string

        Returns:
            Microseconds since Unix epoch
        """
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return int(dt.timestamp() * 1_000_000)

    def send_to_jaeger(self, trace_data: Dict[str, Any],
                       zipkin_url: str = "http://localhost:9411/api/v2/spans") -> bool:
        """Send trace to Jaeger via Zipkin endpoint.

        Args:
            trace_data: Trace dict from agent_tracer
            zipkin_url: Zipkin endpoint URL (default: http://localhost:9411/api/v2/spans)

        Returns:
            True if successful, False otherwise
        """
        try:
            zipkin_spans = self.convert_trace(trace_data)

            response = requests.post(
                zipkin_url,
                json=zipkin_spans,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 202:
                print(f"✓ Trace sent to Jaeger (via Zipkin): {len(zipkin_spans)} spans")
                return True
            else:
                print(f"✗ Failed to send trace: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"✗ Could not connect to Jaeger Zipkin endpoint at {zipkin_url}")
            print("  Make sure Jaeger is running with Zipkin endpoint enabled")
            return False
        except Exception as e:
            print(f"✗ Error sending trace: {e}")
            return False

    def send_trace_file(self, trace_file: str,
                        zipkin_url: str = "http://localhost:9411/api/v2/spans") -> bool:
        """Send a trace file to Jaeger via Zipkin endpoint.

        Args:
            trace_file: Path to trace JSON file
            zipkin_url: Zipkin endpoint URL

        Returns:
            True if successful, False otherwise
        """
        with open(trace_file, 'r') as f:
            trace_data = json.load(f)
        return self.send_to_jaeger(trace_data, zipkin_url)
