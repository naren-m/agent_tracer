"""Integration tests for decorator flow with real TraceClient."""

import pytest
import json
from pathlib import Path

from agent_tracer.decorators import traced_agent, traced_function


@pytest.mark.asyncio
async def test_traced_agent_creates_complete_trace(real_trace_client, storage_dir_path):
    """Integration test: traced_agent creates complete trace stored to disk."""
    
    @traced_agent(real_trace_client)
    class TestAgent:
        async def run(self, task):
            return {"result": "success", "task": task}
    
    # Execute agent
    agent = TestAgent()
    result = await agent.run({"input": "test_task"})
    
    # Verify agent execution
    assert result["result"] == "success"
    assert result["task"]["input"] == "test_task"
    
    # Verify trace was written to storage
    # Find trace_id from storage directory
    trace_dirs = list(storage_dir_path.glob("*/"))
    assert len(trace_dirs) == 1, f"Expected 1 trace directory, found {len(trace_dirs)}"
    
    trace_id = trace_dirs[0].name
    trace_file = trace_dirs[0] / "trace.json"
    
    assert trace_file.exists(), f"Trace file not found at {trace_file}"
    
    # Read and verify trace content
    with open(trace_file) as f:
        trace_data = json.load(f)
    
    assert trace_data["trace_id"] == trace_id
    assert trace_data["trace_type"] == "agent_execution"
    assert trace_data["status"] == "completed"
    assert trace_data["trigger"]["type"] == "agent_task"
    assert "TestAgent" in trace_data["metadata"]["agent"]
    
    # Verify spans exist
    assert len(trace_data["spans"]) >= 1
    root_span = trace_data["spans"][0]
    assert root_span["name"] == "TestAgent Execution"
    assert root_span["type"] == "agent"
    assert root_span["status"] == "completed"


@pytest.mark.asyncio
async def test_nested_decorators_create_span_hierarchy(real_trace_client, storage_dir_path):
    """Integration test: nested traced_function calls create proper span hierarchy."""
    
    @traced_agent(real_trace_client)
    class NestedAgent:
        @traced_function(real_trace_client, "helper_function")
        async def helper(self, value):
            return value * 2
        
        @traced_function(real_trace_client, "processing_step")
        async def process(self, data):
            # Call nested helper
            processed = await self.helper(data["value"])
            return {"processed": processed}
        
        async def run(self, task):
            # Call process which calls helper
            result = await self.process(task)
            return {"result": result}
    
    # Execute with nested calls
    agent = NestedAgent()
    result = await agent.run({"value": 5})
    
    # Verify result
    assert result["result"]["processed"] == 10
    
    # Verify trace storage
    trace_dirs = list(storage_dir_path.glob("*/"))
    assert len(trace_dirs) == 1
    
    trace_file = trace_dirs[0] / "trace.json"
    with open(trace_file) as f:
        trace_data = json.load(f)
    
    # Verify span hierarchy
    spans = trace_data["spans"]
    assert len(spans) == 3, f"Expected 3 spans (run, process, helper), got {len(spans)}"
    
    # Find spans by name
    span_by_name = {s["name"]: s for s in spans}
    
    assert "NestedAgent Execution" in span_by_name
    assert "processing_step" in span_by_name
    assert "helper_function" in span_by_name
    
    # Verify parent-child relationships
    run_span = span_by_name["NestedAgent Execution"]
    process_span = span_by_name["processing_step"]
    helper_span = span_by_name["helper_function"]
    
    # process should be child of run
    assert process_span["parent_span_id"] == run_span["span_id"]
    
    # helper should be child of process
    assert helper_span["parent_span_id"] == process_span["span_id"]
    
    # All should be from same trace
    assert run_span["trace_id"] == trace_data["trace_id"]
    assert process_span["trace_id"] == trace_data["trace_id"]
    assert helper_span["trace_id"] == trace_data["trace_id"]


@pytest.mark.asyncio
async def test_traced_agent_handles_errors_with_storage(real_trace_client, storage_dir_path):
    """Integration test: errors are properly traced and stored."""
    
    @traced_agent(real_trace_client)
    class ErrorAgent:
        async def run(self, task):
            raise ValueError("Intentional test error")
    
    # Execute agent (expect error)
    agent = ErrorAgent()
    with pytest.raises(ValueError, match="Intentional test error"):
        await agent.run({"input": "trigger_error"})
    
    # Verify trace was still written
    trace_dirs = list(storage_dir_path.glob("*/"))
    assert len(trace_dirs) == 1
    
    trace_file = trace_dirs[0] / "trace.json"
    assert trace_file.exists()
    
    with open(trace_file) as f:
        trace_data = json.load(f)
    
    # Verify error is traced
    assert trace_data["status"] == "failed"
    
    root_span = trace_data["spans"][0]
    assert root_span["status"] == "failed"
    assert "error" in root_span
    assert root_span["error"]["type"] == "ValueError"
    assert "Intentional test error" in root_span["error"]["message"]
