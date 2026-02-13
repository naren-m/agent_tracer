#!/usr/bin/env python3
"""
Main runner script for all multi-agent tracing scenarios.

This script runs all three demonstration scenarios:
1. Software Development Team
2. Data Pipeline Processing
3. Incident Response Team

Each scenario demonstrates zero-code distributed tracing with the @traced_agent decorator.
"""

import sys
import asyncio
from typing import Dict, List

from scenarios.software_dev import run_software_dev_scenario
from scenarios.data_pipeline import run_data_pipeline_scenario
from scenarios.incident_response import run_incident_response_scenario


def print_banner(title: str) -> None:
    """Print a formatted banner for scenario sections."""
    width = 80
    print("\n" + "=" * width)
    print(f"  {title}".center(width))
    print("=" * width + "\n")


def print_summary(results: List[Dict[str, any]]) -> None:
    """Print execution summary with Jaeger links."""
    print_banner("EXECUTION SUMMARY")

    print("Scenario Results:")
    print("-" * 80)

    for result in results:
        status = "✓" if result["success"] else "✗"
        print(f"{status} {result['name']}")
        if result["success"]:
            print(f"  Trace ID: {result['trace_id']}")
        else:
            print(f"  Error: {result['error']}")
        print()

    # Print Jaeger access information
    print("\n" + "-" * 80)
    print("View Traces in Jaeger UI:")
    print("-" * 80)
    print("  URL: http://localhost:16686")
    print("\n  Services to explore:")
    print("    • software-dev-team")
    print("    • data-pipeline")
    print("    • incident-response-team")
    print("\n  Key features to check:")
    print("    • Span hierarchy (agent → task → LLM)")
    print("    • LLM token metrics (prompt/completion tokens)")
    print("    • Agent collaboration patterns")
    print("    • Error propagation and handling")
    print("=" * 80 + "\n")


async def main() -> int:
    """Run all scenarios and report results."""
    print_banner("MULTI-AGENT TRACING DEMONSTRATIONS")
    print("Running all scenarios with distributed tracing enabled...")
    print("Check Jaeger UI at http://localhost:16686 for real-time traces\n")

    results = []

    # Scenario 1: Software Development Team
    print_banner("Scenario 1: Software Development Team")
    try:
        result = await run_software_dev_scenario()
        results.append({
            "name": "Software Development Team",
            "success": True,
            "trace_id": result["trace_id"],
            "duration": 0.0  # Duration not tracked in current implementation
        })
        print(f"✓ Completed (Trace ID: {result['trace_id']})")
    except Exception as e:
        results.append({
            "name": "Software Development Team",
            "success": False,
            "error": str(e)
        })
        print(f"✗ Failed: {e}")

    # Scenario 2: Data Pipeline Processing
    print_banner("Scenario 2: Data Pipeline Processing")
    try:
        result = await run_data_pipeline_scenario()
        results.append({
            "name": "Data Pipeline Processing",
            "success": True,
            "trace_id": result["trace_id"],
            "duration": 0.0  # Duration not tracked in current implementation
        })
        print(f"✓ Completed (Trace ID: {result['trace_id']})")
    except Exception as e:
        results.append({
            "name": "Data Pipeline Processing",
            "success": False,
            "error": str(e)
        })
        print(f"✗ Failed: {e}")

    # Scenario 3: Incident Response Team
    print_banner("Scenario 3: Incident Response Team")
    try:
        result = await run_incident_response_scenario()
        results.append({
            "name": "Incident Response Team",
            "success": True,
            "trace_id": result["trace_id"],
            "duration": 0.0  # Duration not tracked in current implementation
        })
        print(f"✓ Completed (Trace ID: {result['trace_id']})")
    except Exception as e:
        results.append({
            "name": "Incident Response Team",
            "success": False,
            "error": str(e)
        })
        print(f"✗ Failed: {e}")

    # Print summary
    print_summary(results)

    # Return exit code based on results
    failed = sum(1 for r in results if not r["success"])
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
