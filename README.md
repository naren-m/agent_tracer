# agent-tracer

Universal tracing library for AI agent systems with LLM decision capture.

**Version**: 0.2.0 | **Python**: >= 3.11 | **License**: MIT

agent-tracer provides hierarchical tracing for any AI agent system -- RCA, monitoring, CI/CD, orchestration, or custom agents. It captures execution flows, LLM decisions with reasoning and criteria, and artifacts, storing everything in PostgreSQL and/or JSON files on disk.

v0.2.0 merges the original `agent-tracer` core (v0.1.0) with the `a2a-traced` decorator library (v1.0.1) into a single unified package.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Features](#features)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Integrations](#integrations)
- [Configuration](#configuration)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

### Core package

```bash
pip install agent-tracer
```

### Optional extras

```bash
pip install agent-tracer[llm]         # Anthropic + OpenAI client libraries
pip install agent-tracer[langchain]   # LangChain/LangGraph integration
pip install agent-tracer[exporters]   # Zipkin and Jaeger exporters
pip install agent-tracer[all]         # All optional dependencies
```

### Development

```bash
pip install -e ".[dev]"
```

Or using Make:

```bash
make setup          # Create venv, install dependencies
make install-dev    # Install with dev extras
make test           # Run test suite
```

---

## Quick Start

### 1. Basic tracing with TraceClient

```python
from agent_tracer import TraceClient
from agent_tracer.storage import TraceStorageBackend

# File-only storage (no PostgreSQL required)
storage = TraceStorageBackend(db_conn=None, storage_dir="./traces")
client = TraceClient(storage)

# Start a trace
trace_id = client.start_trace(
    trigger_type="manual",
    triggered_by="user@example.com",
    metadata={"purpose": "debugging", "environment": "production"}
)

# Create spans with steps and artifacts
with client.span("analysis_phase", "agent_execution") as span:
    client.add_step(
        name="load_data",
        step_type="data_fetch",
        input_data={"source": "database"},
        output_data={"records": 100}
    )

    client.add_artifact(
        name="analysis_result",
        artifact_type="report",
        content={"findings": ["issue1", "issue2"]}
    )

    client.add_decision(
        name="root_cause_identified",
        reasoning="Multiple error patterns converge on config drift",
        criteria=["frequency", "impact", "correlation"],
        final_score=0.92
    )

# Finalize the trace
client.complete_trace(
    status="completed",
    summary={"total_issues": 2, "severity": "high"}
)
```

### 2. Decorator-based tracing

```python
import asyncio
from agent_tracer import TraceClient, traced_agent, traced_llm_call
from agent_tracer.models import AgentDecision, DecisionCriteria, LLMContext
from agent_tracer.context import LLMContextCaptureMixin
from agent_tracer.storage import TraceStorageBackend

storage = TraceStorageBackend(db_conn=None, storage_dir="./traces")
trace_client = TraceClient(storage)

@traced_agent(trace_client, fail_safe=True)
class TaskPlannerAgent(LLMContextCaptureMixin):

    @traced_llm_call(trace_client)
    async def call_llm(self, prompt: str) -> AgentDecision:
        # Your LLM call here -- returns a structured decision
        return AgentDecision(
            action="create_subtasks",
            reasoning="Task is complex, parallel execution improves efficiency",
            confidence=0.87,
            alternatives_considered=["execute_sequentially", "delegate"],
            criteria=[
                DecisionCriteria(factor="complexity", score=0.9, weight=0.4),
                DecisionCriteria(factor="time_constraints", score=0.8, weight=0.3),
            ],
            context_used={"task": "implement auth"}
        )

    async def run(self, task: dict):
        decision = await self.call_llm(prompt=f"Plan: {task['description']}")
        return {"status": "completed", "action": decision.action}

# Tracing happens automatically
asyncio.run(TaskPlannerAgent().run({"description": "Implement auth", "sender": "system"}))
```

### 3. Fail-safe mode

Tracing errors never break your agent:

```python
from agent_tracer.utils import FailSafeTraceClient

safe_client = FailSafeTraceClient(trace_client)

# If tracing fails (e.g., storage unavailable), the agent continues normally.
# Failures are logged and the client stops retrying for the current trace.
safe_client.start_trace(...)
```

---

## Features

### Hierarchical Tracing

Trace -> Span -> Step -> Artifact. Spans nest via parent/child relationships. Steps record individual actions. Artifacts attach data of any size (small data inline, large data on disk with preview).

### Decision Capture

Record agent reasoning with structured `AgentDecision` models that include the chosen action, confidence score, evaluation criteria with weights, alternatives considered, and the context used.

### Decorator Suite

- `@traced_agent(client)` -- Wraps an agent class. Automatically traces the `run()` method, captures context, and extracts decisions from `AgentDecision` return values.
- `@traced_llm_call(client)` -- Traces LLM calls with pre-call context capture (via `LLMContextCaptureMixin`) and post-call decision extraction.
- `@traced_function(client)` -- Traces any async function as a span.
- `@traced_tool(client)` -- Traces tool executions with input/output logging.

### Context Propagation

Thread-safe and async-safe trace context via `contextvars`:

```python
from agent_tracer.context import get_current_trace_id, set_current_trace_id

set_current_trace_id("trace_abc123")
print(get_current_trace_id())  # "trace_abc123"
```

Span stack management for nested hierarchies:

```python
from agent_tracer.context import push_span, pop_span, get_current_span, get_span_stack

push_span("span_outer")
push_span("span_inner")
print(get_current_span())  # "span_inner"
print(get_span_stack())    # ["span_outer", "span_inner"]
pop_span()                 # returns "span_inner"
```

### LLM Context Capture

Mix `LLMContextCaptureMixin` into your agent class to automatically capture model name, temperature, messages, estimated token count, available tools, and agent state before each LLM call.

### Dual Storage

- **PostgreSQL**: Trace and span metadata stored in JSONB columns for flexible querying.
- **Disk**: Full trace JSON written to `{storage_dir}/{trace_id}/trace.json`. Large artifacts stored as individual files.
- **File-only mode**: Pass `db_conn=None` to skip PostgreSQL entirely.

### Trace Export

Export traces to Zipkin or Jaeger format for visualization in distributed tracing UIs:

```python
from agent_tracer.integrations.exporters import ZipkinExporter, JaegerExporter

# Zipkin (also works with Jaeger's Zipkin endpoint on port 9411)
zipkin = ZipkinExporter(service_name="my-agent")
zipkin.send_to_jaeger(trace_data)

# Jaeger native format
jaeger = JaegerExporter(service_name="my-agent")
jaeger.export_file("traces/trace_abc/trace.json", "jaeger_output.json")
jaeger.send_to_jaeger(trace_data, "http://localhost:14268/api/traces")
```

### LangChain/LangGraph Integration

Drop-in callback handler that automatically traces node execution, LLM calls, and state transitions:

```python
from agent_tracer.integrations import ComprehensiveTracingCallback

callback = ComprehensiveTracingCallback(trace_client, auto_parse_decisions=True)
# Add to your LangGraph agent's callbacks list
```

The callback captures chain start/end, LLM start/end with prompt and response, and parses LLM responses into `AgentDecision` objects using heuristic text analysis.

---

## Architecture

### Package Structure

```
agent_tracer/
  __init__.py          - Public API re-exports
  core/
    trace_client.py    - TraceClient: start/complete traces, spans, steps, artifacts
    schemas.py         - Pydantic models: Trace, Span, Step, Artifact, TriggerInfo
    utils.py           - Datetime helpers
  decorators/
    agent.py           - @traced_agent class decorator
    llm.py             - @traced_llm_call method decorator
    function.py        - @traced_function decorator
    tool.py            - @traced_tool decorator
  models/
    decisions.py       - AgentDecision, DecisionCriteria, LLMContext
  context/
    capture.py         - LLMContextCaptureMixin
    propagation.py     - get/set_current_trace_id, span stack (contextvars)
  utils/
    fail_safe.py       - FailSafeTraceClient wrapper
  storage/
    storage_backend.py - TraceStorageBackend (PostgreSQL + disk)
  integrations/
    langchain.py       - ComprehensiveTracingCallback
    exporters/
      zipkin.py        - ZipkinExporter
      jaeger.py        - JaegerExporter
```

### Data Model

```
Trace
  |-- trace_id, trace_type, status, trigger, metadata, summary
  |-- created_at, completed_at, duration_ms
  |
  +-- Span (1..N)
        |-- span_id, parent_span_id, name, type, status
        |-- start_time, end_time, duration_ms, agent_metadata
        |
        +-- Step (0..N)
        |     |-- step_id, step_type, name, status
        |     |-- input, output, decision_logic
        |
        +-- Artifact (0..N)
              |-- artifact_id, name, artifact_type, content_type
              |-- storage (inline or external_ref), content, preview
```

### Core Schemas (Pydantic v2)

| Model | Purpose |
|-------|---------|
| `Trace` | Top-level execution container |
| `Span` | Execution phase or agent activity |
| `Step` | Individual action within a span |
| `Artifact` | Data/files attached to spans |
| `TriggerInfo` | What initiated the trace |
| `TraceSummary` | Summary metrics (total/failed spans) |
| `AgentMetadata` | Agent-specific span metadata |
| `StorageInfo` | Artifact storage location and size |
| `AgentDecision` | Structured decision with reasoning and criteria |
| `DecisionCriteria` | Single evaluation factor with score and weight |
| `LLMContext` | Pre-call context (model, temperature, messages, tools) |

---

## API Reference

### TraceClient

```python
client = TraceClient(storage_backend)

# Lifecycle
trace_id = client.start_trace(trigger_type, triggered_by, metadata, trace_type="agent_execution")
client.complete_trace(status, summary)

# Spans (context manager)
with client.span(name, span_type, agent_metadata=None) as span_data:
    ...

# Steps and artifacts
client.add_step(name, step_type, input_data, output_data)
client.add_artifact(name, artifact_type, content, metadata=None)
client.add_decision(name, reasoning, criteria, final_score)
```

### Decorators

```python
@traced_agent(trace_client, fail_safe=True)       # Class decorator for agents
@traced_llm_call(trace_client, fail_safe=True)     # Method decorator for LLM calls
@traced_function(trace_client, span_name=None)     # Decorator for async functions
@traced_tool(trace_client)                         # Decorator for tool executions
```

### Context Propagation

```python
set_current_trace_id(trace_id)        # Set trace ID in current async context
get_current_trace_id() -> str | None  # Get trace ID from current context

push_span(span_id)                    # Push span onto stack
pop_span() -> str | None              # Pop span from stack
get_current_span() -> str | None      # Peek at top span
get_span_stack() -> list[str]         # Get full span hierarchy
```

### Imports

```python
# Top-level (most common)
from agent_tracer import (
    TraceClient, traced_agent, traced_llm_call,
    AgentDecision, DecisionCriteria, LLMContext,
    FailSafeTraceClient,
)

# Sub-modules
from agent_tracer.decorators import traced_function, traced_tool
from agent_tracer.models import AgentDecision, DecisionCriteria, LLMContext
from agent_tracer.context import LLMContextCaptureMixin, get_current_trace_id
from agent_tracer.storage import TraceStorageBackend, TraceNotFoundError
from agent_tracer.utils import FailSafeTraceClient
from agent_tracer.integrations import ComprehensiveTracingCallback
from agent_tracer.integrations.exporters import ZipkinExporter, JaegerExporter
```

---

## Integrations

### LangChain / LangGraph

Requires the `langchain` extra:

```bash
pip install agent-tracer[langchain]
```

```python
from agent_tracer.integrations import ComprehensiveTracingCallback

callback = ComprehensiveTracingCallback(
    trace_client,
    auto_parse_decisions=True,  # Parse LLM text into AgentDecision
    fail_safe=True,             # Never crash the agent
)

# The @traced_agent decorator auto-injects this callback when it detects
# a LangGraph agent (one with a `callbacks` list attribute).
```

### Zipkin / Jaeger

Requires the `exporters` extra:

```bash
pip install agent-tracer[exporters]
```

**Zipkin** (also ingested by Jaeger on port 9411):

```python
from agent_tracer.integrations.exporters import ZipkinExporter

exporter = ZipkinExporter(service_name="my-agent")
exporter.send_to_jaeger(trace_data, zipkin_url="http://localhost:9411/api/v2/spans")
```

**Jaeger** (native format via collector on port 14268):

```python
from agent_tracer.integrations.exporters import JaegerExporter

exporter = JaegerExporter(service_name="my-agent")

# Export to file
exporter.export_file("traces/trace_abc/trace.json", "output.jaeger.json")

# Export entire directory
exporter.export_directory("./traces", "./jaeger_output")

# Send directly to Jaeger collector
exporter.send_to_jaeger(trace_data, "http://localhost:14268/api/traces")
```

---

## Configuration

### Storage Setup

**File-only** (no database required):

```python
storage = TraceStorageBackend(db_conn=None, storage_dir="./traces")
```

**PostgreSQL + file**:

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="agent_traces", user="tracer", password="secret"
)
storage = TraceStorageBackend(db_conn=conn, storage_dir="./traces")
```

### PostgreSQL Schema

The storage backend expects two tables:

```sql
CREATE TABLE agent_tracer_traces (
    trace_id        TEXT PRIMARY KEY,
    trace_type      TEXT,
    status          TEXT,
    trigger_type    TEXT,
    trigger_source  TEXT,
    triggered_by    TEXT,
    triggered_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    duration_ms     INTEGER,
    total_spans     INTEGER,
    failed_spans    INTEGER,
    summary_metrics JSONB,
    metadata        JSONB,
    trace_document_url TEXT
);

CREATE TABLE agent_tracer_spans (
    span_id         TEXT PRIMARY KEY,
    trace_id        TEXT REFERENCES agent_tracer_traces(trace_id),
    parent_span_id  TEXT,
    name            TEXT,
    span_type       TEXT,
    status          TEXT,
    start_time      TIMESTAMPTZ,
    end_time        TIMESTAMPTZ,
    duration_ms     INTEGER,
    agent_metadata  JSONB
);
```

### Artifact Storage

- Artifacts smaller than 10 KB are stored inline as JSON within the trace.
- Larger artifacts are written to `{storage_dir}/{trace_id}/artifacts/{artifact_id}.txt` with a 500-character preview kept inline.

---

## Testing

```bash
# Run all tests
make test

# Or directly with pytest
pytest -v

# With coverage
pytest --cov=agent_tracer --cov-report=term-missing

# Unit tests only
pytest tests/unit/ -v
```

Test configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`.

---

## Contributing

1. Fork the repository and create a feature branch.
2. Install development dependencies: `pip install -e ".[dev]"`
3. Write tests for any new functionality.
4. Run the test suite: `make test`
5. Submit a pull request.

### Code Style

- Type hints on all public APIs.
- Docstrings on all public classes and functions.
- Pydantic v2 models for data validation.
- Async-first decorator design (all decorators wrap async functions).

### Dependencies

Core: `pydantic>=2.0.0`, `psycopg2-binary>=2.9.9`, `python-dateutil>=2.8.0`

Optional: `anthropic`, `openai`, `langchain-core`, `requests`

Dev: `pytest`, `pytest-asyncio`, `pytest-cov`, `rich`

---

## License

MIT License. See [LICENSE](LICENSE) for details.
