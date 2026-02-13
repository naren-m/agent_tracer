"""Test that @traced_agent decorator integrates correctly with agents.

This test verifies that the decorator:
1. Can be applied to agent classes
2. Injects callbacks into the agent
3. Doesn't break the agent's run method signature
"""

from agent_tracer.decorators import traced_agent
from examples.multi_agent.scenarios.software_dev import CoordinatorAgent
from agent_tracer import TraceClient
from agent_tracer.storage import TraceStorageBackend


def test_decorator_application():
    """Test that decorator can be applied to agent classes."""
    # Create trace client
    storage = TraceStorageBackend(db_conn=None, storage_dir="/tmp/test_traces")
    trace_client = TraceClient(storage)

    # Apply decorator
    TracedCoordinator = traced_agent(trace_client)(CoordinatorAgent)

    # Create instance
    agent = TracedCoordinator(
        agent_id="test_agent",
        role="Test Coordinator",
        model="llama2",
        temperature=0.7
    )

    # Verify agent has callbacks
    assert hasattr(agent, 'callbacks')
    assert isinstance(agent.callbacks, list)
    assert len(agent.callbacks) > 0, "Decorator should inject at least one callback"

    # Verify callback is our tracing callback
    from agent_tracer.langchain_integration import ComprehensiveTracingCallback
    assert any(isinstance(cb, ComprehensiveTracingCallback) for cb in agent.callbacks), \
        "Decorator should inject ComprehensiveTracingCallback"

    print("✓ Decorator successfully applied and injected callbacks")


def test_multiple_agents_traced():
    """Test that multiple agents can be traced with same client."""
    from examples.multi_agent.scenarios.software_dev import (
        CoordinatorAgent, ResearchAgent, AnalysisAgent, SynthesisAgent
    )

    # Create trace client
    storage = TraceStorageBackend(db_conn=None, storage_dir="/tmp/test_traces")
    trace_client = TraceClient(storage)

    # Apply decorator to all agents
    TracedCoordinator = traced_agent(trace_client)(CoordinatorAgent)
    TracedResearch = traced_agent(trace_client)(ResearchAgent)
    TracedAnalysis = traced_agent(trace_client)(AnalysisAgent)
    TracedSynthesis = traced_agent(trace_client)(SynthesisAgent)

    # Create instances
    coordinator = TracedCoordinator(
        agent_id="coordinator",
        role="Coordinator",
        model="llama2",
        temperature=0.7
    )

    research = TracedResearch(
        agent_id="research",
        role="Researcher",
        model="llama2",
        temperature=0.7
    )

    analysis = TracedAnalysis(
        agent_id="analysis",
        role="Analyst",
        model="llama2",
        temperature=0.7
    )

    synthesis = TracedSynthesis(
        agent_id="synthesis",
        role="Planner",
        model="llama2",
        temperature=0.7
    )

    # Verify all have callbacks
    for agent in [coordinator, research, analysis, synthesis]:
        assert len(agent.callbacks) > 0, f"Agent {agent.agent_id} should have callbacks"

    print("✓ Multiple agents successfully traced with same trace_client")


def test_agent_retains_original_behavior():
    """Test that traced agent retains original behavior and attributes."""
    # Create trace client
    storage = TraceStorageBackend(db_conn=None, storage_dir="/tmp/test_traces")
    trace_client = TraceClient(storage)

    # Apply decorator
    TracedCoordinator = traced_agent(trace_client)(CoordinatorAgent)

    # Create instance
    agent = TracedCoordinator(
        agent_id="test_agent",
        role="Test Coordinator",
        model="llama2",
        temperature=0.7
    )

    # Verify original attributes exist
    assert agent.agent_id == "test_agent"
    assert agent.role == "Test Coordinator"
    assert agent.model == "llama2"
    assert agent.temperature == 0.7

    # Verify graph exists and has nodes
    assert agent.graph is not None
    assert hasattr(agent, 'analyze_task')
    assert hasattr(agent, 'delegate')
    assert hasattr(agent, 'aggregate')

    # Verify run method exists
    assert hasattr(agent, 'run')
    assert callable(agent.run)

    print("✓ Traced agent retains all original behavior and attributes")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing @traced_agent Decorator Integration")
    print("=" * 60)
    print()

    print("Test 1: Decorator Application")
    print("-" * 60)
    test_decorator_application()
    print()

    print("Test 2: Multiple Agents Traced")
    print("-" * 60)
    test_multiple_agents_traced()
    print()

    print("Test 3: Agent Retains Original Behavior")
    print("-" * 60)
    test_agent_retains_original_behavior()
    print()

    print("=" * 60)
    print("All Decorator Tests Passed!")
    print("=" * 60)
    print("\nNote: These tests verify decorator integration without")
    print("      requiring Ollama. To test full execution with LLM calls,")
    print("      run: python examples/multi_agent/scenarios/software_dev.py")
