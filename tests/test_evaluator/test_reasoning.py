"""
Tests for ReasoningEvaluator.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from evaluation_system.models import EvalCase, EvaluationOutput, JudgeResponse, ConfidenceLevel
from evaluation_system.evaluator.reasoning_evaluator import ReasoningEvaluator
from tests.conftest import MockLLMJudge


class TestReasoningEvaluator:
    """Test cases for ReasoningEvaluator."""
    
    @pytest.fixture
    def evaluator(self, mock_llm_judge):
        return ReasoningEvaluator(
            agent_id=1,
            agent_config={},
            seaf_api_base="http://localhost:9000",
            seaf_api_key="test-key",
            llm_judge=mock_llm_judge,
        )
    
    def test_get_evaluation_dimensions(self, evaluator):
        """Test that evaluator returns correct dimensions."""
        dims = evaluator.get_evaluation_dimensions()
        assert "correctness" in dims
        assert "tool_usage" in dims
        assert "efficiency" in dims
        assert "relevance" in dims
        assert len(dims) == 4
    
    def test_extract_tool_calls_from_response(self, evaluator):
        """Test extraction of tool calls from response messages."""
        response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Let me check the weather.",
                    "tool_calls": [
                        {"id": "call_1", "name": "get_weather", "arguments": {"city": "Beijing"}},
                        {"id": "call_2", "name": "get_location", "arguments": {}},
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "call_1",
                    "name": "get_weather",
                    "content": '{"temp": 22}',
                },
            ]
        }
        
        tool_calls = evaluator._extract_tool_calls(response)
        
        assert len(tool_calls) == 3
        tool_names = [tc["name"] for tc in tool_calls if not tc.get("is_result")]
        assert "get_weather" in tool_names
        assert "get_location" in tool_names
    
    def test_get_final_response(self, evaluator):
        """Test extraction of final response text."""
        response = {
            "messages": [
                {"role": "assistant", "content": "First message"},
                {
                    "role": "assistant",
                    "content": "This is the final response.",
                },
            ]
        }
        
        final = evaluator._get_final_response(response)
        assert final == "This is the final response."
    
    def test_judge_with_expected_tools(self, evaluator):
        """Test rule-based judgment with expected tools."""
        response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Done",
                    "tool_calls": [
                        {"id": "c1", "name": "get_weather", "arguments": {}},
                        {"id": "c2", "name": "get_location", "arguments": {}},
                    ],
                },
            ]
        }
        
        result = evaluator.judge(response, expected_tools=["get_weather", "get_location"])
        
        assert result.scores["tool_match"] == 100.0
        assert result.passed is True
        assert len(result.tool_call_log) == 2
    
    def test_judge_with_partial_tools(self, evaluator):
        """Test judgment when only some expected tools are used."""
        response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Done",
                    "tool_calls": [
                        {"id": "c1", "name": "get_weather", "arguments": {}},
                    ],
                },
            ]
        }
        
        result = evaluator.judge(response, expected_tools=["get_weather", "get_location"])
        
        assert result.scores["tool_match"] == 50.0
        assert result.passed is True
    
    def test_judge_with_no_tools(self, evaluator):
        """Test judgment when no expected tools specified."""
        response = {
            "messages": [
                {"role": "assistant", "content": "Direct response without tools."},
            ]
        }
        
        result = evaluator.judge(response, expected_tools=[])
        
        assert result.scores["tool_match"] == 100.0
    
    @pytest.mark.asyncio
    async def test_evaluate_success(self, evaluator, sample_reasoning_cases):
        """Test successful evaluation of a reasoning case."""
        mock_response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": "The weather is sunny.",
                    "tool_calls": [
                        {"id": "c1", "name": "get_weather", "arguments": {}},
                    ],
                },
            ]
        }
        
        with patch.object(evaluator, "_call_chat_agent", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            case = sample_reasoning_cases[0]
            output = await evaluator.evaluate(case)
            
            assert output.result.passed is True
            assert "correctness" in output.result.scores
            assert output.latency_ms >= 0
    
    @pytest.mark.asyncio
    async def test_evaluate_with_tool_calls(self, evaluator):
        """Test evaluation correctly extracts and logs tool calls."""
        mock_response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Found it!",
                    "tool_calls": [
                        {"id": "c1", "name": "web_search", "arguments": {"query": "AI news"}},
                        {"id": "c2", "name": "get_summary", "arguments": {}},
                    ],
                },
            ]
        }
        
        case = EvalCase(
            name="search_test",
            query="Search for AI news",
            expected_tools=["web_search"],
        )
        
        with patch.object(evaluator, "_call_chat_agent", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            output = await evaluator.evaluate(case)
            
            assert len(output.result.tool_call_log) == 2
    
    @pytest.mark.asyncio
    async def test_judge_with_llm_mock(self, evaluator, sample_reasoning_cases):
        """Test that LLM judge is called during evaluation."""
        mock_response = {
            "messages": [
                {
                    "role": "assistant",
                    "content": "The weather is nice.",
                    "tool_calls": [
                        {"id": "c1", "name": "get_weather", "arguments": {}},
                    ],
                },
            ]
        }
        
        with patch.object(evaluator, "_call_chat_agent", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            case = sample_reasoning_cases[0]
            output = await evaluator.evaluate(case)
            
            # The mock judge should have been called
            assert evaluator.llm_judge.call_count >= 1
            assert output.result.judge_response is not None
    
    @pytest.mark.asyncio
    async def test_batch_evaluate(self, evaluator, sample_reasoning_cases):
        """Test batch evaluation of multiple cases."""
        mock_response = {
            "messages": [
                {"role": "assistant", "content": "Done"},
            ]
        }
        
        with patch.object(evaluator, "_call_chat_agent", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            cases = sample_reasoning_cases[:2]
            progress_calls = []
            
            def progress_callback(completed, total):
                progress_calls.append((completed, total))
            
            outputs = await evaluator.batch_evaluate(cases, progress_callback)
            
            assert len(outputs) == 2
            assert len(progress_calls) == 2
            assert progress_calls[-1] == (2, 2)
