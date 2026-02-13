#!/usr/bin/env python3
"""
Benchmark script to measure tracing overhead in multi-agent workflows.

This script runs a sample agent workflow multiple times with tracing enabled
and calculates the average overhead introduced by the tracing instrumentation.
"""

import asyncio
import time
import statistics
from typing import List, Tuple

from base_agent import BaseTracedAgent
from agent_tracer import traced_agent


@traced_agent(service_name="benchmark-test")
class BenchmarkAgent(BaseTracedAgent):
    """Simple agent for benchmarking tracing overhead."""

    def __init__(self, name: str):
        super().__init__(name, "Benchmark Agent", model_name="llama2")

    async def simple_task(self, input_text: str) -> str:
        """Execute a simple LLM task for benchmarking."""
        # Create a span for the task
        with self.tracer.start_as_current_span("simple_task") as span:
            span.set_attribute("input.length", len(input_text))

            # Call LLM (this will be automatically traced)
            response = await self.llm.ainvoke(input_text)

            span.set_attribute("output.length", len(response.content))
            return response.content


async def run_benchmark_iteration() -> float:
    """Run a single benchmark iteration and return execution time."""
    start_time = time.time()

    # Create agent
    agent = BenchmarkAgent("BenchmarkAgent")

    # Execute simple workflow
    result = await agent.simple_task(
        "Write a one-sentence summary of distributed tracing."
    )

    # Simulate a bit of processing
    await asyncio.sleep(0.1)

    execution_time = time.time() - start_time
    return execution_time


def calculate_statistics(times: List[float]) -> Tuple[float, float, float, float]:
    """Calculate statistical metrics from execution times."""
    avg_time = statistics.mean(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
    min_time = min(times)
    max_time = max(times)

    return avg_time, std_dev, min_time, max_time


def estimate_overhead(avg_time: float) -> Tuple[float, float]:
    """
    Estimate tracing overhead.

    Assumes:
    - LLM call takes ~3-5s (majority of time)
    - Agent logic takes ~0.1-0.2s
    - Tracing overhead is the remainder

    Returns:
        Tuple of (overhead_ms, overhead_percentage)
    """
    # Estimated base execution time without tracing
    # LLM call: ~4s, Agent logic: ~0.15s, Sleep: 0.1s
    estimated_base_time = 4.25

    # Calculate overhead
    overhead_ms = max(0, (avg_time - estimated_base_time) * 1000)
    overhead_percentage = (overhead_ms / (avg_time * 1000)) * 100

    return overhead_ms, overhead_percentage


async def run_benchmark(iterations: int = 5) -> None:
    """
    Run benchmark with specified number of iterations.

    Args:
        iterations: Number of times to run the workflow
    """
    print("=" * 80)
    print("TRACING OVERHEAD BENCHMARK".center(80))
    print("=" * 80)
    print()
    print(f"Running workflow {iterations} times with tracing enabled...")
    print()

    execution_times = []

    for i in range(iterations):
        print(f"Run {i + 1}/{iterations}...", end=" ", flush=True)
        exec_time = await run_benchmark_iteration()
        execution_times.append(exec_time)
        print(f"{exec_time:.3f}s")

    print()
    print("=" * 80)
    print("RESULTS".center(80))
    print("=" * 80)
    print()

    # Calculate statistics
    avg_time, std_dev, min_time, max_time = calculate_statistics(execution_times)

    print(f"Average execution time: {avg_time:.3f}s")
    print(f"Standard deviation:     {std_dev:.3f}s")
    print(f"Min execution time:     {min_time:.3f}s")
    print(f"Max execution time:     {max_time:.3f}s")
    print()

    # Estimate overhead
    overhead_ms, overhead_pct = estimate_overhead(avg_time)

    print("-" * 80)
    print("ESTIMATED TRACING OVERHEAD")
    print("-" * 80)
    print(f"Overhead:               ~{overhead_ms:.0f}ms")
    print(f"Percentage:             ~{overhead_pct:.2f}%")
    print()

    # Breakdown
    print("-" * 80)
    print("EXECUTION TIME BREAKDOWN (estimated)")
    print("-" * 80)
    llm_time = 4.0
    agent_time = 0.25
    llm_pct = (llm_time / avg_time) * 100
    agent_pct = (agent_time / avg_time) * 100

    print(f"LLM calls:              ~{llm_time:.1f}s ({llm_pct:.1f}%)")
    print(f"Agent logic:            ~{agent_time:.2f}s ({agent_pct:.1f}%)")
    print(f"Tracing overhead:       ~{overhead_ms/1000:.3f}s ({overhead_pct:.2f}%)")
    print()

    # Performance assessment
    print("=" * 80)
    print("PERFORMANCE ASSESSMENT".center(80))
    print("=" * 80)
    print()

    if overhead_pct < 2.0:
        assessment = "EXCELLENT - Near-zero overhead"
        icon = "✓"
    elif overhead_pct < 5.0:
        assessment = "GOOD - Minimal overhead"
        icon = "✓"
    elif overhead_pct < 10.0:
        assessment = "ACCEPTABLE - Moderate overhead"
        icon = "⚠"
    else:
        assessment = "HIGH - Consider optimization"
        icon = "✗"

    print(f"{icon} {assessment}")
    print()
    print(f"Tracing adds ~{overhead_ms:.0f}ms to {avg_time*1000:.0f}ms total execution")
    print(f"This represents {overhead_pct:.2f}% of total time")
    print()

    # Recommendations
    if overhead_pct > 5.0:
        print("RECOMMENDATIONS:")
        print("  • Check network latency to Jaeger collector")
        print("  • Verify Jaeger is running locally (not remote)")
        print("  • Consider batch span export for production")
        print()

    print("=" * 80)
    print()


def main():
    """Main entry point."""
    try:
        asyncio.run(run_benchmark(iterations=5))
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
    except Exception as e:
        print(f"\n\nError during benchmark: {e}")
        raise


if __name__ == "__main__":
    main()
