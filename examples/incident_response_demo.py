#!/usr/bin/env python3
"""Production Incident Response Demo.

A realistic multi-agent scenario where 4 agents collaborate to diagnose
and fix a production API outage. Agents talk to each other 12+ times
under a single unified trace.

Agents:
    - IncidentCommander: Orchestrates the response, decides next actions
    - LogAnalyzer: Examines logs, identifies patterns, correlates events
    - InfraEngineer: Checks infrastructure health, applies fixes
    - SecurityAnalyst: Assesses security implications

Usage:
    python examples/incident_response_demo.py

Requires:
    - Ollama running locally with a llama model
    - pip install agent-tracer[all]
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from langchain_ollama import ChatOllama

from agent_tracer import TraceClient
from agent_tracer.storage import TraceStorageBackend
from agent_tracer.integrations.exporters import ZipkinExporter


# -- Data structures ----------------------------------------------------------

@dataclass
class Message:
    """A message between agents."""
    sender: str
    receiver: str
    content: str
    msg_type: str = "request"  # request, response, directive, report
    timestamp: float = field(default_factory=time.time)


@dataclass
class IncidentState:
    """Shared state for the incident."""
    incident_id: str
    severity: str
    alert: str
    messages: List[Message] = field(default_factory=list)
    findings: Dict[str, List[str]] = field(default_factory=dict)
    status: str = "open"
    resolution: str = ""


# -- Agent definitions --------------------------------------------------------

class BaseAgent:
    """Base agent with LLM capability and identity."""

    def __init__(self, name: str, role: str, llm: ChatOllama):
        self.name = name
        self.role = role
        self.llm = llm

    async def respond(self, prompt: str) -> str:
        """Get LLM response for a prompt."""
        system = (
            f"You are {self.name}, a {self.role}. "
            "You are responding in a production incident war room. "
            "Be concise -- 2-3 sentences max. Be specific and technical."
        )
        result = await self.llm.ainvoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
        )
        return result.content.strip()


class IncidentCommander(BaseAgent):
    def __init__(self, llm: ChatOllama):
        super().__init__(
            "Commander",
            "Incident Commander who orchestrates production incident response",
            llm,
        )


class LogAnalyzer(BaseAgent):
    def __init__(self, llm: ChatOllama):
        super().__init__(
            "LogAnalyzer",
            "Log Analysis Engineer who examines logs, metrics, and error patterns",
            llm,
        )


class InfraEngineer(BaseAgent):
    def __init__(self, llm: ChatOllama):
        super().__init__(
            "InfraEngineer",
            "Infrastructure Engineer who manages Kubernetes clusters and services",
            llm,
        )


class SecurityAnalyst(BaseAgent):
    def __init__(self, llm: ChatOllama):
        super().__init__(
            "SecurityAnalyst",
            "Security Analyst who assesses threats and validates changes",
            llm,
        )


# -- Interaction engine -------------------------------------------------------

async def agent_interaction(
    trace_client: TraceClient,
    sender: BaseAgent,
    receiver: BaseAgent,
    prompt: str,
    incident: IncidentState,
    interaction_num: int,
    msg_type: str = "request",
) -> str:
    """Execute a single agent-to-agent interaction with tracing.

    Creates a span for the interaction, records the prompt and response
    as steps, and logs the message exchange.
    """
    span_name = f"[{interaction_num}] {sender.name} -> {receiver.name}"

    with trace_client.span(span_name, "agent_interaction", agent_metadata={
        "sender": sender.name,
        "sender_role": sender.role,
        "receiver": receiver.name,
        "receiver_role": receiver.role,
        "interaction_num": interaction_num,
        "msg_type": msg_type,
    }):
        # Build context from recent messages
        recent = incident.messages[-4:] if incident.messages else []
        context_lines = [f"  [{m.sender} -> {m.receiver}]: {m.content[:120]}" for m in recent]
        context_str = "\n".join(context_lines) if context_lines else "  (start of incident)"

        full_prompt = (
            f"INCIDENT: {incident.alert}\n"
            f"SEVERITY: {incident.severity}\n"
            f"RECENT CONTEXT:\n{context_str}\n\n"
            f"MESSAGE FROM {sender.name}: {prompt}"
        )

        # Record the request
        trace_client.add_step(
            name=f"{sender.name} sends {msg_type}",
            step_type="agent_message",
            input_data={"from": sender.name, "to": receiver.name, "prompt": prompt},
            output_data={"status": "sent"},
        )

        # LLM call by receiving agent
        with trace_client.span(f"{receiver.name} LLM call", "llm", agent_metadata={
            "agent": receiver.name,
            "model": receiver.llm.model,
        }):
            response = await receiver.respond(full_prompt)

        # Record the response
        trace_client.add_step(
            name=f"{receiver.name} responds",
            step_type="agent_message",
            input_data={"from": receiver.name, "to": sender.name},
            output_data={"response": response[:500]},
        )

        # Track messages
        incident.messages.append(Message(sender.name, receiver.name, prompt, msg_type))
        incident.messages.append(Message(receiver.name, sender.name, response, "response"))

        # Track findings per agent
        if receiver.name not in incident.findings:
            incident.findings[receiver.name] = []
        incident.findings[receiver.name].append(response[:200])

    return response


# -- Scenario runner ----------------------------------------------------------

async def run_incident_response():
    """Run the full incident response scenario.

    12+ agent-to-agent interactions under a single unified trace.
    """
    # Setup
    storage_dir = "traces/incident_response_demo"
    storage = TraceStorageBackend(db_conn=None, storage_dir=storage_dir)
    trace_client = TraceClient(storage)

    # Detect Ollama model
    try:
        import ollama
        models = ollama.Client().list()
        model_names = [m.model for m in models.models]
        llama = next((n for n in model_names if "llama" in n.lower()), "llama3.2")
    except Exception:
        llama = "llama3.2"

    llm = ChatOllama(model=llama, temperature=0.7)

    # Create agents
    commander = IncidentCommander(llm)
    log_analyzer = LogAnalyzer(llm)
    infra_eng = InfraEngineer(llm)
    security = SecurityAnalyst(llm)

    # Create incident
    incident = IncidentState(
        incident_id="INC-2026-0214",
        severity="P1 - Critical",
        alert=(
            "ALERT: 500 error rate spike on /api/payments endpoint. "
            "Error rate jumped from 0.1% to 45% in the last 10 minutes. "
            "Customer-facing payment processing is failing. "
            "Last deployment: payment-service v2.4.1 deployed 2 hours ago."
        ),
    )

    # Start unified trace
    trace_id = trace_client.start_trace(
        trigger_type="pagerduty_alert",
        triggered_by="monitoring-system",
        metadata={
            "incident_id": incident.incident_id,
            "severity": incident.severity,
            "agents": ["Commander", "LogAnalyzer", "InfraEngineer", "SecurityAnalyst"],
            "workflow": "incident_response",
        },
    )

    print(f"{'='*70}")
    print(f"  INCIDENT RESPONSE: {incident.incident_id}")
    print(f"  Severity: {incident.severity}")
    print(f"  Trace ID: {trace_id}")
    print(f"{'='*70}\n")
    print(f"ALERT: {incident.alert}\n")

    try:
        # --- Phase 1: Triage (interactions 1-3) ---
        with trace_client.span("Phase 1: Triage", "phase"):
            print(f"\n{'─'*70}")
            print("PHASE 1: TRIAGE")
            print(f"{'─'*70}")

            # 1. Commander -> LogAnalyzer: Initial log investigation
            print(f"\n[1] Commander -> LogAnalyzer")
            r1 = await agent_interaction(
                trace_client, commander, log_analyzer,
                "We have a P1 on /api/payments. Error rate at 45%. "
                "Pull the last 30 minutes of logs and tell me what error patterns you see.",
                incident, 1, "directive",
            )
            print(f"    LogAnalyzer: {r1[:150]}...")

            # 2. Commander -> InfraEngineer: Check service health
            print(f"\n[2] Commander -> InfraEngineer")
            r2 = await agent_interaction(
                trace_client, commander, infra_eng,
                "Payment service is throwing 500s. Check pod health, resource usage, "
                "and any recent restarts in the payment-service namespace.",
                incident, 2, "directive",
            )
            print(f"    InfraEngineer: {r2[:150]}...")

            # 3. Commander -> SecurityAnalyst: Initial security check
            print(f"\n[3] Commander -> SecurityAnalyst")
            r3 = await agent_interaction(
                trace_client, commander, security,
                "We have a P1 incident on payments. Any unusual traffic patterns, "
                "auth failures, or signs of attack on the payment endpoints?",
                incident, 3, "request",
            )
            print(f"    SecurityAnalyst: {r3[:150]}...")

        # --- Phase 2: Investigation (interactions 4-7) ---
        with trace_client.span("Phase 2: Investigation", "phase"):
            print(f"\n{'─'*70}")
            print("PHASE 2: INVESTIGATION")
            print(f"{'─'*70}")

            # 4. Commander -> LogAnalyzer: Correlate with deployment
            print(f"\n[4] Commander -> LogAnalyzer")
            r4 = await agent_interaction(
                trace_client, commander, log_analyzer,
                "payment-service v2.4.1 was deployed 2 hours ago. "
                "Correlate the error spike timing with the deployment. "
                "Are we seeing OOMKilled or memory-related errors in the logs?",
                incident, 4, "request",
            )
            print(f"    LogAnalyzer: {r4[:150]}...")

            # 5. LogAnalyzer -> InfraEngineer: Request resource metrics
            print(f"\n[5] LogAnalyzer -> InfraEngineer")
            r5 = await agent_interaction(
                trace_client, log_analyzer, infra_eng,
                "I'm seeing memory growth patterns in the logs. "
                "Can you pull the memory usage graph for payment-service pods "
                "over the last 3 hours? Is it a steady climb or sudden spike?",
                incident, 5, "request",
            )
            print(f"    InfraEngineer: {r5[:150]}...")

            # 6. InfraEngineer -> LogAnalyzer: Share findings
            print(f"\n[6] InfraEngineer -> LogAnalyzer")
            r6 = await agent_interaction(
                trace_client, infra_eng, log_analyzer,
                "Memory is climbing steadily from 512MB to 1.8GB over 2 hours "
                "then OOMKilled. Each restart gets back to 512MB then climbs again. "
                "Classic memory leak. Can you check if v2.4.1 changed any connection pooling "
                "or caching code?",
                incident, 6, "request",
            )
            print(f"    LogAnalyzer: {r6[:150]}...")

            # 7. Commander -> SecurityAnalyst: Validate deployment
            print(f"\n[7] Commander -> SecurityAnalyst")
            r7 = await agent_interaction(
                trace_client, commander, security,
                "We suspect v2.4.1 introduced a memory leak. "
                "Was this deployment properly authorized? Check the CI/CD audit log "
                "and verify the deployer's identity and approval chain.",
                incident, 7, "request",
            )
            print(f"    SecurityAnalyst: {r7[:150]}...")

        # --- Phase 3: Mitigation (interactions 8-10) ---
        with trace_client.span("Phase 3: Mitigation", "phase"):
            print(f"\n{'─'*70}")
            print("PHASE 3: MITIGATION")
            print(f"{'─'*70}")

            # 8. Commander -> InfraEngineer: Apply hotfix
            print(f"\n[8] Commander -> InfraEngineer")
            r8 = await agent_interaction(
                trace_client, commander, infra_eng,
                "Confirmed memory leak in v2.4.1. Two-part fix: "
                "1) Immediately increase memory limit to 4GB to buy time. "
                "2) Prepare rollback to v2.3.9. Execute the memory limit increase now.",
                incident, 8, "directive",
            )
            print(f"    InfraEngineer: {r8[:150]}...")

            # 9. SecurityAnalyst -> InfraEngineer: Validate fix
            print(f"\n[9] SecurityAnalyst -> InfraEngineer")
            r9 = await agent_interaction(
                trace_client, security, infra_eng,
                "Before rolling back to v2.3.9, confirm that version has no known "
                "CVEs and the container image hash matches what's in our verified registry.",
                incident, 9, "request",
            )
            print(f"    InfraEngineer: {r9[:150]}...")

            # 10. Commander -> InfraEngineer: Execute rollback
            print(f"\n[10] Commander -> InfraEngineer")
            r10 = await agent_interaction(
                trace_client, commander, infra_eng,
                "Security has cleared v2.3.9. Execute the rollback now. "
                "Use canary deployment -- route 10% traffic first, then full rollout "
                "if error rate drops below 1%.",
                incident, 10, "directive",
            )
            print(f"    InfraEngineer: {r10[:150]}...")

        # --- Phase 4: Verification (interactions 11-13) ---
        with trace_client.span("Phase 4: Verification", "phase"):
            print(f"\n{'─'*70}")
            print("PHASE 4: VERIFICATION")
            print(f"{'─'*70}")

            # 11. Commander -> LogAnalyzer: Verify recovery
            print(f"\n[11] Commander -> LogAnalyzer")
            r11 = await agent_interaction(
                trace_client, commander, log_analyzer,
                "Rollback to v2.3.9 is in progress. Monitor the error rate and "
                "memory usage. Report when error rate drops below 1% and memory stabilizes.",
                incident, 11, "directive",
            )
            print(f"    LogAnalyzer: {r11[:150]}...")

            # 12. LogAnalyzer -> SecurityAnalyst: Anomaly check
            print(f"\n[12] LogAnalyzer -> SecurityAnalyst")
            r12 = await agent_interaction(
                trace_client, log_analyzer, security,
                "Error rate is dropping. During the outage window, I noticed some "
                "unusual retry patterns from 3 IP addresses that sent 10x normal volume. "
                "Could be legitimate retries or something else. Can you investigate?",
                incident, 12, "request",
            )
            print(f"    SecurityAnalyst: {r12[:150]}...")

            # 13. Commander -> LogAnalyzer: Final status
            print(f"\n[13] Commander -> LogAnalyzer")
            r13 = await agent_interaction(
                trace_client, commander, log_analyzer,
                "Give me the final numbers: current error rate, p99 latency, "
                "memory usage, and pod restart count in the last 15 minutes.",
                incident, 13, "request",
            )
            print(f"    LogAnalyzer: {r13[:150]}...")

        # --- Phase 5: Closure (interaction 14) ---
        with trace_client.span("Phase 5: Closure", "phase"):
            print(f"\n{'─'*70}")
            print("PHASE 5: CLOSURE")
            print(f"{'─'*70}")

            # 14. Commander -> all: Incident summary
            print(f"\n[14] Commander -> SecurityAnalyst (final clearance)")
            r14 = await agent_interaction(
                trace_client, commander, security,
                "Error rate is back to 0.1%, memory stable at 480MB. "
                "Give me your final security clearance to close this incident. "
                "Any recommendations for the post-mortem?",
                incident, 14, "request",
            )
            print(f"    SecurityAnalyst: {r14[:150]}...")

        # Close incident
        incident.status = "resolved"
        incident.resolution = (
            f"Memory leak in payment-service v2.4.1 caused OOM kills and 500 errors. "
            f"Rolled back to v2.3.9 via canary deployment. Error rate recovered to 0.1%. "
            f"Total interactions: {len(incident.messages)}"
        )

        # Complete trace
        trace_client.complete_trace(
            status="completed",
            summary={
                "incident_id": incident.incident_id,
                "resolution": incident.resolution,
                "total_interactions": len(incident.messages),
                "agents_involved": 4,
                "phases": ["triage", "investigation", "mitigation", "verification", "closure"],
                "root_cause": "memory leak in v2.4.1",
                "fix_applied": "rollback to v2.3.9",
            },
        )

        print(f"\n{'='*70}")
        print(f"  INCIDENT RESOLVED: {incident.incident_id}")
        print(f"  Total agent interactions: {len(incident.messages)}")
        print(f"  Resolution: {incident.resolution}")
        print(f"  Trace ID: {trace_id}")
        print(f"{'='*70}")

        return trace_id, incident

    except Exception as e:
        trace_client.complete_trace(
            status="failed",
            summary={"error": str(e), "type": type(e).__name__},
        )
        raise


async def export_and_display(trace_id: str, storage_dir: str):
    """Export trace to Jaeger and display summary."""
    # Find the trace file
    traces_path = Path(storage_dir)
    trace_dirs = list(traces_path.glob("trace_*"))

    if not trace_dirs:
        print("No traces found to export.")
        return

    exporter = ZipkinExporter(service_name="incident-response")

    for trace_dir in trace_dirs:
        trace_file = trace_dir / "trace.json"
        if trace_file.exists():
            with open(trace_file) as f:
                trace_data = json.load(f)

            # Print trace summary
            spans = trace_data.get("spans", [])
            print(f"\nTrace: {trace_data['trace_id']}")
            print(f"Duration: {trace_data.get('duration_ms', 0)}ms")
            print(f"Spans: {len(spans)}")
            print(f"Phases:")
            for span in spans:
                indent = "  " if span.get("parent_span_id") else ""
                steps = len(span.get("steps", []))
                print(f"  {indent}{span['name']} ({span['duration_ms']}ms, {steps} steps)")

            # Send to Jaeger
            success = exporter.send_to_jaeger(trace_data)
            if success:
                print(f"\nSent to Jaeger at http://localhost:16686")
                print(f"Search for service: 'incident-response'")


async def main():
    print("Starting Production Incident Response Demo...")
    print("Using Ollama for LLM calls (responses will be generated)\n")

    trace_id, incident = await run_incident_response()

    print("\n\nExporting to Jaeger...\n")
    await export_and_display(trace_id, "traces/incident_response_demo")


if __name__ == "__main__":
    asyncio.run(main())
