# Migration Guide: a2a-traced to agent-tracer v0.2.0

## Overview

As of agent-tracer v0.2.0, the `a2a-traced` package has been merged into the
unified `agent-tracer` library. All tracing decorators, decision models, context
management utilities, and fail-safe clients that previously lived in `a2a-traced`
are now part of `agent-tracer` directly.

**`a2a-traced` is deprecated.** It will not receive further updates. All existing
functionality is preserved in agent-tracer v0.2.0 with no API changes -- only
import paths have changed.

---

## 1. Installation

Remove the separate `a2a-traced` dependency and install the unified package.

**Before (two packages):**

```bash
pip install agent-tracer a2a-traced
```

**After (single package):**

```bash
# Core tracing only
pip install agent-tracer

# With all optional dependencies (LLM providers, exporters, langchain)
pip install agent-tracer[all]
```

Optional dependency groups available in v0.2.0:

| Extra       | Includes                            |
|-------------|-------------------------------------|
| `llm`       | `anthropic`, `openai`               |
| `langchain` | `langchain-core`                    |
| `exporters` | `requests` (for Jaeger/Zipkin)      |
| `all`       | All of the above                    |
| `dev`       | `pytest`, `pytest-asyncio`, `pytest-cov`, `rich` |

After installing, uninstall the old package:

```bash
pip uninstall a2a-traced
```

---

## 2. Import Path Changes

Every symbol that was previously exported from `a2a_traced` is now available
under `agent_tracer`. The table below lists every affected import.

### Decorators

| Before (a2a-traced)                                          | After (agent-tracer v0.2.0)                                |
|--------------------------------------------------------------|------------------------------------------------------------|
| `from a2a_traced.decorators import traced_agent`             | `from agent_tracer.decorators import traced_agent`         |
| `from a2a_traced.decorators import traced_llm_call`          | `from agent_tracer.decorators import traced_llm_call`      |
| `from a2a_traced.decorators import traced_function`          | `from agent_tracer.decorators import traced_function`      |
| `from a2a_traced.decorators import traced_tool`              | `from agent_tracer.decorators import traced_tool`          |

### Decision Models

| Before (a2a-traced)                                          | After (agent-tracer v0.2.0)                                |
|--------------------------------------------------------------|------------------------------------------------------------|
| `from a2a_traced.decision_models import AgentDecision`       | `from agent_tracer.models import AgentDecision`            |
| `from a2a_traced.decision_models import DecisionCriteria`    | `from agent_tracer.models import DecisionCriteria`         |
| `from a2a_traced.decision_models import LLMContext`          | `from agent_tracer.models import LLMContext`               |

### Context Management

| Before (a2a-traced)                                          | After (agent-tracer v0.2.0)                                |
|--------------------------------------------------------------|------------------------------------------------------------|
| `from a2a_traced.context_capture import LLMContextCaptureMixin` | `from agent_tracer.context import LLMContextCaptureMixin` |
| `from a2a_traced.context_propagation import get_current_trace_id` | `from agent_tracer.context import get_current_trace_id` |
| `from a2a_traced.context_propagation import set_current_trace_id` | `from agent_tracer.context import set_current_trace_id` |

### Utilities

| Before (a2a-traced)                                          | After (agent-tracer v0.2.0)                                |
|--------------------------------------------------------------|------------------------------------------------------------|
| `from a2a_traced.fail_safe import FailSafeTraceClient`       | `from agent_tracer.utils import FailSafeTraceClient`      |

---

## 3. Automated Migration

The following commands will update import paths across your codebase. Run them
from your project root.

### Using find + sed (macOS / BSD sed)

```bash
# Decorators
find . -name '*.py' -exec sed -i '' 's/from a2a_traced\.decorators/from agent_tracer.decorators/g' {} +

# Decision models (module renamed: decision_models -> models)
find . -name '*.py' -exec sed -i '' 's/from a2a_traced\.decision_models/from agent_tracer.models/g' {} +

# Context capture (module renamed: context_capture -> context)
find . -name '*.py' -exec sed -i '' 's/from a2a_traced\.context_capture/from agent_tracer.context/g' {} +

# Context propagation (module renamed: context_propagation -> context)
find . -name '*.py' -exec sed -i '' 's/from a2a_traced\.context_propagation/from agent_tracer.context/g' {} +

# Fail-safe client (module renamed: fail_safe -> utils)
find . -name '*.py' -exec sed -i '' 's/from a2a_traced\.fail_safe/from agent_tracer.utils/g' {} +

# Catch any remaining bare a2a_traced references
find . -name '*.py' -exec sed -i '' 's/import a2a_traced/import agent_tracer/g' {} +
```

### Using find + sed (Linux / GNU sed)

```bash
# Decorators
find . -name '*.py' -exec sed -i 's/from a2a_traced\.decorators/from agent_tracer.decorators/g' {} +

# Decision models
find . -name '*.py' -exec sed -i 's/from a2a_traced\.decision_models/from agent_tracer.models/g' {} +

# Context capture
find . -name '*.py' -exec sed -i 's/from a2a_traced\.context_capture/from agent_tracer.context/g' {} +

# Context propagation
find . -name '*.py' -exec sed -i 's/from a2a_traced\.context_propagation/from agent_tracer.context/g' {} +

# Fail-safe client
find . -name '*.py' -exec sed -i 's/from a2a_traced\.fail_safe/from agent_tracer.utils/g' {} +

# Catch any remaining bare a2a_traced references
find . -name '*.py' -exec sed -i 's/import a2a_traced/import agent_tracer/g' {} +
```

After running these commands, verify no `a2a_traced` references remain:

```bash
grep -r "a2a_traced" --include="*.py" .
```

---

## 4. Convenience Imports

All major symbols are also available directly from the top-level `agent_tracer`
package, so you can use shorter import paths if you prefer:

```python
from agent_tracer.decorators import traced_agent, traced_llm_call, traced_function, traced_tool
from agent_tracer.models import AgentDecision, DecisionCriteria, LLMContext
from agent_tracer.context import LLMContextCaptureMixin, get_current_trace_id, set_current_trace_id
from agent_tracer.utils import FailSafeTraceClient
```

---

## 5. API Compatibility

There are no API changes between `a2a-traced` v1.0.1 and `agent-tracer` v0.2.0.
All classes, functions, decorators, and their signatures remain identical. The
only difference is the import path.

Specifically:

- **Decorator behavior** -- `traced_agent`, `traced_llm_call`, `traced_function`,
  and `traced_tool` accept the same arguments and produce the same trace output.
- **Model classes** -- `AgentDecision`, `DecisionCriteria`, and `LLMContext`
  retain their fields, validation, and serialization behavior.
- **Context propagation** -- `get_current_trace_id` and `set_current_trace_id`
  use the same thread-local storage mechanism.
- **LLMContextCaptureMixin** -- Mixin behavior and interface are unchanged.
- **FailSafeTraceClient** -- Wrapping behavior and error handling are unchanged.

---

## 6. Checklist

Use this checklist to verify a complete migration:

- [ ] Updated `requirements.txt` / `pyproject.toml` to remove `a2a-traced` and
      use `agent-tracer>=0.2.0` (or `agent-tracer[all]>=0.2.0`).
- [ ] Ran the automated sed commands (or manually updated imports).
- [ ] Confirmed no remaining `a2a_traced` references with `grep -r "a2a_traced"`.
- [ ] Uninstalled the old package: `pip uninstall a2a-traced`.
- [ ] Ran your test suite to confirm nothing is broken.

---

## Questions or Issues

If you encounter problems during migration, check that:

1. You are running agent-tracer v0.2.0 or later (`pip show agent-tracer`).
2. The old `a2a-traced` package is fully uninstalled to avoid import conflicts.
3. All import paths have been updated, including in test files and scripts.
