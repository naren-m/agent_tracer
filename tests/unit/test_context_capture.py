"""Test LLM context capture."""
import pytest


def test_context_capture_extracts_basic_info():
    """Test capturing basic LLM context."""
    from agent_tracer.context_capture import LLMContextCaptureMixin
    from agent_tracer.decision_models import LLMContext
    
    class TestAgent(LLMContextCaptureMixin):
        def __init__(self):
            self.model_name = "gpt-4"
            self.temperature = 0.7
            self.tools = []
    
    agent = TestAgent()
    context = agent._capture_context(
        args=(),
        kwargs={
            "messages": [{"role": "user", "content": "test"}],
            "model": "gpt-4",
            "temperature": 0.7
        }
    )
    
    assert isinstance(context, LLMContext)
    assert context.model == "gpt-4"
    assert context.temperature == 0.7
    assert len(context.messages) == 1


def test_context_capture_counts_tokens():
    """Test token counting in context."""
    from agent_tracer.context_capture import LLMContextCaptureMixin
    
    class TestAgent(LLMContextCaptureMixin):
        model_name = "gpt-4"
        temperature = 0.7
        tools = []
    
    agent = TestAgent()
    messages = [
        {"role": "user", "content": "hello world"},
        {"role": "assistant", "content": "hi there"}
    ]
    
    tokens = agent._count_tokens(messages)
    assert tokens > 0  # Simple word count estimate


def test_context_capture_tools():
    """Test capturing available tools."""
    from agent_tracer.context_capture import LLMContextCaptureMixin
    
    class MockTool:
        def __init__(self, name):
            self.name = name
    
    class TestAgent(LLMContextCaptureMixin):
        def __init__(self):
            self.model_name = "gpt-4"
            self.temperature = 0.7
            self.tools = [MockTool("search"), MockTool("calculator")]
    
    agent = TestAgent()
    context = agent._capture_context(
        args=(),
        kwargs={"messages": [], "model": "gpt-4"}
    )
    
    assert len(context.tools_available) == 2
    assert "search" in context.tools_available
    assert "calculator" in context.tools_available


def test_context_capture_agent_state():
    """Test capturing agent state."""
    from agent_tracer.context_capture import LLMContextCaptureMixin
    
    class TestAgent(LLMContextCaptureMixin):
        def __init__(self):
            self.model_name = "gpt-4"
            self.temperature = 0.7
            self.tools = []
            self.history = ["msg1", "msg2", "msg3"]
            self.last_action = "search"
            self.memory = {"key": "value"}
    
    agent = TestAgent()
    context = agent._capture_context(
        args=(),
        kwargs={"messages": [], "model": "gpt-4"}
    )
    
    assert context.agent_state["conversation_turns"] == 3
    assert context.agent_state["last_action"] == "search"
    assert context.agent_state["memory"] == {"key": "value"}


def test_context_capture_defaults():
    """Test context capture with minimal agent attributes."""
    from agent_tracer.context_capture import LLMContextCaptureMixin
    
    class MinimalAgent(LLMContextCaptureMixin):
        pass
    
    agent = MinimalAgent()
    context = agent._capture_context(
        args=(),
        kwargs={"messages": [{"role": "user", "content": "test"}]}
    )
    
    assert context.model == "unknown"
    assert context.temperature == 0.7
    assert context.tools_available == []
    assert context.agent_state == {}
