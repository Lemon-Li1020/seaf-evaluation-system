"""
Pytest configuration and fixtures.
"""

import pytest
import pytest_asyncio
from typing import List, Dict, Any
import httpx

# Add the workspace to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation_system.config import Settings
from evaluation_system.database import Database
from evaluation_system.models import EvalCase, AgentType
from evaluation_system.llm_judge.service import LLMJudgeService
from evaluation_system.llm_judge.prompts import DIMENSION_WEIGHTS
from tests.fixtures.seaf_mock import SeafAPIMock


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    return Settings(
        server_host="127.0.0.1",
        server_port=8000,
        db_url="sqlite+aiosqlite:///:memory:",
        llm_provider="deepseek",
        llm_model="deepseek-chat",
        llm_api_key="test-key",
        llm_base_url="https://api.deepseek.com",
        llm_timeout=30,
        seaf_api_base="http://localhost:9000",
        seaf_api_key="test-seaf-key",
        evaluation_reasoning_timeout=120,
        evaluation_workflow_timeout=300,
        regression_threshold=10.0,
    )


@pytest.fixture
def db() -> Database:
    """Create a fresh in-memory database for each test."""
    return Database()


@pytest_asyncio.fixture
async def llm_judge_mock(mock_settings, monkeypatch) -> LLMJudgeService:
    """Create LLM judge service with mocked API calls."""
    service = LLMJudgeService()
    return service


@pytest.fixture
def sample_reasoning_cases() -> List[EvalCase]:
    """Sample test cases for reasoning agents."""
    return [
        EvalCase(
            id=1,
            test_set_id=1,
            name="weather_query",
            query="What is the weather in Beijing?",
            expected_tools=["get_weather", "get_location"],
            expected_answer_keywords=["temperature", "sunny", "cloudy", "rain"],
            difficulty="easy",
            tags=["weather", "tool-use"],
        ),
        EvalCase(
            id=2,
            test_set_id=1,
            name="calculation",
            query="Calculate 123 + 456",
            expected_tools=["calculator"],
            expected_answer_keywords=["579"],
            difficulty="easy",
            tags=["calculation", "math"],
        ),
        EvalCase(
            id=3,
            test_set_id=1,
            name="search_query",
            query="Search for recent news about AI",
            expected_tools=["web_search"],
            expected_answer_keywords=["AI", "news", "article"],
            difficulty="medium",
            tags=["search", "information"],
        ),
    ]


@pytest.fixture
def sample_workflow_cases() -> List[EvalCase]:
    """Sample test cases for workflow agents."""
    return [
        EvalCase(
            id=10,
            test_set_id=2,
            name="order_processing",
            query="Process order #12345",
            expected_nodes=["validate_order", "process_payment", "send_confirmation"],
            expected_order=["validate_order", "process_payment", "send_confirmation"],
            max_total_latency_ms=5000,
            difficulty="medium",
            tags=["workflow", "order"],
        ),
        EvalCase(
            id=11,
            test_set_id=2,
            name="data_pipeline",
            query="Run the ETL pipeline",
            expected_nodes=["extract", "transform", "load"],
            expected_order=["extract", "transform", "load"],
            max_total_latency_ms=30000,
            difficulty="hard",
            tags=["workflow", "etl"],
        ),
    ]


@pytest.fixture
def sample_orchestration_cases() -> List[EvalCase]:
    """Sample test cases for orchestration agents."""
    return [
        EvalCase(
            id=20,
            test_set_id=3,
            name="sales_analysis",
            query="Analyze sales data and generate report",
            expected_sub_agents=["data_collector", "report_generator"],
            expected_order=["data_collector", "report_generator"],
            max_sub_agent_calls=5,
            difficulty="medium",
            tags=["orchestration", "analysis"],
        ),
        EvalCase(
            id=21,
            test_set_id=3,
            name="multi_agent_research",
            query="Research the competitive landscape for our product",
            expected_sub_agents=["web_search", "data_analysis", "report_writer"],
            max_sub_agent_calls=8,
            difficulty="hard",
            tags=["orchestration", "research"],
        ),
    ]


@pytest.fixture
def seaf_api_mock_responses() -> Dict[str, Any]:
    """All mock responses for Seaf API."""
    return {
        "chat": SeafAPIMock.chat_agent_ask_response(),
        "workflow_execute": SeafAPIMock.workflow_execute_response(),
        "workflow_status": SeafAPIMock.workflow_execution_response(),
        "orchestration": SeafAPIMock.orchestration_ask_response(),
    }


def create_mock_httpx_response(url_pattern: str, response_data: Dict[str, Any]):
    """Helper to create httpx mock response matchers."""
    pass


class MockLLMJudge:
    """Mock LLM Judge for testing without real API calls."""
    
    def __init__(self):
        self.call_count = 0
    
    async def judge_reasoning(self, request) -> "JudgeResponse":
        from evaluation_system.models import JudgeResponse
        self.call_count += 1
        return JudgeResponse(
            scores={
                "correctness": 85.0,
                "tool_usage": 90.0,
                "efficiency": 80.0,
                "relevance": 88.0,
            },
            weighted_score=85.75,
            confidence="high",
            needs_human_review=False,
            key_findings=["Good tool usage", "Correct response"],
            main_issues=[],
        )
    
    async def judge_workflow(self, request) -> "JudgeResponse":
        from evaluation_system.models import JudgeResponse
        self.call_count += 1
        return JudgeResponse(
            scores={
                "flow_completeness": 95.0,
                "node_performance": 90.0,
                "end_to_end_correctness": 88.0,
                "latency": 92.0,
            },
            weighted_score=91.25,
            confidence="high",
            needs_human_review=False,
            key_findings=["All nodes executed correctly"],
            main_issues=[],
        )
    
    async def judge_orchestration(self, request) -> "JudgeResponse":
        from evaluation_system.models import JudgeResponse
        self.call_count += 1
        return JudgeResponse(
            scores={
                "orchestration_reasonableness": 88.0,
                "sub_agent_effectiveness": 85.0,
                "result_aggregation": 90.0,
                "end_to_end_effectiveness": 87.0,
            },
            weighted_score=87.5,
            confidence="medium",
            needs_human_review=False,
            key_findings=["Good orchestration structure"],
            main_issues=[],
        )
    
    async def close(self) -> None:
        pass


@pytest.fixture
def mock_llm_judge() -> MockLLMJudge:
    """Create a mock LLM judge service."""
    return MockLLMJudge()
