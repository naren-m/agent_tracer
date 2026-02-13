# Agent Tracer

Universal tracing library for ANY AI agent system - RCA, monitoring, CI/CD, orchestration, or custom agents.

## Features

- **100% Generic** - Zero domain-specific coupling
- **Flexible Metadata** - Any key-value pairs, stored as JSONB
- **Hierarchical Tracing** - Trace → Spans → Steps → Artifacts
- **Decision Capture** - Reasoning, criteria, confidence scores
- **Multi-Use Cases** - Works with RCA, monitoring, CI/CD, and more

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from agent_tracer import TraceClient
from agent_tracer.storage import TraceStorageBackend

# Initialize storage and client
storage = TraceStorageBackend(db_conn, storage_dir="./traces")
client = TraceClient(storage)

# Start a trace
trace_id = client.start_trace(
    trigger_type="manual",
    triggered_by="user@example.com",
    metadata={"purpose": "debugging", "environment": "production"}
)

# Create spans and capture execution
with client.span("analysis_phase", "agent_execution") as span:
    # Add steps
    client.add_step(
        name="load_data",
        step_type="data_fetch",
        input_data={"source": "database"},
        output_data={"records": 100}
    )

    # Add artifacts
    client.add_artifact(
        name="analysis_result",
        artifact_type="report",
        content={"findings": ["issue1", "issue2"]}
    )

    # Capture decisions
    client.add_decision(
        name="root_cause_identified",
        reasoning="Multiple error patterns converge",
        criteria=["frequency", "impact", "correlation"],
        final_score=0.92
    )

# Complete the trace
client.complete_trace(
    status="completed",
    summary={"total_issues": 2, "severity": "high"}
)
```

## Architecture

### Data Model

- **Trace**: Top-level execution container
- **Span**: Execution phase or agent activity
- **Step**: Individual action within a span
- **Artifact**: Files, data, or outputs attached to spans/steps

### Storage

- **Metadata**: PostgreSQL with JSONB for flexible queries
- **Full Traces**: JSON files on disk for complete trace replay
- **Artifacts**: External storage for large files with inline storage for small data

## Use Cases

### RCA (Root Cause Analysis)
Track investigation workflows, capture reasoning, and store evidence.

### Monitoring
Trace agent behaviors, performance metrics, and decision-making processes.

### CI/CD
Monitor build pipelines, deployment steps, and automated testing.

### Custom Agents
Instrument any AI agent system with flexible tracing capabilities.

## Requirements

- Python >= 3.11
- PostgreSQL (for metadata storage)
- Dependencies: pydantic, psycopg2-binary, python-dateutil

## Development

Run tests:

```bash
pytest
```

## License

MIT License - see LICENSE file for details.
