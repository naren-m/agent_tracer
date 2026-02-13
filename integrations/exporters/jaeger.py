"""Jaeger trace exporter - converts agent_tracer format to Jaeger JSON format."""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests


class JaegerExporter:
    """Export traces to Jaeger format.

    Converts agent_tracer trace JSON to Jaeger-compatible format that can be:
    - Saved to file for manual import
    - Sent directly to Jaeger collector via HTTP
    - Visualized in Jaeger UI

    Usage:
        exporter = JaegerExporter()

        # From trace file
        exporter.export_file("traces/trace_abc/trace.json", "jaeger_trace.json")

        # From trace dict
        trace_data = {...}
        jaeger_json = exporter.convert_trace(trace_data)

        # Send to Jaeger (requires Jaeger collector running)
        exporter.send_to_jaeger(trace_data, "http://localhost:14268/api/traces")
    """

    def __init__(self, service_name: str = "a2a-agent"):
        """Initialize Jaeger exporter.

        Args:
            service_name: Name of the service for Jaeger (default: "a2a-agent")
        """
        self.service_name = service_name

    def convert_trace(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert agent_tracer trace to Jaeger format.

        Args:
            trace_data: Trace dict from agent_tracer

        Returns:
            Jaeger-formatted trace dict
        """
        trace_id = self._format_trace_id(trace_data["trace_id"])

        # Convert all spans
        jaeger_spans = []
        for span in trace_data.get("spans", []):
            jaeger_span = self._convert_span(span, trace_id)
            jaeger_spans.append(jaeger_span)

        # Build process info
        processes = {
            "p1": {
                "serviceName": self.service_name,
                "tags": [
                    {"key": "trace_type", "type": "string", "value": trace_data.get("trace_type", "")},
                    {"key": "agent", "type": "string", "value": trace_data.get("metadata", {}).get("agent", "unknown")},
                ]
            }
        }

        # Build Jaeger trace
        jaeger_trace = {
            "traceID": trace_id,
            "spans": jaeger_spans,
            "processes": processes,
            "warnings": None
        }

        return {"data": [jaeger_trace]}

    def _convert_span(self, span: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """Convert a single span to Jaeger format.

        Args:
            span: Span dict from agent_tracer
            trace_id: Jaeger-formatted trace ID

        Returns:
            Jaeger-formatted span dict
        """
        span_id = self._format_span_id(span["span_id"])
        start_time = self._to_microseconds(span["start_time"])
        duration = span.get("duration_ms", 0) * 1000  # Convert ms to microseconds

        # Build references (parent span)
        references = []
        if span.get("parent_span_id"):
            parent_id = self._format_span_id(span["parent_span_id"])
            references.append({
                "refType": "CHILD_OF",
                "traceID": trace_id,
                "spanID": parent_id
            })

        # Build tags
        tags = [
            {"key": "span.kind", "type": "string", "value": span.get("type", "internal")},
            {"key": "status", "type": "string", "value": span.get("status", "completed")},
        ]

        # Add agent metadata as tags
        for key, value in span.get("agent_metadata", {}).items():
            tags.append({
                "key": f"agent.{key}",
                "type": "string",
                "value": str(value)
            })

        # Add error info if failed
        if span.get("status") == "failed" and span.get("error"):
            tags.append({
                "key": "error",
                "type": "bool",
                "value": True
            })
            tags.append({
                "key": "error.message",
                "type": "string",
                "value": span["error"].get("message", "")
            })
            tags.append({
                "key": "error.type",
                "type": "string",
                "value": span["error"].get("type", "")
            })

        # Build logs from steps and artifacts
        logs = []

        # Add steps as logs
        for step in span.get("steps", []):
            log_entry = {
                "timestamp": self._to_microseconds(step.get("start_time", span["start_time"])),
                "fields": [
                    {"key": "event", "type": "string", "value": f"step: {step.get('name', 'unknown')}"},
                    {"key": "step_type", "type": "string", "value": step.get("step_type", "")},
                    {"key": "status", "type": "string", "value": step.get("status", "")},
                ]
            }

            # Add step output if present
            if step.get("output"):
                log_entry["fields"].append({
                    "key": "output",
                    "type": "string",
                    "value": json.dumps(step["output"])[:500]  # Truncate long outputs
                })

            logs.append(log_entry)

        # Add artifacts as logs
        for artifact in span.get("artifacts", []):
            log_entry = {
                "timestamp": self._to_microseconds(artifact.get("created_at", span["start_time"])),
                "fields": [
                    {"key": "event", "type": "string", "value": f"artifact: {artifact.get('name', 'unknown')}"},
                    {"key": "artifact_type", "type": "string", "value": artifact.get("artifact_type", "")},
                    {"key": "content_type", "type": "string", "value": artifact.get("content_type", "")},
                ]
            }
            logs.append(log_entry)

        # Build Jaeger span
        jaeger_span = {
            "traceID": trace_id,
            "spanID": span_id,
            "operationName": span.get("name", "unknown"),
            "references": references,
            "startTime": start_time,
            "duration": duration,
            "tags": tags,
            "logs": logs,
            "processID": "p1"
        }

        return jaeger_span

    def _format_trace_id(self, trace_id: str) -> str:
        """Convert trace_id to Jaeger format (16-byte hex string).

        Args:
            trace_id: Original trace ID (e.g., "trace_uuid")

        Returns:
            32-character hex string for Jaeger
        """
        # Hash the trace_id to get consistent 16-byte hex
        hash_obj = hashlib.md5(trace_id.encode())
        return hash_obj.hexdigest()

    def _format_span_id(self, span_id: str) -> str:
        """Convert span_id to Jaeger format (8-byte hex string).

        Args:
            span_id: Original span ID (e.g., "span_abc123")

        Returns:
            16-character hex string for Jaeger
        """
        # Hash the span_id to get consistent 8-byte hex
        hash_obj = hashlib.md5(span_id.encode())
        return hash_obj.hexdigest()[:16]

    def _to_microseconds(self, timestamp: str) -> int:
        """Convert ISO timestamp to microseconds since epoch.

        Args:
            timestamp: ISO 8601 timestamp string

        Returns:
            Microseconds since Unix epoch
        """
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return int(dt.timestamp() * 1_000_000)

    def export_file(self, input_path: str, output_path: str) -> None:
        """Export a trace file to Jaeger format.

        Args:
            input_path: Path to agent_tracer trace.json file
            output_path: Path to write Jaeger JSON file
        """
        # Read trace file
        with open(input_path, 'r') as f:
            trace_data = json.load(f)

        # Convert to Jaeger format
        jaeger_data = self.convert_trace(trace_data)

        # Write Jaeger file
        with open(output_path, 'w') as f:
            json.dump(jaeger_data, f, indent=2)

        print(f"✓ Exported trace to Jaeger format: {output_path}")

    def export_directory(self, traces_dir: str, output_dir: str) -> None:
        """Export all traces in a directory to Jaeger format.

        Args:
            traces_dir: Directory containing trace subdirectories
            output_dir: Directory to write Jaeger JSON files
        """
        traces_path = Path(traces_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Find all trace.json files
        trace_files = list(traces_path.glob("*/trace.json"))

        if not trace_files:
            print(f"⚠️  No trace files found in {traces_dir}")
            return

        print(f"Found {len(trace_files)} trace(s) to export...")

        for trace_file in trace_files:
            trace_id = trace_file.parent.name
            output_file = output_path / f"{trace_id}.jaeger.json"
            self.export_file(str(trace_file), str(output_file))

        print(f"\n✓ Exported {len(trace_files)} trace(s) to {output_dir}")

    def send_to_jaeger(self, trace_data: Dict[str, Any],
                       collector_url: str = "http://localhost:14268/api/traces") -> bool:
        """Send trace directly to Jaeger collector via HTTP.

        Args:
            trace_data: Trace dict from agent_tracer
            collector_url: Jaeger collector endpoint (default: http://localhost:14268/api/traces)

        Returns:
            True if successful, False otherwise
        """
        try:
            jaeger_data = self.convert_trace(trace_data)

            # Jaeger expects the trace in a specific format
            response = requests.post(
                collector_url,
                json=jaeger_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 202:
                print(f"✓ Trace sent to Jaeger: {collector_url}")
                return True
            else:
                print(f"✗ Failed to send trace to Jaeger: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"✗ Could not connect to Jaeger at {collector_url}")
            print("  Make sure Jaeger is running (docker run -d -p 14268:14268 jaegertracing/all-in-one:latest)")
            return False
        except Exception as e:
            print(f"✗ Error sending trace to Jaeger: {e}")
            return False
