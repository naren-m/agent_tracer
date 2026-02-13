"""Test decision model structures."""

import pytest
from pydantic import ValidationError


def test_decision_criteria_validation():
    """Test DecisionCriteria validates scores."""
    from agent_tracer.decision_models import DecisionCriteria

    # Should fail - score out of range
    with pytest.raises(ValidationError):
        DecisionCriteria(factor="test", score=1.5)


def test_agent_decision_structure():
    """Test AgentDecision has required fields."""
    from agent_tracer.decision_models import AgentDecision

    decision = AgentDecision(
        action="test_action",
        reasoning="test reasoning",
        confidence=0.85,
        alternatives_considered=["alt1"],
        criteria=[],
        context_used={}
    )

    assert decision.action == "test_action"
    assert decision.confidence == 0.85


def test_llm_context_structure():
    """Test LLMContext captures required fields."""
    from agent_tracer.decision_models import LLMContext

    context = LLMContext(
        model="gpt-4",
        temperature=0.7,
        messages=[{"role": "user", "content": "test"}],
        prompt_tokens=10,
        tools_available=[],
        agent_state={}
    )

    assert context.model == "gpt-4"
    assert len(context.messages) == 1


def test_decision_criteria_weight_validation():
    """Test DecisionCriteria validates weight."""
    from agent_tracer.decision_models import DecisionCriteria

    # Should fail - weight out of range
    with pytest.raises(ValidationError):
        DecisionCriteria(factor="test", score=0.5, weight=1.5)


def test_agent_decision_confidence_validation():
    """Test AgentDecision validates confidence."""
    from agent_tracer.decision_models import AgentDecision

    # Should fail - confidence out of range
    with pytest.raises(ValidationError):
        AgentDecision(
            action="test",
            reasoning="test",
            confidence=1.5,  # Invalid
            alternatives_considered=[],
            criteria=[],
            context_used={}
        )


def test_llm_context_temperature_validation():
    """Test LLMContext validates temperature range."""
    from agent_tracer.decision_models import LLMContext

    # Should fail - temperature out of range
    with pytest.raises(ValidationError):
        LLMContext(
            model="gpt-4",
            temperature=3.0,  # Invalid (> 2.0)
            messages=[],
            prompt_tokens=10,
        )


def test_llm_context_negative_tokens_validation():
    """Test LLMContext rejects negative token counts."""
    from agent_tracer.decision_models import LLMContext

    # Should fail - negative tokens
    with pytest.raises(ValidationError):
        LLMContext(
            model="gpt-4",
            temperature=0.7,
            messages=[],
            prompt_tokens=-10,  # Invalid
        )
