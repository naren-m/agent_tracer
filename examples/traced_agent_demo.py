"""Demo showing @traced_agent usage with AgentDecision extraction.

This example demonstrates:
1. Basic agent tracing with @traced_agent decorator
2. LLM context capture with LLMContextCaptureMixin
3. AgentDecision extraction with criteria and reasoning
4. Fail-safe tracing (errors don't break the agent)

Run with: python -m a2a_traced.examples.traced_agent_demo
"""

import asyncio
from pathlib import Path
from agent_tracer import TraceClient
from agent_tracer.storage import TraceStorageBackend
from agent_tracer.decorators import traced_agent, traced_llm_call
from agent_tracer.decision_models import AgentDecision, DecisionCriteria, LLMContext
from agent_tracer.context_capture import LLMContextCaptureMixin


# Initialize tracer with file-based storage
traces_dir = Path("./traces")
traces_dir.mkdir(exist_ok=True)
storage_backend = TraceStorageBackend(db_conn=None, storage_dir=str(traces_dir))
trace_client = TraceClient(storage_backend)


# Mock agent class demonstrating tracing
@traced_agent(trace_client, fail_safe=True)
class TaskPlannerAgent(LLMContextCaptureMixin):
    """Example agent that plans tasks with LLM decision making."""

    def __init__(self, name: str = "TaskPlanner"):
        self.name = name

    @traced_llm_call(trace_client, fail_safe=True)
    async def call_llm(self, prompt: str) -> AgentDecision:
        """Mock LLM call that returns a structured decision.

        In a real agent, this would call an actual LLM API.
        Here we simulate the response for demo purposes.
        """
        # Simulate LLM processing
        await asyncio.sleep(0.1)

        # Return a structured decision
        return AgentDecision(
            action="create_subtasks",
            reasoning=(
                "The task is complex and requires breaking down into smaller steps. "
                "Parallel execution of subtasks will improve efficiency."
            ),
            confidence=0.87,
            alternatives_considered=[
                "execute_sequentially",
                "delegate_to_specialist",
                "request_clarification"
            ],
            criteria=[
                DecisionCriteria(
                    factor="task_complexity",
                    score=0.9,
                    weight=0.4,
                    reasoning="High complexity requires decomposition"
                ),
                DecisionCriteria(
                    factor="time_constraints",
                    score=0.8,
                    weight=0.3,
                    reasoning="Tight deadline favors parallel execution"
                ),
                DecisionCriteria(
                    factor="resource_availability",
                    score=0.9,
                    weight=0.3,
                    reasoning="Sufficient resources for parallel work"
                )
            ],
            context_used={
                "task_description": "Implement feature X with tests and docs",
                "deadline": "2 days",
                "available_tools": ["code_editor", "test_runner", "doc_generator"]
            }
        )

    def _capture_context(self, args, kwargs) -> LLMContext:
        """Capture context before LLM call (used by LLMContextCaptureMixin)."""
        prompt = kwargs.get('prompt') or (args[0] if args else "")

        return LLMContext(
            model="gpt-4-turbo",
            temperature=0.7,
            messages=[
                {"role": "system", "content": "You are a task planning assistant."},
                {"role": "user", "content": prompt}
            ],
            prompt_tokens=len(prompt.split()) * 2,  # Rough estimate
            tools_available=["create_subtasks", "delegate", "execute"],
            agent_state={"name": self.name, "mode": "planning"}
        )

    async def run(self, task: dict):
        """Main agent execution (traced automatically by @traced_agent)."""
        print(f"\n[{self.name}] Processing task: {task.get('description')}")

        # Call LLM for decision making (traced by @traced_llm_call)
        prompt = f"Plan how to execute: {task.get('description')}"
        decision = await self.call_llm(prompt=prompt)

        # Execute the decided action
        print(f"[{self.name}] Decision: {decision.action}")
        print(f"[{self.name}] Confidence: {decision.confidence:.2f}")
        print(f"[{self.name}] Reasoning: {decision.reasoning[:80]}...")

        return {
            "status": "completed",
            "action": decision.action,
            "confidence": decision.confidence
        }


async def main():
    """Run the demo agent."""
    print("=" * 70)
    print("A2A Traced Agent Demo")
    print("=" * 70)

    # Create agent instance
    agent = TaskPlannerAgent(name="DemoAgent")

    # Create a task
    task = {
        "sender": "demo_system",
        "description": "Implement user authentication with tests and documentation"
    }

    # Run agent (tracing happens automatically)
    result = await agent.run(task)

    print(f"\n[Result] {result}")
    print("\n" + "=" * 70)
    print("Trace saved to: ./traces/")
    print("=" * 70)
    print("\nWhat was traced:")
    print("  ✓ Agent execution span")
    print("  ✓ LLM call with context capture")
    print("  ✓ Decision with criteria and reasoning")
    print("  ✓ Alternatives considered")
    print("  ✓ Full execution timeline")
    print("\nCheck the ./traces/ directory for the complete trace files.")


if __name__ == "__main__":
    asyncio.run(main())
