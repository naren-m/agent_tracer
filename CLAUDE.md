# agent-tracer

Universal tracing library for AI agent systems. Captures execution flows, LLM decisions, and artifacts.

## What This Package Does

agent-tracer adds observability to any AI agent. It records what your agent did, why it made each decision, and what data it produced -- stored as structured JSON files and optionally in PostgreSQL.

**Use this when you need to:** trace agent execution, capture LLM reasoning, debug agent behavior, export traces to Jaeger/Zipkin, or build audit trails for agent systems.

## Project Layout

```
agent_tracer/
  __init__.py            # Public API (all main imports)
  pyproject.toml         # Package config, dependencies, extras
  core/
    trace_client.py      # TraceClient - main entry point for tracing
    schemas.py           # Pydantic models: Trace, Span, Step, Artifact
    utils.py             # Datetime helpers
  decorators/
    agent.py             # @traced_agent - class decorator for agents
    llm.py               # @traced_llm_call - method decorator for LLM calls
    function.py          # @traced_function - decorator for async functions
    tool.py              # @traced_tool - decorator for tool executions
  models/
    decisions.py         # AgentDecision, DecisionCriteria, LLMContext
  context/
    capture.py           # LLMContextCaptureMixin
    propagation.py       # Trace ID and span stack via contextvars
  utils/
    fail_safe.py         # FailSafeTraceClient wrapper
  storage/
    storage_backend.py   # TraceStorageBackend (PostgreSQL + disk)
    schema.sql           # PostgreSQL schema
  integrations/
    langchain.py         # LangChain/LangGraph callback handler
    exporters/
      zipkin.py          # ZipkinExporter
      jaeger.py          # JaegerExporter
  examples/              # Demo scripts (runnable)
  tests/                 # pytest suite (68+ tests)
```

## How to Install

```bash
pip install -e ".[dev]"          # Development (with test deps)
pip install agent-tracer         # Core only
pip install agent-tracer[all]    # All optional deps
```

## How to Run Tests

```bash
pytest -v                        # All tests
pytest tests/unit/ -v            # Unit tests only
pytest --cov=agent_tracer        # With coverage
```

## Public API

Everything below is importable from `agent_tracer` directly:

### Core
- `TraceClient` - Start/complete traces, create spans, add steps/artifacts/decisions
- `Trace`, `Span`, `Step`, `Artifact` - Pydantic data models
- `TriggerInfo`, `TraceSummary`, `StorageInfo`, `AgentMetadata` - Supporting models

### Decorators
- `@traced_agent(client, fail_safe=True)` - Wraps agent class, traces `run()` method
- `@traced_llm_call(client)` - Traces LLM calls with context capture
- `@traced_function(client)` - Traces any async function as a span
- `@traced_tool(client)` - Traces tool executions with input/output

### Decision Models
- `AgentDecision` - Structured decision: action, reasoning, confidence, criteria, alternatives
- `DecisionCriteria` - Single evaluation factor with score (0-1) and weight (0-1)
- `LLMContext` - Pre-call context: model, temperature, messages, token count

### Context Management
- `set_current_trace_id(id)` / `get_current_trace_id()` - Async-safe trace ID via contextvars
- `push_span(id)` / `pop_span()` / `get_current_span()` / `get_span_stack()` - Span nesting
- `LLMContextCaptureMixin` - Mixin for auto-capturing LLM context before calls

### Utilities
- `FailSafeTraceClient` - Wraps TraceClient so tracing errors never crash the agent

### Storage
- `TraceStorageBackend(db_conn, storage_dir)` - PostgreSQL + disk storage
- `TraceStorageBackend(db_conn=None, storage_dir="./traces")` - File-only mode (no DB needed)

### Integrations (optional extras)
- `agent_tracer.integrations.ComprehensiveTracingCallback` - LangChain/LangGraph (requires `[langchain]`)
- `agent_tracer.integrations.exporters.ZipkinExporter` - Zipkin format (requires `[exporters]`)
- `agent_tracer.integrations.exporters.JaegerExporter` - Jaeger format (requires `[exporters]`)

## Quick Usage Pattern

```python
from agent_tracer import TraceClient, traced_agent, traced_llm_call
from agent_tracer.models import AgentDecision, DecisionCriteria
from agent_tracer.context import LLMContextCaptureMixin
from agent_tracer.storage import TraceStorageBackend

# 1. Set up storage and client
storage = TraceStorageBackend(db_conn=None, storage_dir="./traces")
client = TraceClient(storage)

# 2. Decorate your agent
@traced_agent(client, fail_safe=True)
class MyAgent(LLMContextCaptureMixin):
    @traced_llm_call(client)
    async def call_llm(self, prompt: str) -> AgentDecision:
        # Your LLM call here
        return AgentDecision(
            action="chosen_action",
            reasoning="Why this was chosen",
            confidence=0.85,
            alternatives_considered=["other_option"],
            criteria=[DecisionCriteria(factor="relevance", score=0.9, weight=0.5)],
            context_used={"key": "value"}
        )

    async def run(self, task: dict):
        decision = await self.call_llm(prompt=task["description"])
        return {"status": "completed", "action": decision.action}

# 3. Traces are written automatically to ./traces/
```

## Key Design Decisions

- **Async-first**: All decorators wrap async functions. Use `asyncio.run()` for sync entry points.
- **Pydantic v2**: All data models use Pydantic v2 with strict validation.
- **contextvars**: Trace ID and span stack propagation is thread-safe and async-safe.
- **Fail-safe by default**: Set `fail_safe=True` on decorators so tracing never breaks the agent.
- **File-only mode**: Pass `db_conn=None` to skip PostgreSQL entirely. Traces go to `{storage_dir}/{trace_id}/trace.json`.
- **Optional dependencies**: Core has minimal deps. LLM clients, LangChain, and exporters are optional extras.

## Common Tasks

### Adding a new decorator
Add to `decorators/`, follow the pattern in `decorators/agent.py`. Register in `decorators/__init__.py` and `__init__.py`.

### Adding a new integration
Add to `integrations/`. If it needs a new optional dependency, add to `pyproject.toml` under `[project.optional-dependencies]`.

### Adding a new model
Add to `models/decisions.py` or create a new file in `models/`. Register in `models/__init__.py` and `__init__.py`.

### Using in another project
```python
pip install agent-tracer
```
Then import from `agent_tracer`. See the Quick Usage Pattern above.
