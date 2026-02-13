"""Incident Response Multi-Agent Scenario.

Demonstrates a realistic incident troubleshooting workflow with:
- CoordinatorAgent: Orchestrates incident response
- DiagnosticsAgent: Analyzes error logs and system state
- ResolutionAgent: Provides remediation steps

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
from agent_tracer.exporters import ZipkinExporter


# ==============================================================================
# Agent 1: CoordinatorAgent - Orchestrates incident response
# ==============================================================================

class CoordinatorAgent(BaseLangGraphAgent):
    """Orchestrates multi-agent incident response workflow.

    Workflow:
    1. assess_incident - Initial incident assessment
    2. dispatch - Assign diagnostic tasks
    3. verify_resolution - Verify fix and close incident
    """

    def _build_graph(self):
        """Build coordinator workflow graph."""
        workflow = StateGraph(MultiAgentState)

        # Define nodes
        workflow.add_node("assess_incident", self.assess_incident)
        workflow.add_node("dispatch", self.dispatch)
        workflow.add_node("verify_resolution", self.verify_resolution)

        # Define edges
        workflow.set_entry_point("assess_incident")
        workflow.add_edge("assess_incident", "dispatch")
        workflow.add_edge("dispatch", "verify_resolution")
        workflow.add_edge("verify_resolution", END)

        return workflow.compile()

    async def assess_incident(self, state: MultiAgentState) -> Dict[str, Any]:
        """Assess incident severity and impact."""
        prompt = f"""Assess this incident: {state['task']}

Determine severity and impact in one sentence."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "incident_assessment": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "coordinator", "content": f"Assessment: {result.content}"}
            ]
        }

    async def dispatch(self, state: MultiAgentState) -> Dict[str, Any]:
        """Dispatch diagnostic and resolution tasks."""
        prompt = f"""Dispatch incident response for: {state['context'].get('incident_assessment', '')}

Identify which specialists to engage in one sentence."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "dispatch_plan": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "coordinator", "content": f"Dispatching to: {result.content}"}
            ]
        }

    async def verify_resolution(self, state: MultiAgentState) -> Dict[str, Any]:
        """Verify incident resolution and close ticket."""
        diagnostics = state.get("results", {}).get("diagnostics", "No diagnostics")
        resolution = state.get("results", {}).get("resolution", "No resolution")

        prompt = f"""Verify incident resolution:

Diagnostics: {diagnostics}
Resolution: {resolution}

Confirm resolution status in 2 sentences."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "results": {
                **state.get("results", {}),
                "incident_closure": result.content
            },
            "status": "completed",
            "messages": state.get("messages", []) + [
                {"role": "coordinator", "content": f"Closure: {result.content}"}
            ]
        }


# ==============================================================================
# Agent 2: DiagnosticsAgent - Analyzes error logs and system state
# ==============================================================================

class DiagnosticsAgent(BaseLangGraphAgent):
    """Performs diagnostic analysis of errors and system state.

    Workflow:
    1. analyze_logs - Examine error logs
    2. identify_root_cause - Determine root cause
    """

    def _build_graph(self):
        """Build diagnostics workflow graph."""
        workflow = StateGraph(MultiAgentState)

        # Define nodes
        workflow.add_node("analyze_logs", self.analyze_logs)
        workflow.add_node("identify_root_cause", self.identify_root_cause)

        # Define edges
        workflow.set_entry_point("analyze_logs")
        workflow.add_edge("analyze_logs", "identify_root_cause")
        workflow.add_edge("identify_root_cause", END)

        return workflow.compile()

    async def analyze_logs(self, state: MultiAgentState) -> Dict[str, Any]:
        """Analyze error logs for patterns."""
        prompt = f"""Analyze error logs for: {state['task']}

Identify 2 key error patterns in one sentence each."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "log_analysis": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "diagnostics", "content": f"Log patterns: {result.content}"}
            ]
        }

    async def identify_root_cause(self, state: MultiAgentState) -> Dict[str, Any]:
        """Identify root cause from log analysis."""
        log_analysis = state["context"].get("log_analysis", "")

        prompt = f"""Identify root cause from: {log_analysis}

State the most likely root cause in one sentence."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "results": {
                **state.get("results", {}),
                "diagnostics": f"Patterns: {log_analysis}\nRoot cause: {result.content}"
            },
            "messages": state.get("messages", []) + [
                {"role": "diagnostics", "content": f"Root cause: {result.content}"}
            ]
        }


# ==============================================================================
# Agent 3: ResolutionAgent - Provides remediation steps
# ==============================================================================

class ResolutionAgent(BaseLangGraphAgent):
    """Provides remediation steps and preventive measures.

    Workflow:
    1. create_remediation - Generate fix steps
    2. recommend_prevention - Suggest preventive measures
    """

    def _build_graph(self):
        """Build resolution workflow graph."""
        workflow = StateGraph(MultiAgentState)

        # Define nodes
        workflow.add_node("create_remediation", self.create_remediation)
        workflow.add_node("recommend_prevention", self.recommend_prevention)

        # Define edges
        workflow.set_entry_point("create_remediation")
        workflow.add_edge("create_remediation", "recommend_prevention")
        workflow.add_edge("recommend_prevention", END)

        return workflow.compile()

    async def create_remediation(self, state: MultiAgentState) -> Dict[str, Any]:
        """Create immediate remediation steps."""
        diagnostics = state.get("results", {}).get("diagnostics", "No diagnostics")

        prompt = f"""Create remediation for: {diagnostics}

Provide 2 immediate fix steps in one sentence each."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "remediation_steps": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "resolution", "content": f"Fix steps: {result.content}"}
            ]
        }

    async def recommend_prevention(self, state: MultiAgentState) -> Dict[str, Any]:
        """Recommend preventive measures."""
        remediation = state["context"].get("remediation_steps", "")

        prompt = f"""Recommend prevention for: {remediation}

Suggest 2 preventive measures in one sentence each."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "results": {
                **state.get("results", {}),
                "resolution": f"Remediation: {remediation}\nPrevention: {result.content}"
            },
            "messages": state.get("messages", []) + [
                {"role": "resolution", "content": f"Prevention: {result.content}"}
            ]
        }


# ==============================================================================
# Scenario Runner
# ==============================================================================

async def run_incident_response_scenario():
    """Run the incident response multi-agent scenario.

    Workflow:
    1. Coordinator assesses incident
    2. Diagnostics agent analyzes logs and identifies root cause
    3. Resolution agent provides remediation and prevention steps
    4. Coordinator verifies resolution

    Returns:
        Dict with final results and trace data
    """
    # Setup tracing
    storage = TraceStorageBackend(db_conn=None, storage_dir="traces/incident_response_scenario")
    trace_client = TraceClient(storage)

    # Start main trace
    trace_id = trace_client.start_trace(
        trigger_type="multi_agent_workflow",
        triggered_by="incident_response_scenario",
        metadata={
            "scenario": "database_error_troubleshooting",
            "agents": ["coordinator", "diagnostics", "resolution"],
            "workflow_type": "incident_management"
        }
    )

    print(f"Started trace: {trace_id}")

    try:
        # Apply @traced_agent decorator to create traced instances
        TracedCoordinator = traced_agent(trace_client)(CoordinatorAgent)
        TracedDiagnostics = traced_agent(trace_client)(DiagnosticsAgent)
        TracedResolution = traced_agent(trace_client)(ResolutionAgent)

        # Create agent instances
        coordinator = TracedCoordinator(
            agent_id="coordinator",
            role="Incident Coordinator",
            temperature=0.7
        )

        diagnostics = TracedDiagnostics(
            agent_id="diagnostics",
            role="Diagnostics Specialist",
            temperature=0.7
        )

        resolution = TracedResolution(
            agent_id="resolution",
            role="Resolution Specialist",
            temperature=0.7
        )

        # Initial task
        task = "Troubleshoot database connection timeout errors in production"

        # Step 1: Coordinator assesses incident
        print("\n=== Step 1: Incident Assessment ===")
        coord_result = await coordinator.run({"task": task})
        print(f"Assessment: {coord_result['context'].get('incident_assessment', 'N/A')}")

        # Step 2: Diagnostics analysis
        print("\n=== Step 2: Diagnostics Analysis ===")
        diag_result = await diagnostics.run({
            "task": task,
            "context": coord_result["context"]
        })
        print(f"Diagnostics: {diag_result['results'].get('diagnostics', 'N/A')}")

        # Step 3: Resolution planning
        print("\n=== Step 3: Resolution Planning ===")
        resolution_result = await resolution.run({
            "task": task,
            "context": coord_result["context"],
            "results": diag_result["results"]
        })
        print(f"Resolution: {resolution_result['results'].get('resolution', 'N/A')}")

        # Step 4: Coordinator verifies
        print("\n=== Step 4: Resolution Verification ===")
        final_result = await coordinator.run({
            "task": task,
            "context": coord_result["context"],
            "results": resolution_result["results"]
        })
        print(f"Closure: {final_result['results'].get('incident_closure', 'N/A')}")

        # Complete trace
        trace_client.complete_trace(
            status="completed",
            summary={
                "workflow": "database_error_troubleshooting",
                "agents_executed": 3,
                "final_result": final_result["results"].get("incident_closure", "")
            }
        )

        print(f"\n✓ Trace completed: {trace_id}")

        # Export to Jaeger
        print("\n=== Exporting to Jaeger ===")
        exporter = ZipkinExporter(service_name="incident-response-agents")

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
        print(f"\n✗ Incident response failed: {e}")
        raise


# ==============================================================================
# Main Entry Point
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Incident Response Multi-Agent Scenario")
    print("=" * 80)
    print("\nThis demonstrates a realistic incident troubleshooting workflow")
    print("with automatic tracing via @traced_agent decorator.\n")

    result = asyncio.run(run_incident_response_scenario())

    print("\n" + "=" * 80)
    print("Scenario Complete!")
    print("=" * 80)
    print(f"\nTrace ID: {result['trace_id']}")
    print(f"Status: {result['status']}")
    print("\nView traces in Jaeger UI at: http://localhost:16686")
    print("\nSearch for service: 'incident-response-agents'")
