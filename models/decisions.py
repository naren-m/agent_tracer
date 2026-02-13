"""Pydantic models for agent decisions and LLM context."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DecisionCriteria(BaseModel):
    """Evaluation criteria for a decision."""

    factor: str = Field(description="The evaluation factor")
    score: float = Field(ge=0.0, le=1.0, description="Score for this factor")
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Weight of this factor")
    reasoning: Optional[str] = Field(default=None, description="Why this score")


class AgentDecision(BaseModel):
    """Structured decision output from an agent."""

    action: str = Field(description="The action/choice selected")
    reasoning: str = Field(description="Why this action was chosen")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in decision")
    alternatives_considered: List[str] = Field(
        description="Other options that were evaluated"
    )
    criteria: List[DecisionCriteria] = Field(
        description="Evaluation criteria used"
    )
    context_used: Dict[str, Any] = Field(
        description="What information was considered"
    )


class LLMContext(BaseModel):
    """Context provided to LLM for decision making."""

    model: str = Field(description="LLM model name")
    temperature: float = Field(ge=0.0, le=2.0, description="Temperature setting")
    messages: List[Dict[str, str]] = Field(description="Conversation messages")
    prompt_tokens: int = Field(ge=0, description="Estimated prompt tokens")
    tools_available: List[str] = Field(default_factory=list, description="Available tools")
    agent_state: Dict[str, Any] = Field(default_factory=dict, description="Agent state")
