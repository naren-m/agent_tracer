"""LangChain callback handler for automatic tracing integration.

This module provides ComprehensiveTracingCallback that intercepts LangGraph
events and automatically captures node execution, LLM calls, and state transitions
without requiring any tracing code in the agent implementation.
"""

from typing import Any, Dict, List, Optional
import re
import logging
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from agent_tracer import TraceClient
from models.decision_models import AgentDecision, DecisionCriteria
from utils.fail_safe import FailSafeTraceClient
from context.context_propagation import set_current_trace_id

# Module logger
logger = logging.getLogger(__name__)


def _parse_decision_from_text(text: str) -> AgentDecision:
    """Parse LLM response text into AgentDecision structure.

    Uses simple heuristics to extract:
    - Action: First verb phrase or sentence
    - Reasoning: Text after "because", "since", etc.
    - Confidence: Based on confidence keywords

    Args:
        text: Raw LLM response text

    Returns:
        AgentDecision with parsed fields
    """
    # Extract action (first meaningful sentence/verb)
    action_match = re.search(r"(?:I will|I'll|will|should|must)\s+(.+?)(?:\.|because|since)", text, re.IGNORECASE)
    action = action_match.group(1).strip() if action_match else "unknown"

    # Extract reasoning (text after "because", "since", etc.)
    reasoning_match = re.search(r"(?:because|since|as|due to)\s+(.+?)(?:\.|$)", text, re.IGNORECASE | re.DOTALL)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else text[:200]

    # Determine confidence from keywords
    confidence = 0.5  # Default medium confidence

    high_confidence_words = ["very confident", "certain", "sure", "definitely", "clearly"]
    low_confidence_words = ["might", "maybe", "perhaps", "possibly", "uncertain", "not sure"]

    text_lower = text.lower()

    # Count confidence indicators
    high_count = sum(1 for word in high_confidence_words if word in text_lower)
    low_count = sum(1 for word in low_confidence_words if word in text_lower)

    # Determine confidence based on counts
    if high_count > low_count:
        confidence = 0.9
    elif low_count > high_count:
        confidence = 0.3

    # Build decision object
    return AgentDecision(
        action=action,
        reasoning=reasoning,
        confidence=confidence,
        alternatives_considered=[],  # Could enhance with NLP parsing
        criteria=[
            DecisionCriteria(
                factor="llm_analysis",
                score=confidence,
                weight=1.0,
                reasoning="Parsed from LLM response"
            )
        ],
        context_used={"raw_text": text[:500]}  # Store snippet of raw text
    )


class ComprehensiveTracingCallback(BaseCallbackHandler):
    """LangChain callback handler that automatically traces agent execution.

    Intercepts LangGraph events to capture:
    - Node execution (on_chain_start/end)
    - LLM calls with context (on_llm_start/end)
    - State transitions and decisions

    The callback is fail-safe: any errors in tracing will be logged but won't
    crash the agent execution.
    """

    def __init__(self, trace_client: TraceClient, auto_parse_decisions: bool = True, fail_safe: bool = True):
        """Initialize callback with trace client and configuration.

        Args:
            trace_client: TraceClient instance for recording traces
            auto_parse_decisions: If True, parse LLM responses into AgentDecision.
                                If False, just log raw response without parsing.
            fail_safe: If True, wrap trace_client in FailSafeTraceClient to prevent crashes
        """
        super().__init__()
        self.trace_client = FailSafeTraceClient(trace_client) if fail_safe else trace_client
        self.auto_parse_decisions = auto_parse_decisions
        self._run_id_to_span: Dict[str, Any] = {}  # Map run_id to span context manager
        self._llm_context: Optional[Dict[str, Any]] = None  # Store current LLM context

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Capture node execution start.

        Args:
            serialized: Chain configuration (contains node name)
            inputs: Input data to the node
            run_id: Unique ID for this execution
            parent_run_id: Parent execution ID if nested
            tags: Optional tags
            metadata: Optional metadata
        """
        try:
            node_name = serialized.get("name", "unknown_node") if serialized else "unknown_node"

            # Start trace on first node (if not already started)
            if str(run_id) not in self._run_id_to_span:
                trace_id = self.trace_client.start_trace(
                    trigger_type="langchain_node",
                    triggered_by=node_name,
                    metadata={
                        "run_id": str(run_id),
                        "parent_run_id": str(parent_run_id) if parent_run_id else None,
                        "tags": tags or [],
                    }
                )
                set_current_trace_id(trace_id)

            # Enter span context for this node
            span_ctx = self.trace_client.span(node_name, "node")
            span_ctx.__enter__()

            # Store span context manager for later cleanup
            self._run_id_to_span[str(run_id)] = span_ctx

            # Add input data as artifact
            self.trace_client.add_artifact(
                f"Node Input: {node_name}",
                "input",
                inputs
            )

        except Exception as e:
            # Fail-safe: log but don't crash
            logger.exception(f"Error in on_chain_start: {e}")

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        """Capture node execution end.

        Args:
            outputs: Output data from the node
            run_id: Unique ID for this execution
        """
        try:
            # Exit the span context for this node
            if str(run_id) in self._run_id_to_span:
                span_ctx = self._run_id_to_span.pop(str(run_id))

                # Add output data as artifact before exiting span
                self.trace_client.add_artifact(
                    "Node Output",
                    "output",
                    outputs
                )

                # Exit span context
                span_ctx.__exit__(None, None, None)

        except Exception as e:
            logger.exception(f"Error in on_chain_end: {e}")

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Capture LLM call start with context.

        Args:
            serialized: LLM configuration
            prompts: Prompt texts sent to LLM
            run_id: Unique ID for this LLM call
            parent_run_id: Parent execution ID
            tags: Optional tags
            metadata: Optional metadata
        """
        try:
            model_name = serialized.get("name", "unknown_llm")

            # Store LLM context for use in on_llm_end
            self._llm_context = {
                "prompts": prompts,
                "model": model_name,
                "run_id": str(run_id),
                "parent_run_id": str(parent_run_id) if parent_run_id else None,
                "tags": tags or [],
                "metadata": metadata or {},
            }

            # Enter span context for LLM call
            span_ctx = self.trace_client.span(model_name, "llm")
            span_ctx.__enter__()

            # Store span context manager
            self._run_id_to_span[str(run_id)] = span_ctx

            # Add prompts as artifact
            self.trace_client.add_artifact(
                f"LLM Prompts: {model_name}",
                "prompts",
                {"prompts": prompts, "model": model_name, "prompt_count": len(prompts)}
            )

        except Exception as e:
            logger.exception(f"Error in on_llm_start: {e}")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        """Capture LLM call end and optionally parse response into AgentDecision.

        Args:
            response: LLM response with generations
            run_id: Unique ID for this LLM call
        """
        try:
            # Extract response text
            response_text = None
            if response.generations and len(response.generations) > 0:
                if len(response.generations[0]) > 0:
                    response_text = response.generations[0][0].text

                    # Add response as artifact
                    self.trace_client.add_artifact(
                        "LLM Response",
                        "response",
                        {"text": response_text, "context": self._llm_context}
                    )

                    if self.auto_parse_decisions:
                        # Parse into AgentDecision and store
                        decision = _parse_decision_from_text(response_text)

                        # Enrich decision with LLM context
                        if self._llm_context:
                            decision.context_used.update({
                                "model": self._llm_context.get("model"),
                                "prompts": self._llm_context.get("prompts"),
                                "metadata": self._llm_context.get("metadata"),
                            })

                        # Store decision as artifact
                        self.trace_client.add_decision(
                            name="LLM Decision",
                            reasoning=decision.reasoning,
                            criteria=[
                                {
                                    "factor": c.factor,
                                    "score": c.score,
                                    "weight": c.weight,
                                    "reasoning": c.reasoning
                                }
                                for c in decision.criteria
                            ],
                            final_score=decision.confidence
                        )

            # Clear LLM context after processing response
            self._llm_context = None

            # Exit the span context for this LLM call
            if str(run_id) in self._run_id_to_span:
                span_ctx = self._run_id_to_span.pop(str(run_id))
                span_ctx.__exit__(None, None, None)

        except Exception as e:
            logger.exception(f"Error in on_llm_end: {e}")

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        """Handle LLM errors gracefully.

        Args:
            error: Exception that occurred
            run_id: Unique ID for this LLM call
        """
        try:
            # Add error as artifact
            self.trace_client.add_artifact(
                "LLM Error",
                "error",
                {"error": str(error), "type": type(error).__name__}
            )

            # Clear LLM context on error
            self._llm_context = None

            # Exit span even on error
            if str(run_id) in self._run_id_to_span:
                span_ctx = self._run_id_to_span.pop(str(run_id))
                span_ctx.__exit__(type(error), error, None)

        except Exception as e:
            logger.exception(f"Error in on_llm_error: {e}")

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        """Handle chain errors gracefully.

        Args:
            error: Exception that occurred
            run_id: Unique ID for this execution
        """
        try:
            # Add error as artifact
            self.trace_client.add_artifact(
                "Chain Error",
                "error",
                {"error": str(error), "type": type(error).__name__}
            )

            # Exit span even on error
            if str(run_id) in self._run_id_to_span:
                span_ctx = self._run_id_to_span.pop(str(run_id))
                span_ctx.__exit__(type(error), error, None)

        except Exception as e:
            logger.exception(f"Error in on_chain_error: {e}")
