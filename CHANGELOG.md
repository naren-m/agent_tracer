# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-02-14

### Fixed

- Fix `_utc_now_iso` bug in `TraceClient.add_artifact` -- was referencing undefined name instead of `utc_now_iso`, causing artifact creation to fail silently under fail-safe mode.
- Fix stale exporter imports in all examples (`agent_tracer.exporters` -> `agent_tracer.integrations.exporters`).

### Added

- `examples/incident_response_demo.py`: realistic 4-agent production incident response scenario with 14 agent-to-agent interactions under a single unified trace (33 spans, 5 phases).

## [0.2.0] - 2026-02-13

### Added

- Decorator-based tracing: `@traced_agent`, `@traced_llm_call`, `@traced_function`, `@traced_tool`.
- Decision models: `AgentDecision`, `DecisionCriteria`, `LLMContext` (Pydantic models for structured decision capture).
- Context management: `LLMContextCaptureMixin` for capturing LLM context before calls.
- Context propagation: async-safe trace ID propagation using `contextvars`.
- Fail-safe tracing: `FailSafeTraceClient` wrapper that prevents tracing errors from breaking agents.
- LangChain/LangGraph integration: `ComprehensiveTracingCallback` for automatic tracing.
- Export integrations: Zipkin and Jaeger trace exporters.
- Optional dependency groups: `[llm]`, `[langchain]`, `[exporters]`, `[all]`.
- Comprehensive test suite with 68+ tests.

### Changed

- Package version bumped from 0.1.0 to 0.2.0.
- Package description updated to reflect unified tracing capabilities.
- Added `pytest-asyncio` to dev dependencies.

## [0.1.0] - 2026-01-15

### Added

- Initial release.
- `TraceClient` for creating and managing traces.
- File-based and PostgreSQL storage backends.
- Hierarchical trace structure (Trace -> Span -> Step).
- Pydantic schemas for trace data.
- Core utilities.
