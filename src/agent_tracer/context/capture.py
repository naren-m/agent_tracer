"""Context capture utilities for LLM calls."""
from typing import List, Dict, Any
from agent_tracer.models import LLMContext


class LLMContextCaptureMixin:
    """Mixin for agents that need to capture LLM context."""

    def _capture_context(self, args: tuple, kwargs: dict) -> LLMContext:
        """Capture full context before LLM call."""
        messages = kwargs.get('messages', [])

        return LLMContext(
            model=kwargs.get('model', getattr(self, 'model_name', 'unknown')),
            temperature=kwargs.get('temperature', getattr(self, 'temperature', 0.7)),
            messages=messages,
            prompt_tokens=self._count_tokens(messages),
            tools_available=self._get_available_tools(),
            agent_state=self._get_agent_state()
        )

    def _count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count (simple word count for now)."""
        total = 0
        for msg in messages:
            content = msg.get('content', '')
            total += len(content.split())
        return total

    def _get_available_tools(self) -> List[str]:
        """Get list of tools agent can use."""
        tools = getattr(self, 'tools', [])
        if hasattr(tools, '__iter__'):
            return [getattr(tool, 'name', str(tool)) for tool in tools]
        return []

    def _get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state."""
        state = {}

        if hasattr(self, 'history'):
            state['conversation_turns'] = len(self.history)

        if hasattr(self, 'last_action'):
            state['last_action'] = self.last_action

        if hasattr(self, 'memory'):
            state['memory'] = self.memory

        return state
