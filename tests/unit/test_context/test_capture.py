"""Test context capture mixin."""

import pytest
from agent_tracer.context import LLMContextCaptureMixin
from agent_tracer.models import LLMContext


class TestLLMContextCaptureMixin:
    """Test LLMContextCaptureMixin functionality."""

    def test_capture_context_with_kwargs(self):
        """Test capturing context from kwargs."""

        class TestAgent(LLMContextCaptureMixin):
            pass

        agent = TestAgent()
        context = agent._capture_context(
            (),
            {
                'model': 'gpt-4',
                'temperature': 0.8,
                'messages': [
                    {'role': 'user', 'content': 'Hello world'}
                ]
            }
        )

        assert isinstance(context, LLMContext)
        assert context.model == 'gpt-4'
        assert context.temperature == 0.8
        assert len(context.messages) == 1
        assert context.prompt_tokens > 0

    def test_capture_context_with_defaults(self):
        """Test capturing context with default values."""

        class TestAgent(LLMContextCaptureMixin):
            model_name = 'claude-3'
            temperature = 0.5

        agent = TestAgent()
        context = agent._capture_context((), {})

        assert context.model == 'claude-3'
        assert context.temperature == 0.5
        assert context.messages == []
        assert context.prompt_tokens == 0

    def test_count_tokens(self):
        """Test token counting."""

        class TestAgent(LLMContextCaptureMixin):
            pass

        agent = TestAgent()
        messages = [
            {'role': 'user', 'content': 'Hello world'},
            {'role': 'assistant', 'content': 'Hi there, how can I help?'}
        ]

        tokens = agent._count_tokens(messages)
        # "Hello world" = 2 words, "Hi there, how can I help?" = 6 words
        assert tokens == 8

    def test_get_available_tools(self):
        """Test getting available tools."""

        class Tool:
            def __init__(self, name):
                self.name = name

        class TestAgent(LLMContextCaptureMixin):
            def __init__(self):
                self.tools = [Tool('search'), Tool('calculator')]

        agent = TestAgent()
        tools = agent._get_available_tools()

        assert len(tools) == 2
        assert 'search' in tools
        assert 'calculator' in tools

    def test_get_available_tools_empty(self):
        """Test getting available tools when none exist."""

        class TestAgent(LLMContextCaptureMixin):
            pass

        agent = TestAgent()
        tools = agent._get_available_tools()

        assert tools == []

    def test_get_agent_state(self):
        """Test getting agent state."""

        class TestAgent(LLMContextCaptureMixin):
            def __init__(self):
                self.history = ['turn1', 'turn2', 'turn3']
                self.last_action = 'search'
                self.memory = {'key': 'value'}

        agent = TestAgent()
        state = agent._get_agent_state()

        assert state['conversation_turns'] == 3
        assert state['last_action'] == 'search'
        assert state['memory'] == {'key': 'value'}

    def test_get_agent_state_minimal(self):
        """Test getting agent state with minimal attributes."""

        class TestAgent(LLMContextCaptureMixin):
            pass

        agent = TestAgent()
        state = agent._get_agent_state()

        assert state == {}

    def test_capture_context_integration(self):
        """Test full context capture integration."""

        class Tool:
            def __init__(self, name):
                self.name = name

        class TestAgent(LLMContextCaptureMixin):
            def __init__(self):
                self.model_name = 'gpt-4'
                self.temperature = 0.7
                self.tools = [Tool('search'), Tool('calculator')]
                self.history = ['turn1']
                self.last_action = 'think'

        agent = TestAgent()
        context = agent._capture_context(
            (),
            {
                'messages': [
                    {'role': 'user', 'content': 'What is 2+2?'}
                ]
            }
        )

        assert context.model == 'gpt-4'
        assert context.temperature == 0.7
        assert len(context.messages) == 1
        assert context.prompt_tokens == 3  # "What is 2+2?"
        assert len(context.tools_available) == 2
        assert context.agent_state['conversation_turns'] == 1
        assert context.agent_state['last_action'] == 'think'
