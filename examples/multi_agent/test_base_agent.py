"""Tests for base LangGraph agent."""
import pytest
from base_agent import MultiAgentState, BaseLangGraphAgent


@pytest.mark.asyncio
async def test_base_agent_has_graph():
    """Test that base agent builds a graph."""
    agent = BaseLangGraphAgent(agent_id="test", role="tester")

    assert agent.graph is not None
    assert hasattr(agent, 'callbacks')
    assert isinstance(agent.callbacks, list)


@pytest.mark.asyncio
async def test_base_agent_processes_task():
    """Test that base agent can process a task."""
    agent = BaseLangGraphAgent(agent_id="test", role="tester")

    result = await agent.run({"task": "test task", "context": {}})

    assert "results" in result
    assert "agent_id" in result
