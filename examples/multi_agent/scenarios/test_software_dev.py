"""Tests for software development scenario agents.

Verifies that all agents are properly structured and can be instantiated.
"""

import asyncio
from examples.multi_agent.scenarios.software_dev import (
    CoordinatorAgent,
    ResearchAgent,
    AnalysisAgent,
    SynthesisAgent
)


def test_agent_instantiation():
    """Test that all agents can be instantiated without errors."""
    # Test CoordinatorAgent
    coordinator = CoordinatorAgent(
        agent_id="test_coordinator",
        role="Test Coordinator",
        model="llama2",
        temperature=0.7
    )
    assert coordinator.agent_id == "test_coordinator"
    assert coordinator.role == "Test Coordinator"
    assert coordinator.graph is not None
    print("✓ CoordinatorAgent instantiated successfully")

    # Test ResearchAgent
    research = ResearchAgent(
        agent_id="test_research",
        role="Test Researcher",
        model="llama2",
        temperature=0.7
    )
    assert research.agent_id == "test_research"
    assert research.role == "Test Researcher"
    assert research.graph is not None
    print("✓ ResearchAgent instantiated successfully")

    # Test AnalysisAgent
    analysis = AnalysisAgent(
        agent_id="test_analysis",
        role="Test Analyst",
        model="llama2",
        temperature=0.7
    )
    assert analysis.agent_id == "test_analysis"
    assert analysis.role == "Test Analyst"
    assert analysis.graph is not None
    print("✓ AnalysisAgent instantiated successfully")

    # Test SynthesisAgent
    synthesis = SynthesisAgent(
        agent_id="test_synthesis",
        role="Test Planner",
        model="llama2",
        temperature=0.7
    )
    assert synthesis.agent_id == "test_synthesis"
    assert synthesis.role == "Test Planner"
    assert synthesis.graph is not None
    print("✓ SynthesisAgent instantiated successfully")


def test_agent_graphs():
    """Test that agent graphs are properly structured."""
    coordinator = CoordinatorAgent(
        agent_id="test_coordinator",
        role="Test Coordinator",
        model="llama2",
        temperature=0.7
    )

    # Test that coordinator has the right nodes
    # Note: LangGraph compiled graphs don't expose node info directly,
    # but we can verify the graph exists and is compiled
    assert coordinator.graph is not None
    assert hasattr(coordinator, 'analyze_task')
    assert hasattr(coordinator, 'delegate')
    assert hasattr(coordinator, 'aggregate')
    print("✓ CoordinatorAgent graph structure verified")

    research = ResearchAgent(
        agent_id="test_research",
        role="Test Researcher",
        model="llama2",
        temperature=0.7
    )
    assert research.graph is not None
    assert hasattr(research, 'research')
    assert hasattr(research, 'validate')
    print("✓ ResearchAgent graph structure verified")

    analysis = AnalysisAgent(
        agent_id="test_analysis",
        role="Test Analyst",
        model="llama2",
        temperature=0.7
    )
    assert analysis.graph is not None
    assert hasattr(analysis, 'analyze_security')
    assert hasattr(analysis, 'recommend')
    print("✓ AnalysisAgent graph structure verified")

    synthesis = SynthesisAgent(
        agent_id="test_synthesis",
        role="Test Planner",
        model="llama2",
        temperature=0.7
    )
    assert synthesis.graph is not None
    assert hasattr(synthesis, 'synthesize')
    print("✓ SynthesisAgent graph structure verified")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Software Development Scenario Agents")
    print("=" * 60)
    print()

    print("Test 1: Agent Instantiation")
    print("-" * 60)
    test_agent_instantiation()
    print()

    print("Test 2: Agent Graph Structure")
    print("-" * 60)
    test_agent_graphs()
    print()

    print("=" * 60)
    print("All Tests Passed!")
    print("=" * 60)
