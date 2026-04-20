"""
Data models for Seaf Evaluation System.
All models using Pydantic (no dataclass).
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


# --- Literal Types ---
AgentType = Literal["reasoning", "workflow", "orchestration"]
TaskStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
TriggerType = Literal["manual", "scheduled", "pre_release", "api"]
GradeType = Literal["A", "B", "C", "D", "F"]
ConfidenceLevel = Literal["high", "medium", "low"]


# --- TestCase ---
class EvalCase(BaseModel):
    id: Optional[int] = None
    test_set_id: Optional[int] = None
    name: str
    query: str
    expected_tools: Optional[List[str]] = Field(default_factory=list)
    expected_answer_keywords: Optional[List[str]] = Field(default_factory=list)
    expected_nodes: Optional[List[str]] = Field(default_factory=list)
    expected_sub_agents: Optional[List[str]] = Field(default_factory=list)
    expected_order: Optional[List[str]] = Field(default_factory=list)
    max_sub_agent_calls: Optional[int] = None
    conflict_scenario: Optional[str] = None
    max_node_latency_ms: Optional[int] = None
    max_total_latency_ms: Optional[int] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    difficulty: Optional[str] = None


# --- TestSet ---
class TestSet(BaseModel):
    id: Optional[int] = None
    team_id: int
    agent_id: int
    name: str
    agent_type: AgentType
    description: Optional[str] = ""
    total_cases: int = 0
    version: str = "v1.0"


# --- EvaluationTask ---
class EvaluationTask(BaseModel):
    id: Optional[int] = None
    task_uuid: str
    team_id: int
    test_set_id: int
    agent_id: int
    agent_type: AgentType
    agent_version: Optional[str] = "latest"
    trigger: TriggerType = "manual"
    status: TaskStatus = "pending"
    total_cases: int = 0
    completed_cases: int = 0
    progress: float = 0.0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


# --- TestCaseResult ---
class TestCaseResult(BaseModel):
    id: Optional[int] = None
    task_id: int
    test_case_id: int
    query: str
    agent_response: str = ""
    tool_call_log: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    node_execution_log: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    sub_agent_call_log: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    scores: Dict[str, float] = Field(default_factory=dict)
    weighted_score: float = 0.0
    passed: bool = False
    latency_ms: int = 0
    llm_response: Optional[str] = None
    confidence: Optional[ConfidenceLevel] = None
    needs_human_review: bool = False
    error_message: Optional[str] = None


# --- EvaluationReport ---
class EvaluationReport(BaseModel):
    id: Optional[int] = None
    task_id: int
    team_id: int
    agent_id: int
    test_set_id: int
    summary: Dict[str, Any] = Field(default_factory=dict)
    by_dimension: Dict[str, float] = Field(default_factory=dict)
    regression: Optional[Dict[str, Any]] = None


# --- EvaluationConfig ---
class EvaluationConfig(BaseModel):
    agent_type: AgentType
    dimensions: Dict[str, float] = Field(default_factory=dict)
    grade_rules: Dict[str, Any] = Field(default_factory=dict)
    regression_threshold: float = 10.0


# --- LLM Judge ---
class JudgeRequest(BaseModel):
    user_query: str
    agent_response: str = ""
    tool_call_log: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    node_execution_log: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    sub_agent_call_log: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    expected_tools: Optional[List[str]] = Field(default_factory=list)
    expected_nodes: Optional[List[str]] = Field(default_factory=list)
    expected_sub_agents: Optional[List[str]] = Field(default_factory=list)
    expected_order: Optional[List[str]] = Field(default_factory=list)
    agent_type: AgentType = "reasoning"


class JudgeResponse(BaseModel):
    scores: Dict[str, float] = Field(default_factory=dict)
    weighted_score: float = 0.0
    confidence: ConfidenceLevel = "medium"
    needs_human_review: bool = False
    key_findings: List[str] = Field(default_factory=list)
    main_issues: List[str] = Field(default_factory=list)
    raw_response: Optional[str] = None


# --- Evaluation Input/Output ---
class EvaluationInput(BaseModel):
    case: EvalCase
    agent_id: int
    agent_type: AgentType
    session_id: Optional[str] = None


class EvaluationOutput(BaseModel):
    result: "EvaluationResult"
    raw_response: str = ""
    latency_ms: int = 0


class EvaluationResult(BaseModel):
    passed: bool = False
    scores: Dict[str, float] = Field(default_factory=dict)
    weighted_score: float = 0.0
    tool_call_log: List[Dict[str, Any]] = Field(default_factory=list)
    node_execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    sub_agent_call_log: List[Dict[str, Any]] = Field(default_factory=list)
    judge_response: Optional[JudgeResponse] = None
    error_message: Optional[str] = None


# --- API Request/Response Models ---
class CreateTestSetRequest(BaseModel):
    team_id: int
    agent_id: int
    name: str
    agent_type: AgentType
    description: Optional[str] = ""


class CreateTaskRequest(BaseModel):
    team_id: int
    test_set_id: int
    agent_id: int
    agent_type: AgentType
    agent_version: Optional[str] = "latest"
    trigger: TriggerType = "manual"


class TaskProgressResponse(BaseModel):
    task_id: int
    status: TaskStatus
    total_cases: int
    completed_cases: int
    progress: float
    error_message: Optional[str] = None


class CompareRequest(BaseModel):
    agent_id: int
    report_ids: List[int]
