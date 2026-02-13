# Getting Started with Agent Tracer

**Quick start guide to get you up and running with Agent Tracer in under 5 minutes!**

## What is Agent Tracer?

Agent Tracer is a universal tracing library for AI agent systems. It helps you:

- 📊 **Track agent execution** - Capture every step, decision, and artifact
- 🔍 **Debug effectively** - Understand what your agent did and why
- 📈 **Analyze performance** - Measure and optimize agent behavior
- 🗄️ **Store traces** - PostgreSQL + file system for flexible querying

## Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.11+** installed
- ✅ **PostgreSQL 14+** (optional but recommended)
- ✅ **5 minutes** of your time

## Installation

### Step 1: Install Agent Tracer

```bash
# Clone or navigate to the agent_tracer directory
cd agent_proj

# Install the library
pip install -e .
```

### Step 2: Install Dependencies

```bash
pip install psycopg2-binary pydantic python-dateutil
```

### Step 3: Setup Database (Optional)

If you want to store traces in PostgreSQL:

```bash
# Install PostgreSQL (if not already installed)
# macOS:
brew install postgresql@14
brew services start postgresql@14

# Ubuntu/Debian:
sudo apt-get install postgresql-14
sudo systemctl start postgresql

# Create the database
python examples/setup_database.py localhost agent_tracer_db postgres postgres
```

> **Note**: The demo works without PostgreSQL too! Traces will be saved to the file system only.

## Your First Trace

### Run the Demo

```bash
python getting_started_demo.py
```

You should see output like:

```
======================================================================
  🚀 Agent Tracer - Getting Started Demo
======================================================================
▸ Initializing Agent Tracer...
▸ Setting up database connection...
  ▸ PostgreSQL connection successful ✓
  ▸ Storage initialized: /tmp/agent_tracer_demo_xxxxx
  ▸ Trace client ready ✓
  ▸ Agent initialized ✓

======================================================================
  📊 Starting Agent Tracer
======================================================================
📌 Trace ID: trace_abc123...

======================================================================
  🤖 Running Agent Workflow
======================================================================
🎯 Processing task: 'Classify user feedback sentiment'
🔍 Analyzing problem...
  ▸ Analysis complete ✓
🤔 Making decision...
  ▸ Decision: proceed_with_confidence ✓
⚡ Executing action...
  ▸ Execution complete ✓

======================================================================
  ✅ Demo Complete!
======================================================================

📋 Results:
  Status: success
  Actions Completed: 3
  Output: Task completed successfully with high confidence

📊 Trace Information:
  Trace ID: trace_abc123
  Storage Location: /tmp/agent_tracer_demo_xxxxx/trace_abc123

🔍 View Your Trace:
  1. File: cat /tmp/agent_tracer_demo_xxxxx/trace_abc123/trace.json
  2. Database: SELECT * FROM agent_tracers WHERE trace_id = 'trace_abc123';
```

### Understanding the Output

The demo shows a complete agent workflow with tracing:

1. **Initialization** - Setup storage and trace client
2. **Start Trace** - Begin tracking with metadata
3. **Agent Workflow** - Execute with nested spans:
   - Problem Analysis
   - Decision Making
   - Action Execution
4. **Complete Trace** - Finalize with status and summary

## Key Concepts

### 1. Trace Structure

```
Trace (trace_abc123)
│
├── Span: Simple Agent Workflow (agent)
│   │
│   ├── Span: Problem Analysis (analysis)
│   │   ├── Step: Analyze Problem Statement
│   │   └── Artifact: Analysis Results
│   │
│   ├── Span: Decision Making (decision)
│   │   └── Decision: Action Selection
│   │       ├── Reasoning
│   │       ├── Criteria (complexity, confidence)
│   │       └── Final Score
│   │
│   └── Span: Action Execution (execution)
│       ├── Step: Execute: gather_data
│       ├── Step: Execute: process
│       ├── Step: Execute: validate
│       └── Artifact: Execution Results
```

### 2. Core Components

**Trace** - Top-level container for an agent execution
```python
trace_id = client.start_trace(
    trigger_type="user_request",  # What initiated this?
    triggered_by="api_endpoint",  # Which system?
    metadata={"user_id": "123"}   # Custom data
)
```

**Span** - A logical unit of work (phase, agent, action)
```python
with client.span("My Agent", "agent"):
    # Your agent code here
    pass
```

**Step** - An individual operation within a span
```python
client.add_step(
    name="Fetch Data",
    step_type="processing",
    input_data={"query": "SELECT * FROM users"},
    output_data={"rows": 100, "status": "completed"}
)
```

**Decision** - A decision point with reasoning
```python
client.add_decision(
    name="Route Selection",
    reasoning="Selected fast path based on load. Decision: fast_path",
    criteria=[{"factor": "load", "score": 0.8, "weight": 1.0}],
    final_score=0.8
)
```

**Artifact** - Output or data produced
```python
client.add_artifact(
    name="Analysis Results",
    artifact_type="analysis",
    content=results  # Can be dict, list, or string
)
```

## Customize Your Own Agent

### Basic Template

```python
from agent_tracer import TraceClient
from agent_tracer.storage import TraceStorageBackend
import psycopg2

# Setup
db_conn = psycopg2.connect(...)  # or None for file-only
storage = TraceStorageBackend(db_conn, "/tmp/traces")
client = TraceClient(storage)

# Start trace
trace_id = client.start_trace(
    trigger_type="your_trigger",
    triggered_by="your_system",
    metadata={"custom": "data"}
)

# Your agent logic
with client.span("Your Agent", "agent"):
    # Step 1: Analyze
    client.add_step(
        name="Analyze Input",
        step_type="processing",
        input_data={"raw_input": "user data"},
        output_data={"status": "completed", "result": "analyzed"}
    )

    # Step 2: Decide
    client.add_decision(
        name="Action Selection",
        reasoning="Your reasoning here",
        criteria=[{"factor": "confidence", "score": 0.9, "weight": 1.0}],
        final_score=0.9
    )

    # Step 3: Execute
    with client.span("Execute Action", "action"):
        # Your action code
        result = do_something()

    # Store result
    client.add_artifact(
        name="Result",
        artifact_type="output",
        content=result  # Can be dict, list, or string
    )

# Complete
client.complete_trace(status="completed", summary={"result": result})
```

## Testing Your Setup

### Test 1: File System Storage

```bash
# Run without database
python getting_started_demo.py

# Check the trace file
ls /tmp/agent_tracer_demo_*
cat /tmp/agent_tracer_demo_*/trace_*/trace.json
```

### Test 2: Database Storage

```bash
# Run with database
python getting_started_demo.py

# Query the database
psql -U postgres -d agent_tracer_db -c "SELECT trace_id, status, created_at FROM agent_tracers ORDER BY created_at DESC LIMIT 5;"
```

### Test 3: Query Traces

```python
from agent_tracer.storage import TraceStorageBackend
import psycopg2

db_conn = psycopg2.connect(
    dbname="agent_tracer_db",
    user="postgres",
    password="postgres",
    host="localhost"
)

storage = TraceStorageBackend(db_conn, "/tmp/traces")

# Find traces by metadata
traces = storage.query_traces_by_metadata("purpose", "getting_started_example")

for trace in traces:
    print(f"Trace: {trace['trace_id']}")
    print(f"Status: {trace['status']}")
    print(f"Created: {trace['created_at']}")
```

## Next Steps

### 1. Explore Examples

```bash
cd examples
python ollama_agent.py  # Full AI agent with LLM integration
```

See [examples/README.md](examples/README.md) for details.

### 2. Read Documentation

- [Quickstart Guide](docs/QUICKSTART.md) - Detailed tutorial
- [Use Cases](docs/USE_CASES.md) - Real-world examples
- [API Reference](docs/API.md) - Complete API documentation

### 3. Build Your Agent

Use the demo as a template:

1. **Copy** `getting_started_demo.py` to your project
2. **Modify** the `SimpleAgent` class with your logic
3. **Add** your own spans, steps, decisions, and artifacts
4. **Run** and analyze your traces!

## Troubleshooting

### Import Error

```
ImportError: No module named 'agent_tracer'
```

**Solution**: Install the library
```bash
pip install -e .
```

### Database Connection Failed

```
psycopg2.OperationalError: could not connect to server
```

**Solution**: Start PostgreSQL or run without database
```bash
# macOS
brew services start postgresql@14

# Ubuntu/Debian
sudo systemctl start postgresql

# Or just run without database - traces will be file-only
```

### Permission Denied on Storage Directory

```
PermissionError: [Errno 13] Permission denied: '/tmp/agent_tracers'
```

**Solution**: Create directory with proper permissions
```bash
mkdir -p /tmp/agent_tracers
chmod 755 /tmp/agent_tracers
```

### Module Not Found

```
ModuleNotFoundError: No module named 'pydantic'
```

**Solution**: Install dependencies
```bash
pip install psycopg2-binary pydantic python-dateutil
```

## Common Patterns

### Pattern 1: Multi-Phase Agent

```python
with client.span("Multi-Phase Agent", "agent"):
    # Phase 1
    with client.span("Planning", "phase"):
        plan = create_plan()
        client.add_artifact("Plan", "plan", "application/json", plan)

    # Phase 2
    with client.span("Execution", "phase"):
        result = execute_plan(plan)
        client.add_artifact("Result", "output", "text/plain", result)
```

### Pattern 2: Decision with Multiple Criteria

```python
client.add_decision(
    name="Strategy Selection",
    reasoning="Chose strategy based on multiple factors",
    criteria=[
        {"factor": "performance", "score": 0.9, "weight": 0.4},
        {"factor": "cost", "score": 0.7, "weight": 0.3},
        {"factor": "reliability", "score": 0.85, "weight": 0.3}
    ],
    final_score=0.83,  # Weighted average
    outcome="optimized_strategy"
)
```

### Pattern 3: Error Handling

```python
try:
    with client.span("Risky Operation", "execution"):
        result = risky_operation()
        client.add_step("Success", "processing", "completed")
        client.complete_trace(status="completed", summary={"result": result})
except Exception as e:
    client.add_step("Error", "error", "failed", metadata={"error": str(e)})
    client.complete_trace(status="failed", summary={"error": str(e)})
    raise
```

## FAQ

**Q: Do I need PostgreSQL?**
A: No, traces can be stored in the file system only. PostgreSQL is optional but recommended for querying.

**Q: Can I use this with any agent framework?**
A: Yes! Agent Tracer is framework-agnostic. Use it with LangChain, LlamaIndex, custom agents, or any system.

**Q: How much overhead does tracing add?**
A: Minimal - typically <5ms per operation. Storage is async and non-blocking.

**Q: Can I deploy this in production?**
A: Yes! The library is designed for production use with proper error handling and performance.

**Q: How do I query traces programmatically?**
A: Use the storage API or direct SQL queries on the PostgreSQL database.

**Q: Can I customize the metadata structure?**
A: Absolutely! Store any JSON-serializable data in the metadata field.

## Support

- 📖 [Documentation](docs/)
- 💬 [GitHub Issues](https://github.com/your-repo/agent_tracer/issues)
- 📧 Email: support@example.com

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**Ready to build amazing traced agents?** 🚀

Start with `python getting_started_demo.py` and explore the examples!
