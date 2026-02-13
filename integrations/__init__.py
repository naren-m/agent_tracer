"""Integration modules for agent-tracer with various frameworks."""

__all__ = []

# LangChain integration (optional dependency)
try:
    from agent_tracer.integrations.langchain import ComprehensiveTracingCallback
    __all__.append("ComprehensiveTracingCallback")
except ImportError:
    ComprehensiveTracingCallback = None

# Exporters (optional dependency - requires requests)
try:
    from agent_tracer.integrations.exporters import ZipkinExporter, JaegerExporter
    __all__.extend(["ZipkinExporter", "JaegerExporter"])
except ImportError:
    ZipkinExporter = None
    JaegerExporter = None
