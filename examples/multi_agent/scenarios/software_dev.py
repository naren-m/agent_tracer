"""Software Development Multi-Agent Scenario.

Demonstrates a realistic authentication feature design workflow with:
- CoordinatorAgent: Orchestrates the workflow
- ResearchAgent: Researches authentication methods
- AnalysisAgent: Analyzes security implications
- SynthesisAgent: Creates implementation plan

All agents use LangGraph for workflow and are automatically traced
via @traced_agent decorator with zero tracing code in agent logic.
"""

import asyncio
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from agent_tracer.decorators import traced_agent
from examples.multi_agent.base_agent import BaseLangGraphAgent, MultiAgentState
from agent_tracer import TraceClient
from agent_tracer.storage import TraceStorageBackend
from agent_tracer.integrations.exporters import ZipkinExporter


# ==============================================================================
# Agent 1: CoordinatorAgent - Orchestrates the workflow
# ==============================================================================

class CoordinatorAgent(BaseLangGraphAgent):
    """Orchestrates multi-agent workflow for feature design.

    Workflow:
    1. analyze_task - Understand requirements
    2. delegate - Assign work to specialists
    3. aggregate - Combine results into final plan
    """

    def _build_graph(self):
        """Build coordinator workflow graph."""
        workflow = StateGraph(MultiAgentState)

        # Define nodes
        workflow.add_node("analyze_task", self.analyze_task)
        workflow.add_node("delegate", self.delegate)
        workflow.add_node("aggregate", self.aggregate)

        # Define edges
        workflow.set_entry_point("analyze_task")
        workflow.add_edge("analyze_task", "delegate")
        workflow.add_edge("delegate", "aggregate")
        workflow.add_edge("aggregate", END)

        return workflow.compile()

    async def analyze_task(self, state: MultiAgentState) -> Dict[str, Any]:
        """Analyze the task requirements."""
        prompt = f"""Analyze this feature request: {state['task']}

Identify key requirements in one sentence."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "requirements": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "coordinator", "content": f"Requirements: {result.content}"}
            ]
        }

    async def delegate(self, state: MultiAgentState) -> Dict[str, Any]:
        """Delegate work to specialist agents."""
        prompt = f"""Given requirements: {state['context'].get('requirements', '')}

Which specialists should work on this? List: researcher, security analyst, or implementation planner."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "delegation_plan": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "coordinator", "content": f"Delegating to: {result.content}"}
            ]
        }

    async def aggregate(self, state: MultiAgentState) -> Dict[str, Any]:
        """Aggregate results from all agents."""
        research = state.get("results", {}).get("research", "No research")
        security = state.get("results", {}).get("security", "No security analysis")
        plan = state.get("results", {}).get("implementation", "No plan")

        prompt = f"""Summarize this feature design in 2 sentences:

Research: {research}
Security: {security}
Plan: {plan}"""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "results": {
                **state.get("results", {}),
                "final_summary": result.content
            },
            "status": "completed",
            "messages": state.get("messages", []) + [
                {"role": "coordinator", "content": f"Summary: {result.content}"}
            ]
        }


# ==============================================================================
# Agent 2: ResearchAgent - Researches authentication methods
# ==============================================================================

class ResearchAgent(BaseLangGraphAgent):
    """Researches authentication approaches.

    Workflow:
    1. research - Investigate auth methods
    2. validate - Validate findings
    """

    def _build_graph(self):
        """Build research workflow graph."""
        workflow = StateGraph(MultiAgentState)

        # Define nodes
        workflow.add_node("research", self.research)
        workflow.add_node("validate", self.validate)

        # Define edges
        workflow.set_entry_point("research")
        workflow.add_edge("research", "validate")
        workflow.add_edge("validate", END)

        return workflow.compile()

    async def research(self, state: MultiAgentState) -> Dict[str, Any]:
        """Research authentication methods."""
        prompt = f"""Research auth methods for: {state['task']}

List 2 common approaches in one sentence each."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "research_findings": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "researcher", "content": f"Found: {result.content}"}
            ]
        }

    async def validate(self, state: MultiAgentState) -> Dict[str, Any]:
        """Validate research findings."""
        findings = state["context"].get("research_findings", "")

        prompt = f"""Validate these auth methods: {findings}

Are they suitable? Answer in one sentence."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "results": {
                **state.get("results", {}),
                "research": f"{findings}\nValidation: {result.content}"
            },
            "messages": state.get("messages", []) + [
                {"role": "researcher", "content": f"Validated: {result.content}"}
            ]
        }


# ==============================================================================
# Agent 3: AnalysisAgent - Security analysis
# ==============================================================================

class AnalysisAgent(BaseLangGraphAgent):
    """Analyzes security implications.

    Workflow:
    1. analyze_security - Identify risks
    2. recommend - Provide recommendations
    """

    def _build_graph(self):
        """Build analysis workflow graph."""
        workflow = StateGraph(MultiAgentState)

        # Define nodes
        workflow.add_node("analyze_security", self.analyze_security)
        workflow.add_node("recommend", self.recommend)

        # Define edges
        workflow.set_entry_point("analyze_security")
        workflow.add_edge("analyze_security", "recommend")
        workflow.add_edge("recommend", END)

        return workflow.compile()

    async def analyze_security(self, state: MultiAgentState) -> Dict[str, Any]:
        """Analyze security risks."""
        research = state.get("results", {}).get("research", "Unknown auth method")

        prompt = f"""Security analysis for: {research}

List 2 main risks in one sentence each."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "security_risks": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "security", "content": f"Risks: {result.content}"}
            ]
        }

    async def recommend(self, state: MultiAgentState) -> Dict[str, Any]:
        """Provide security recommendations."""
        risks = state["context"].get("security_risks", "")

        prompt = f"""Given risks: {risks}

Recommend 2 mitigations in one sentence each."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "results": {
                **state.get("results", {}),
                "security": f"Risks: {risks}\nMitigations: {result.content}"
            },
            "messages": state.get("messages", []) + [
                {"role": "security", "content": f"Mitigations: {result.content}"}
            ]
        }


# ==============================================================================
# Agent 4: SynthesisAgent - Creates implementation plan
# ==============================================================================

class SynthesisAgent(BaseLangGraphAgent):
    """Creates implementation plan.

    Workflow:
    1. synthesize - Create final plan
    """

    def _build_graph(self):
        """Build synthesis workflow graph."""
        workflow = StateGraph(MultiAgentState)

        # Define node
        workflow.add_node("synthesize", self.synthesize)

        # Define edges
        workflow.set_entry_point("synthesize")
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    async def synthesize(self, state: MultiAgentState) -> Dict[str, Any]:
        """Create implementation plan."""
        research = state.get("results", {}).get("research", "No research")
        security = state.get("results", {}).get("security", "No security")

        prompt = f"""Create implementation plan:

Research: {research}
Security: {security}

Provide 3 implementation steps in one sentence each."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "results": {
                **state.get("results", {}),
                "implementation": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "planner", "content": f"Plan: {result.content}"}
            ]
        }


# ==============================================================================
# Scenario Runner
# ==============================================================================

async def run_software_dev_scenario():
    """Run the software development multi-agent scenario.

    Workflow:
    1. Coordinator analyzes task
    2. Research agent investigates auth methods
    3. Analysis agent evaluates security
    4. Synthesis agent creates plan
    5. Coordinator aggregates results

    Returns:
        Dict with final results and trace data
    """
    # Setup tracing
    storage = TraceStorageBackend(db_conn=None, storage_dir="traces/software_dev_scenario")
    trace_client = TraceClient(storage)

    # Start main trace
    trace_id = trace_client.start_trace(
        trigger_type="multi_agent_workflow",
        triggered_by="software_dev_scenario",
        metadata={
            "scenario": "authentication_feature_design",
            "agents": ["coordinator", "research", "analysis", "synthesis"],
            "workflow_type": "sequential_with_coordination"
        }
    )

    print(f"Started trace: {trace_id}")

    try:
        # Apply @traced_agent decorator to create traced instances
        # Note: The decorator adds tracing capabilities without modifying agent logic

        TracedCoordinator = traced_agent(trace_client)(CoordinatorAgent)
        TracedResearch = traced_agent(trace_client)(ResearchAgent)
        TracedAnalysis = traced_agent(trace_client)(AnalysisAgent)
        TracedSynthesis = traced_agent(trace_client)(SynthesisAgent)

        # Create agent instances
        coordinator = TracedCoordinator(
            agent_id="coordinator",
            role="Workflow Coordinator",
            temperature=0.7
        )

        research = TracedResearch(
            agent_id="research",
            role="Authentication Researcher",
            temperature=0.7
        )

        analysis = TracedAnalysis(
            agent_id="analysis",
            role="Security Analyst",
            temperature=0.7
        )

        synthesis = TracedSynthesis(
            agent_id="synthesis",
            role="Implementation Planner",
            temperature=0.7
        )

        # Initial task
        task = "Design user authentication for a web application"

        # Step 1: Coordinator analyzes and delegates
        print("\n=== Step 1: Coordinator Analysis ===")
        coord_result = await coordinator.run({"task": task})
        print(f"Requirements: {coord_result['context'].get('requirements', 'N/A')}")

        # Step 2: Research authentication methods
        print("\n=== Step 2: Research Phase ===")
        research_result = await research.run({
            "task": task,
            "context": coord_result["context"]
        })
        print(f"Research: {research_result['results'].get('research', 'N/A')}")

        # Step 3: Security analysis
        print("\n=== Step 3: Security Analysis ===")
        analysis_result = await analysis.run({
            "task": task,
            "context": coord_result["context"],
            "results": research_result["results"]
        })
        print(f"Security: {analysis_result['results'].get('security', 'N/A')}")

        # Step 4: Create implementation plan
        print("\n=== Step 4: Implementation Planning ===")
        synthesis_result = await synthesis.run({
            "task": task,
            "context": coord_result["context"],
            "results": analysis_result["results"]
        })
        print(f"Plan: {synthesis_result['results'].get('implementation', 'N/A')}")

        # Step 5: Coordinator aggregates
        print("\n=== Step 5: Coordinator Aggregation ===")
        final_result = await coordinator.run({
            "task": task,
            "context": coord_result["context"],
            "results": synthesis_result["results"]
        })
        print(f"Summary: {final_result['results'].get('final_summary', 'N/A')}")

        # Complete trace
        trace_client.complete_trace(
            status="completed",
            summary={
                "workflow": "authentication_feature_design",
                "agents_executed": 4,
                "final_result": final_result["results"].get("final_summary", "")
            }
        )

        print(f"\n✓ Trace completed: {trace_id}")

        # Export to Jaeger
        print("\n=== Exporting to Jaeger ===")
        exporter = ZipkinExporter(service_name="software-dev-scenario")

        # Get all traces from storage directory
        import json
        from pathlib import Path

        storage_path = Path(storage.storage_dir)
        for trace_dir in storage_path.glob("trace_*"):
            trace_file = trace_dir / "trace.json"
            if trace_file.exists():
                with open(trace_file, 'r') as f:
                    trace_dict = json.load(f)
                success = exporter.send_to_jaeger(trace_dict)
                if success:
                    print(f"✓ Exported trace {trace_dict['trace_id']} to Jaeger")
                else:
                    print(f"✗ Failed to export trace {trace_dict['trace_id']}")

        return {
            "trace_id": trace_id,
            "final_result": final_result,
            "status": "success"
        }

    except Exception as e:
        # Handle errors
        trace_client.complete_trace(
            status="failed",
            summary={"error": str(e), "type": type(e).__name__}
        )
        print(f"\n✗ Workflow failed: {e}")
        raise


# ==============================================================================
# Main Entry Point
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Software Development Multi-Agent Scenario")
    print("=" * 80)
    print("\nThis demonstrates a realistic authentication feature design workflow")
    print("with automatic tracing via @traced_agent decorator.\n")

    result = asyncio.run(run_software_dev_scenario())

    print("\n" + "=" * 80)
    print("Scenario Complete!")
    print("=" * 80)
    print(f"\nTrace ID: {result['trace_id']}")
    print(f"Status: {result['status']}")
    print("\nView traces in Jaeger UI at: http://localhost:16686")
    print("\nSearch for service: 'software-dev-scenario'")
