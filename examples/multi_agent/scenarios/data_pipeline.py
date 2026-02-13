"""Data Pipeline Multi-Agent Scenario.

Demonstrates a realistic data processing workflow with:
- CoordinatorAgent: Orchestrates the pipeline
- DataFetchAgent: Fetches user feedback data
- DataAnalysisAgent: Performs sentiment analysis and generates insights

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
# Agent 1: CoordinatorAgent - Orchestrates the data pipeline
# ==============================================================================

class CoordinatorAgent(BaseLangGraphAgent):
    """Orchestrates multi-agent data pipeline workflow.

    Workflow:
    1. initialize_pipeline - Setup data processing
    2. coordinate - Manage data flow between agents
    3. finalize - Complete pipeline and generate report
    """

    def _build_graph(self):
        """Build coordinator workflow graph."""
        workflow = StateGraph(MultiAgentState)

        # Define nodes
        workflow.add_node("initialize_pipeline", self.initialize_pipeline)
        workflow.add_node("coordinate", self.coordinate)
        workflow.add_node("finalize", self.finalize)

        # Define edges
        workflow.set_entry_point("initialize_pipeline")
        workflow.add_edge("initialize_pipeline", "coordinate")
        workflow.add_edge("coordinate", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def initialize_pipeline(self, state: MultiAgentState) -> Dict[str, Any]:
        """Initialize data pipeline configuration."""
        prompt = f"""Initialize data pipeline for: {state['task']}

Identify data sources and processing requirements in one sentence."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "pipeline_config": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "coordinator", "content": f"Pipeline initialized: {result.content}"}
            ]
        }

    async def coordinate(self, state: MultiAgentState) -> Dict[str, Any]:
        """Coordinate data flow between processing agents."""
        prompt = f"""Coordinate data processing for: {state['context'].get('pipeline_config', '')}

Define processing sequence in one sentence."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "processing_sequence": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "coordinator", "content": f"Sequence: {result.content}"}
            ]
        }

    async def finalize(self, state: MultiAgentState) -> Dict[str, Any]:
        """Finalize pipeline and generate summary report."""
        fetched_data = state.get("results", {}).get("fetched_data", "No data")
        insights = state.get("results", {}).get("insights", "No insights")

        prompt = f"""Generate pipeline summary report:

Data: {fetched_data}
Insights: {insights}

Summarize key findings in 2 sentences."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "results": {
                **state.get("results", {}),
                "pipeline_report": result.content
            },
            "status": "completed",
            "messages": state.get("messages", []) + [
                {"role": "coordinator", "content": f"Report: {result.content}"}
            ]
        }


# ==============================================================================
# Agent 2: DataFetchAgent - Fetches user feedback data
# ==============================================================================

class DataFetchAgent(BaseLangGraphAgent):
    """Fetches user feedback data from various sources.

    Workflow:
    1. fetch_data - Retrieve feedback data
    2. validate_data - Validate data quality
    """

    def _build_graph(self):
        """Build data fetch workflow graph."""
        workflow = StateGraph(MultiAgentState)

        # Define nodes
        workflow.add_node("fetch_data", self.fetch_data)
        workflow.add_node("validate_data", self.validate_data)

        # Define edges
        workflow.set_entry_point("fetch_data")
        workflow.add_edge("fetch_data", "validate_data")
        workflow.add_edge("validate_data", END)

        return workflow.compile()

    async def fetch_data(self, state: MultiAgentState) -> Dict[str, Any]:
        """Fetch user feedback data."""
        prompt = f"""Fetch user feedback data for: {state['task']}

List 3 sample feedback items in one sentence each."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "raw_data": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "data_fetch", "content": f"Fetched: {result.content}"}
            ]
        }

    async def validate_data(self, state: MultiAgentState) -> Dict[str, Any]:
        """Validate fetched data quality."""
        raw_data = state["context"].get("raw_data", "")

        prompt = f"""Validate data quality: {raw_data}

Is the data complete and usable? Answer in one sentence."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "results": {
                **state.get("results", {}),
                "fetched_data": f"{raw_data}\nValidation: {result.content}"
            },
            "messages": state.get("messages", []) + [
                {"role": "data_fetch", "content": f"Validated: {result.content}"}
            ]
        }


# ==============================================================================
# Agent 3: DataAnalysisAgent - Sentiment analysis and insights
# ==============================================================================

class DataAnalysisAgent(BaseLangGraphAgent):
    """Performs sentiment analysis and generates insights.

    Workflow:
    1. analyze_sentiment - Analyze user sentiment
    2. generate_insights - Generate actionable insights
    """

    def _build_graph(self):
        """Build data analysis workflow graph."""
        workflow = StateGraph(MultiAgentState)

        # Define nodes
        workflow.add_node("analyze_sentiment", self.analyze_sentiment)
        workflow.add_node("generate_insights", self.generate_insights)

        # Define edges
        workflow.set_entry_point("analyze_sentiment")
        workflow.add_edge("analyze_sentiment", "generate_insights")
        workflow.add_edge("generate_insights", END)

        return workflow.compile()

    async def analyze_sentiment(self, state: MultiAgentState) -> Dict[str, Any]:
        """Analyze sentiment in user feedback."""
        data = state.get("results", {}).get("fetched_data", "No data")

        prompt = f"""Analyze sentiment in feedback: {data}

Identify overall sentiment and key themes in 2 sentences."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "context": {
                **state.get("context", {}),
                "sentiment_analysis": result.content
            },
            "messages": state.get("messages", []) + [
                {"role": "analysis", "content": f"Sentiment: {result.content}"}
            ]
        }

    async def generate_insights(self, state: MultiAgentState) -> Dict[str, Any]:
        """Generate actionable insights from analysis."""
        sentiment = state["context"].get("sentiment_analysis", "")

        prompt = f"""Generate insights from: {sentiment}

Provide 2 actionable recommendations in one sentence each."""

        result = await self.llm.ainvoke(prompt, config={"callbacks": self.callbacks})

        return {
            "results": {
                **state.get("results", {}),
                "insights": f"Sentiment: {sentiment}\nRecommendations: {result.content}"
            },
            "messages": state.get("messages", []) + [
                {"role": "analysis", "content": f"Insights: {result.content}"}
            ]
        }


# ==============================================================================
# Scenario Runner
# ==============================================================================

async def run_data_pipeline_scenario():
    """Run the data pipeline multi-agent scenario.

    Workflow:
    1. Coordinator initializes pipeline
    2. DataFetch agent retrieves feedback data
    3. DataAnalysis agent performs sentiment analysis
    4. Coordinator generates final report

    Returns:
        Dict with final results and trace data
    """
    # Setup tracing
    storage = TraceStorageBackend(db_conn=None, storage_dir="traces/data_pipeline_scenario")
    trace_client = TraceClient(storage)

    # Start main trace
    trace_id = trace_client.start_trace(
        trigger_type="multi_agent_workflow",
        triggered_by="data_pipeline_scenario",
        metadata={
            "scenario": "user_feedback_analysis",
            "agents": ["coordinator", "data_fetch", "data_analysis"],
            "workflow_type": "data_processing_pipeline"
        }
    )

    print(f"Started trace: {trace_id}")

    try:
        # Apply @traced_agent decorator to create traced instances
        TracedCoordinator = traced_agent(trace_client)(CoordinatorAgent)
        TracedDataFetch = traced_agent(trace_client)(DataFetchAgent)
        TracedDataAnalysis = traced_agent(trace_client)(DataAnalysisAgent)

        # Create agent instances
        coordinator = TracedCoordinator(
            agent_id="coordinator",
            role="Pipeline Coordinator",
            temperature=0.7
        )

        data_fetch = TracedDataFetch(
            agent_id="data_fetch",
            role="Data Fetcher",
            temperature=0.7
        )

        data_analysis = TracedDataAnalysis(
            agent_id="data_analysis",
            role="Data Analyst",
            temperature=0.7
        )

        # Initial task
        task = "Process user feedback data from mobile app reviews"

        # Step 1: Coordinator initializes pipeline
        print("\n=== Step 1: Pipeline Initialization ===")
        coord_result = await coordinator.run({"task": task})
        print(f"Config: {coord_result['context'].get('pipeline_config', 'N/A')}")

        # Step 2: Fetch data
        print("\n=== Step 2: Data Fetching ===")
        fetch_result = await data_fetch.run({
            "task": task,
            "context": coord_result["context"]
        })
        print(f"Data: {fetch_result['results'].get('fetched_data', 'N/A')}")

        # Step 3: Analyze data
        print("\n=== Step 3: Data Analysis ===")
        analysis_result = await data_analysis.run({
            "task": task,
            "context": coord_result["context"],
            "results": fetch_result["results"]
        })
        print(f"Insights: {analysis_result['results'].get('insights', 'N/A')}")

        # Step 4: Coordinator finalizes
        print("\n=== Step 4: Pipeline Finalization ===")
        final_result = await coordinator.run({
            "task": task,
            "context": coord_result["context"],
            "results": analysis_result["results"]
        })
        print(f"Report: {final_result['results'].get('pipeline_report', 'N/A')}")

        # Complete trace
        trace_client.complete_trace(
            status="completed",
            summary={
                "workflow": "user_feedback_analysis",
                "agents_executed": 3,
                "final_result": final_result["results"].get("pipeline_report", "")
            }
        )

        print(f"\n✓ Trace completed: {trace_id}")

        # Export to Jaeger
        print("\n=== Exporting to Jaeger ===")
        exporter = ZipkinExporter(service_name="data-pipeline-agents")

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
        print(f"\n✗ Pipeline failed: {e}")
        raise


# ==============================================================================
# Main Entry Point
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Data Pipeline Multi-Agent Scenario")
    print("=" * 80)
    print("\nThis demonstrates a realistic data processing pipeline workflow")
    print("with automatic tracing via @traced_agent decorator.\n")

    result = asyncio.run(run_data_pipeline_scenario())

    print("\n" + "=" * 80)
    print("Scenario Complete!")
    print("=" * 80)
    print(f"\nTrace ID: {result['trace_id']}")
    print(f"Status: {result['status']}")
    print("\nView traces in Jaeger UI at: http://localhost:16686")
    print("\nSearch for service: 'data-pipeline-agents'")
