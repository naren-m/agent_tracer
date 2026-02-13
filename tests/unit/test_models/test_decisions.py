"""Tests for decision models."""

import pytest
from pydantic import ValidationError
from agent_tracer.models import AgentDecision, DecisionCriteria, LLMContext


def test_agent_decision_creation():
    """Test creating an AgentDecision with all required fields."""
    criteria = [
        DecisionCriteria(
            factor="cost",
            score=0.8,
            weight=0.5,
            reasoning="Lower cost is better"
        ),
        DecisionCriteria(
            factor="performance",
            score=0.9,
            weight=0.5,
            reasoning="Fast execution time"
        )
    ]

    decision = AgentDecision(
        action="use_cache",
        reasoning="Cache provides best balance of cost and performance",
        confidence=0.85,
        alternatives_considered=["direct_api_call", "batch_request"],
        criteria=criteria,
        context_used={
            "cache_hit_rate": 0.75,
            "api_latency": 200,
            "cost_per_request": 0.001
        }
    )

    assert decision.action == "use_cache"
    assert decision.confidence == 0.85
    assert len(decision.criteria) == 2
    assert len(decision.alternatives_considered) == 2
    assert "cache_hit_rate" in decision.context_used


def test_llm_context_minimal():
    """Test creating an LLMContext with minimal required fields."""
    context = LLMContext(
        model="gpt-4",
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "What is 2+2?"}
        ],
        prompt_tokens=25
    )

    assert context.model == "gpt-4"
    assert context.temperature == 0.7
    assert len(context.messages) == 2
    assert context.prompt_tokens == 25
    assert context.tools_available == []  # Default value
    assert context.agent_state == {}  # Default value


# Critical: Validation error tests


def test_decision_criteria_invalid_score_below_zero():
    """Test that DecisionCriteria rejects scores < 0."""
    with pytest.raises(ValidationError) as exc_info:
        DecisionCriteria(
            factor="test",
            score=-0.1,
            weight=0.5,
            reasoning="Invalid score"
        )

    assert "score" in str(exc_info.value)


def test_decision_criteria_invalid_score_above_one():
    """Test that DecisionCriteria rejects scores > 1."""
    with pytest.raises(ValidationError) as exc_info:
        DecisionCriteria(
            factor="test",
            score=1.5,
            weight=0.5,
            reasoning="Invalid score"
        )

    assert "score" in str(exc_info.value)


def test_decision_criteria_invalid_weight_below_zero():
    """Test that DecisionCriteria rejects weights < 0."""
    with pytest.raises(ValidationError) as exc_info:
        DecisionCriteria(
            factor="test",
            score=0.5,
            weight=-0.1,
            reasoning="Invalid weight"
        )

    assert "weight" in str(exc_info.value)


def test_decision_criteria_invalid_weight_above_one():
    """Test that DecisionCriteria rejects weights > 1."""
    with pytest.raises(ValidationError) as exc_info:
        DecisionCriteria(
            factor="test",
            score=0.5,
            weight=1.5,
            reasoning="Invalid weight"
        )

    assert "weight" in str(exc_info.value)


def test_agent_decision_invalid_confidence_below_zero():
    """Test that AgentDecision rejects confidence < 0."""
    with pytest.raises(ValidationError) as exc_info:
        AgentDecision(
            action="test",
            reasoning="test",
            confidence=-0.1,
            alternatives_considered=[],
            criteria=[],
            context_used={}
        )

    assert "confidence" in str(exc_info.value)


def test_agent_decision_invalid_confidence_above_one():
    """Test that AgentDecision rejects confidence > 1."""
    with pytest.raises(ValidationError) as exc_info:
        AgentDecision(
            action="test",
            reasoning="test",
            confidence=1.5,
            alternatives_considered=[],
            criteria=[],
            context_used={}
        )

    assert "confidence" in str(exc_info.value)


def test_llm_context_invalid_temperature_below_zero():
    """Test that LLMContext rejects temperature < 0."""
    with pytest.raises(ValidationError) as exc_info:
        LLMContext(
            model="gpt-4",
            temperature=-0.1,
            messages=[],
            prompt_tokens=0
        )

    assert "temperature" in str(exc_info.value)


def test_llm_context_invalid_temperature_above_two():
    """Test that LLMContext rejects temperature > 2."""
    with pytest.raises(ValidationError) as exc_info:
        LLMContext(
            model="gpt-4",
            temperature=2.5,
            messages=[],
            prompt_tokens=0
        )

    assert "temperature" in str(exc_info.value)


# Good to have: Edge case tests


def test_agent_decision_empty_alternatives():
    """Test AgentDecision with empty alternatives_considered list."""
    decision = AgentDecision(
        action="test_action",
        reasoning="test reasoning",
        confidence=0.5,
        alternatives_considered=[],  # Empty list
        criteria=[],
        context_used={}
    )

    assert decision.alternatives_considered == []


def test_agent_decision_empty_criteria():
    """Test AgentDecision with empty criteria list."""
    decision = AgentDecision(
        action="test_action",
        reasoning="test reasoning",
        confidence=0.5,
        alternatives_considered=[],
        criteria=[],  # Empty list
        context_used={}
    )

    assert decision.criteria == []


def test_agent_decision_empty_context():
    """Test AgentDecision with empty context_used dict."""
    decision = AgentDecision(
        action="test_action",
        reasoning="test reasoning",
        confidence=0.5,
        alternatives_considered=[],
        criteria=[],
        context_used={}  # Empty dict
    )

    assert decision.context_used == {}


def test_llm_context_empty_tools():
    """Test LLMContext with empty tools_available list."""
    context = LLMContext(
        model="gpt-4",
        temperature=0.7,
        messages=[],
        prompt_tokens=0,
        tools_available=[]  # Explicitly empty
    )

    assert context.tools_available == []


def test_llm_context_empty_agent_state():
    """Test LLMContext with empty agent_state dict."""
    context = LLMContext(
        model="gpt-4",
        temperature=0.7,
        messages=[],
        prompt_tokens=0,
        agent_state={}  # Explicitly empty
    )

    assert context.agent_state == {}


def test_decision_criteria_boundary_values():
    """Test DecisionCriteria with boundary values (0.0 and 1.0)."""
    # Test minimum boundary
    criteria_min = DecisionCriteria(
        factor="test",
        score=0.0,
        weight=0.0,
        reasoning="Minimum values"
    )
    assert criteria_min.score == 0.0
    assert criteria_min.weight == 0.0

    # Test maximum boundary
    criteria_max = DecisionCriteria(
        factor="test",
        score=1.0,
        weight=1.0,
        reasoning="Maximum values"
    )
    assert criteria_max.score == 1.0
    assert criteria_max.weight == 1.0


def test_agent_decision_boundary_confidence():
    """Test AgentDecision with boundary confidence values (0.0 and 1.0)."""
    # Test minimum boundary
    decision_min = AgentDecision(
        action="test",
        reasoning="test",
        confidence=0.0,
        alternatives_considered=[],
        criteria=[],
        context_used={}
    )
    assert decision_min.confidence == 0.0

    # Test maximum boundary
    decision_max = AgentDecision(
        action="test",
        reasoning="test",
        confidence=1.0,
        alternatives_considered=[],
        criteria=[],
        context_used={}
    )
    assert decision_max.confidence == 1.0


def test_llm_context_boundary_temperature():
    """Test LLMContext with boundary temperature values (0.0 and 2.0)."""
    # Test minimum boundary
    context_min = LLMContext(
        model="gpt-4",
        temperature=0.0,
        messages=[],
        prompt_tokens=0
    )
    assert context_min.temperature == 0.0

    # Test maximum boundary
    context_max = LLMContext(
        model="gpt-4",
        temperature=2.0,
        messages=[],
        prompt_tokens=0
    )
    assert context_max.temperature == 2.0


# Good to have: Serialization tests


def test_decision_criteria_model_dump():
    """Test DecisionCriteria serialization with model_dump()."""
    criteria = DecisionCriteria(
        factor="cost",
        score=0.8,
        weight=0.5,
        reasoning="Test reasoning"
    )

    data = criteria.model_dump()
    assert isinstance(data, dict)
    assert data["factor"] == "cost"
    assert data["score"] == 0.8
    assert data["weight"] == 0.5
    assert data["reasoning"] == "Test reasoning"


def test_decision_criteria_model_dump_json():
    """Test DecisionCriteria JSON serialization with model_dump_json()."""
    criteria = DecisionCriteria(
        factor="cost",
        score=0.8,
        weight=0.5,
        reasoning="Test reasoning"
    )

    json_str = criteria.model_dump_json()
    assert isinstance(json_str, str)
    assert "cost" in json_str
    assert "0.8" in json_str


def test_agent_decision_model_dump():
    """Test AgentDecision serialization with model_dump()."""
    decision = AgentDecision(
        action="use_cache",
        reasoning="Best choice",
        confidence=0.85,
        alternatives_considered=["option_a", "option_b"],
        criteria=[
            DecisionCriteria(factor="cost", score=0.8, weight=0.5)
        ],
        context_used={"key": "value"}
    )

    data = decision.model_dump()
    assert isinstance(data, dict)
    assert data["action"] == "use_cache"
    assert data["confidence"] == 0.85
    assert len(data["alternatives_considered"]) == 2
    assert len(data["criteria"]) == 1


def test_agent_decision_model_dump_json():
    """Test AgentDecision JSON serialization with model_dump_json()."""
    decision = AgentDecision(
        action="use_cache",
        reasoning="Best choice",
        confidence=0.85,
        alternatives_considered=["option_a"],
        criteria=[],
        context_used={}
    )

    json_str = decision.model_dump_json()
    assert isinstance(json_str, str)
    assert "use_cache" in json_str
    assert "0.85" in json_str


def test_llm_context_model_dump():
    """Test LLMContext serialization with model_dump()."""
    context = LLMContext(
        model="gpt-4",
        temperature=0.7,
        messages=[{"role": "user", "content": "test"}],
        prompt_tokens=25,
        tools_available=["tool1"],
        agent_state={"key": "value"}
    )

    data = context.model_dump()
    assert isinstance(data, dict)
    assert data["model"] == "gpt-4"
    assert data["temperature"] == 0.7
    assert len(data["messages"]) == 1
    assert data["prompt_tokens"] == 25


def test_llm_context_model_dump_json():
    """Test LLMContext JSON serialization with model_dump_json()."""
    context = LLMContext(
        model="gpt-4",
        temperature=0.7,
        messages=[],
        prompt_tokens=0
    )

    json_str = context.model_dump_json()
    assert isinstance(json_str, str)
    assert "gpt-4" in json_str
    assert "0.7" in json_str
