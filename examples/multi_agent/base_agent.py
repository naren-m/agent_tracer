"""Base LangGraph agent template with zero tracing code.

Agent developers inherit from this and implement their logic.
Tracing happens automatically via callbacks.
"""

from typing import TypedDict, Annotated, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
import ollama


def get_default_llama_model() -> str:
    """Get the first available llama model from Ollama.

    Returns:
        Model name, or 'llama2' as fallback
    """
    try:
        client = ollama.Client()
        models = client.list()
        model_names = [m.model for m in models.models]
        llama_models = [name for name in model_names if 'llama' in name.lower()]
        return llama_models[0] if llama_models else 'llama2'
    except:
        return 'llama2'  # Fallback


class MultiAgentState(TypedDict):
    """Shared state structure for multi-agent workflows."""
    task: str
    context: Dict[str, Any]
    messages: list[Dict[str, str]]
    results: Dict[str, Any]
    agent_id: str
    status: str


class BaseLangGraphAgent:
    """Base class for LangGraph agents with automatic tracing.

    Pure LangGraph implementation - zero tracing code needed.
    Tracing happens automatically when @traced_agent decorator is applied.

    Subclasses should:
    1. Override _build_graph() to define workflow
    2. Implement node methods (do_work, analyze, etc.)
    3. Use self.llm for LLM calls

    Example:
        @traced_agent(trace_client)
        class ResearchAgent(BaseLangGraphAgent):
            def _build_graph(self):
                workflow = StateGraph(MultiAgentState)
                workflow.add_node("research", self.do_research)
                workflow.set_entry_point("research")
                workflow.add_edge("research", END)
                return workflow.compile()

            async def do_research(self, state):
                result = await self.llm.ainvoke(f"Research: {state['task']}")
                return {"results": {"research": result.content}}
    """

    def __init__(
        self,
        agent_id: str,
        role: str,
        model: Optional[str] = None,
        temperature: float = 0.7
    ):
        """Initialize base agent.

        Args:
            agent_id: Unique agent identifier
            role: Agent role description
            model: Ollama model to use (auto-detects first llama model if None)
            temperature: LLM temperature
        """
        self.agent_id = agent_id
        self.role = role
        self.model = model or get_default_llama_model()
        self.temperature = temperature

        # LLM instance
        self.llm = ChatOllama(
            model=self.model,
            temperature=temperature
        )

        # Callbacks list - will be populated by @traced_agent decorator
        self.callbacks = []

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Build LangGraph workflow. Override in subclasses.

        Returns:
            Compiled LangGraph workflow
        """
        # Default single-node graph
        workflow = StateGraph(MultiAgentState)
        workflow.add_node("process", self._default_process)
        workflow.set_entry_point("process")
        workflow.add_edge("process", END)
        return workflow.compile()

    async def _default_process(self, state: MultiAgentState) -> Dict[str, Any]:
        """Default processing node."""
        # Simple echo
        return {
            "results": {
                "agent_id": self.agent_id,
                "processed": state.get("task", "")
            },
            "status": "completed"
        }

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent workflow.

        This method is wrapped by @traced_agent decorator for automatic tracing.

        Args:
            input_data: Input task and context

        Returns:
            Agent results
        """
        # Prepare state
        state = {
            "task": input_data.get("task", ""),
            "context": input_data.get("context", {}),
            "messages": [],
            "results": {},
            "agent_id": self.agent_id,
            "status": "running"
        }

        # Run graph with callbacks
        result = await self.graph.ainvoke(
            state,
            config={"callbacks": self.callbacks}
        )

        return result
