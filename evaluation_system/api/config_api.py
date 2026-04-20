"""
Configuration API endpoints.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ..models import AgentType, EvaluationConfig
from ..llm_judge.prompts import DIMENSION_WEIGHTS
from ..config import settings

router = APIRouter(prefix="/config", tags=["config"])

# Default evaluation configs per agent type
DEFAULT_CONFIGS: Dict[AgentType, EvaluationConfig] = {
    "reasoning": EvaluationConfig(
        agent_type="reasoning",
        dimensions={
            "correctness": 0.35,
            "tool_usage": 0.25,
            "efficiency": 0.20,
            "relevance": 0.20,
        },
        grade_rules={},
        regression_threshold=10.0,
    ),
    "workflow": EvaluationConfig(
        agent_type="workflow",
        dimensions={
            "flow_completeness": 0.30,
            "node_performance": 0.25,
            "end_to_end_correctness": 0.25,
            "latency": 0.20,
        },
        grade_rules={},
        regression_threshold=10.0,
    ),
    "orchestration": EvaluationConfig(
        agent_type="orchestration",
        dimensions={
            "orchestration_reasonableness": 0.25,
            "sub_agent_effectiveness": 0.25,
            "result_aggregation": 0.25,
            "end_to_end_effectiveness": 0.25,
        },
        grade_rules={},
        regression_threshold=10.0,
    ),
}


# In-memory config storage (would be a database in production)
_config_store: Dict[AgentType, EvaluationConfig] = {}
_notification_config: Dict[str, Any] = {}


@router.get("/{agent_type}", response_model=EvaluationConfig)
async def get_evaluation_config(agent_type: AgentType) -> EvaluationConfig:
    """Get evaluation configuration for an agent type."""
    return _config_store.get(agent_type) or DEFAULT_CONFIGS.get(agent_type)


@router.put("/{agent_type}", response_model=EvaluationConfig)
async def update_evaluation_config(
    agent_type: AgentType,
    config: EvaluationConfig,
) -> EvaluationConfig:
    """Update evaluation configuration for an agent type."""
    if config.agent_type != agent_type:
        raise HTTPException(status_code=400, detail="Agent type mismatch")
    _config_store[agent_type] = config
    return config


@router.get("/notification-config")
async def get_notification_config() -> Dict[str, Any]:
    """Get notification configuration."""
    return _notification_config


@router.post("/notification-config")
async def update_notification_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Update notification configuration."""
    global _notification_config
    _notification_config = config
    return config
