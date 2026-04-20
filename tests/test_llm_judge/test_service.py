"""
Tests for LLMJudgeService.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from evaluation_system.models import JudgeRequest, JudgeResponse
from evaluation_system.llm_judge.service import LLMJudgeService
from evaluation_system.llm_judge.prompts import DIMENSION_WEIGHTS


class TestLLMJudgeService:
    """Test cases for LLMJudgeService."""
    
    @pytest.fixture
    def service(self, mock_settings):
        return LLMJudgeService()
    
    def test_get_prompt_reasoning(self, service):
        """Test getting reasoning prompt."""
        prompt = service._get_prompt("reasoning")
        assert "correctness" in prompt.lower()
        assert "tool_usage" in prompt.lower()
    
    def test_get_prompt_workflow(self, service):
        """Test getting workflow prompt."""
        prompt = service._get_prompt("workflow")
        assert "flow_completeness" in prompt.lower()
    
    def test_get_prompt_orchestration(self, service):
        """Test getting orchestration prompt."""
        prompt = service._get_prompt("orchestration")
        assert "orchestration" in prompt.lower()
    
    def test_get_prompt_simplified(self, service):
        """Test getting simplified prompt."""
        prompt = service._get_prompt("reasoning", simplified=True)
        assert "Evaluate" in prompt
    
    def test_build_prompt_content(self, service):
        """Test building prompt content dictionary."""
        request = JudgeRequest(
            user_query="What is the weather?",
            agent_response="The weather is sunny.",
            tool_call_log=[{"name": "get_weather", "result": "sunny"}],
            expected_tools=["get_weather"],
            agent_type="reasoning",
        )
        
        content = service._build_prompt_content(request)
        
        assert content["user_query"] == "What is the weather?"
        assert content["agent_response"] == "The weather is sunny."
        assert "get_weather" in content["tool_call_log"]
        assert content["expected_tools"] == "get_weather"
    
    def test_calculate_weighted_score_reasoning(self, service):
        """Test weighted score calculation for reasoning."""
        scores = {
            "correctness": 80.0,
            "tool_usage": 90.0,
            "efficiency": 70.0,
            "relevance": 85.0,
        }
        
        weighted = service._calculate_weighted_score(scores, "reasoning")
        
        # Expected: 0.35*80 + 0.25*90 + 0.20*70 + 0.20*85 = 28 + 22.5 + 14 + 17 = 81.5
        assert abs(weighted - 81.5) < 0.1
    
    def test_calculate_weighted_score_workflow(self, service):
        """Test weighted score calculation for workflow."""
        scores = {
            "flow_completeness": 100.0,
            "node_performance": 80.0,
            "end_to_end_correctness": 90.0,
            "latency": 95.0,
        }
        
        weighted = service._calculate_weighted_score(scores, "workflow")
        
        # Expected: 0.30*100 + 0.25*80 + 0.25*90 + 0.20*95 = 30 + 20 + 22.5 + 19 = 91.5
        assert abs(weighted - 91.5) < 0.1
    
    def test_parse_json_response_valid(self, service):
        """Test parsing valid JSON response."""
        json_str = '{"scores": {"correctness": 85}, "weighted_score": 85.0, "confidence": "high", "needs_human_review": false, "key_findings": [], "main_issues": []}'
        
        parsed = service._parse_json_response(json_str)
        
        assert parsed["scores"]["correctness"] == 85
        assert parsed["confidence"] == "high"
    
    def test_parse_json_response_with_markdown(self, service):
        """Test parsing JSON wrapped in markdown code blocks."""
        json_str = '```json\n{"scores": {"correctness": 85}, "weighted_score": 85.0, "confidence": "high", "needs_human_review": false, "key_findings": [], "main_issues": []}\n```'
        
        parsed = service._parse_json_response(json_str)
        
        assert parsed["scores"]["correctness"] == 85
    
    def test_parse_invalid_json_fallback(self, service):
        """Test fallback when JSON parsing fails."""
        invalid_str = "This is not JSON at all"
        
        with pytest.raises(ValueError):
            service._parse_json_response(invalid_str)
    
    def test_build_default_response(self, service):
        """Test building default response for failed LLM calls."""
        request = JudgeRequest(
            user_query="Test query",
            agent_response="Test response",
            agent_type="reasoning",
        )
        
        response = service._build_default_response(request, "test failure")
        
        assert response.confidence == "low"
        assert response.needs_human_review is True
        assert "test failure" in response.key_findings[0]
        assert len(response.scores) > 0
    
    @pytest.mark.asyncio
    async def test_judge_reasoning_success(self, service):
        """Test successful reasoning judgment."""
        mock_response_content = '{"scores": {"correctness": 85, "tool_usage": 90, "efficiency": 80, "relevance": 88}, "weighted_score": 85.75, "confidence": "high", "needs_human_review": false, "key_findings": ["Good response"], "main_issues": []}'
        
        request = JudgeRequest(
            user_query="What is 2+2?",
            agent_response="2+2 equals 4",
            tool_call_log=[{"name": "calculator", "result": "4"}],
            expected_tools=["calculator"],
            agent_type="reasoning",
        )
        
        with patch.object(service, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response_content
            
            response = await service.judge_reasoning(request)
            
            assert response.scores["correctness"] == 85.0
            assert response.confidence == "high"
            assert response.needs_human_review is False
    
    @pytest.mark.asyncio
    async def test_judge_workflow_success(self, service):
        """Test successful workflow judgment."""
        mock_content = '{"scores": {"flow_completeness": 95, "node_performance": 90, "end_to_end_correctness": 88, "latency": 92}, "weighted_score": 91.25, "confidence": "high", "needs_human_review": false, "key_findings": [], "main_issues": []}'
        
        request = JudgeRequest(
            user_query="Process order",
            agent_response="Order processed",
            node_execution_log=[{"node_name": "validate"}, {"node_name": "process"}],
            expected_nodes=["validate", "process"],
            agent_type="workflow",
        )
        
        with patch.object(service, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_content
            
            response = await service.judge_workflow(request)
            
            assert response.scores["flow_completeness"] == 95.0
            assert response.confidence == "high"
    
    @pytest.mark.asyncio
    async def test_judge_orchestration_success(self, service):
        """Test successful orchestration judgment."""
        mock_content = '{"scores": {"orchestration_reasonableness": 88, "sub_agent_effectiveness": 85, "result_aggregation": 90, "end_to_end_effectiveness": 87}, "weighted_score": 87.5, "confidence": "medium", "needs_human_review": false, "key_findings": [], "main_issues": []}'
        
        request = JudgeRequest(
            user_query="Analyze data",
            agent_response="Analysis complete",
            sub_agent_call_log=[{"sub_agent_name": "collector"}, {"sub_agent_name": "analyzer"}],
            expected_sub_agents=["collector", "analyzer"],
            agent_type="orchestration",
        )
        
        with patch.object(service, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_content
            
            response = await service.judge_orchestration(request)
            
            assert response.scores["orchestration_reasonableness"] == 88.0
            assert response.confidence == "medium"
    
    @pytest.mark.asyncio
    async def test_confidence_high_direct_adopt(self, service):
        """Test that high confidence responses are adopted directly."""
        mock_content = '{"scores": {"correctness": 90}, "weighted_score": 90, "confidence": "high", "needs_human_review": false, "key_findings": [], "main_issues": []}'
        
        request = JudgeRequest(
            user_query="Test",
            agent_response="Response",
            agent_type="reasoning",
        )
        
        with patch.object(service, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_content
            
            response = await service.judge_reasoning(request)
            
            assert response.needs_human_review is False
            assert response.confidence == "high"
    
    @pytest.mark.asyncio
    async def test_confidence_low_human_review(self, service):
        """Test that low confidence responses set needs_human_review flag."""
        mock_content = '{"scores": {"correctness": 60}, "weighted_score": 60, "confidence": "low", "needs_human_review": true, "key_findings": [], "main_issues": ["Ambiguous response"]}'
        
        request = JudgeRequest(
            user_query="Test",
            agent_response="Unclear response",
            agent_type="reasoning",
        )
        
        with patch.object(service, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_content
            
            response = await service.judge_reasoning(request)
            
            assert response.needs_human_review is True
            assert response.confidence == "low"
    
    @pytest.mark.asyncio
    async def test_parse_json_response(self, service):
        """Test JSON parsing of LLM response."""
        raw = '{"scores": {"correctness": 85}, "weighted_score": 85, "confidence": "medium", "needs_human_review": false, "key_findings": ["Good"], "main_issues": []}'
        
        parsed = service._parse_json_response(raw)
        
        assert isinstance(parsed, dict)
        assert "scores" in parsed
        assert "confidence" in parsed
    
    @pytest.mark.asyncio
    async def test_parse_invalid_json_fallback_to_default(self, service):
        """Test that invalid JSON triggers default response (tier 3 fallback)."""
        request = JudgeRequest(
            user_query="Test",
            agent_response="Response",
            agent_type="reasoning",
        )
        
        # Make _call_llm raise an exception
        with patch.object(service, "_call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("API Error")
            
            response = await service.judge_reasoning(request)
            
            # Should fall back to default
            assert response.confidence == "low"
            assert response.needs_human_review is True
    
    @pytest.mark.asyncio
    async def test_build_response_from_parsed(self, service):
        """Test building response from parsed LLM output."""
        parsed = {
            "scores": {"correctness": 80.0, "tool_usage": 85.0, "efficiency": 75.0, "relevance": 90.0},
            "weighted_score": 82.0,
            "confidence": "high",
            "needs_human_review": False,
            "key_findings": ["Good tool usage"],
            "main_issues": [],
        }
        
        response = service._build_response_from_parsed(parsed, "raw text", "reasoning")
        
        assert response.scores["correctness"] == 80.0
        assert response.weighted_score == 82.0
        assert response.confidence == "high"
        assert len(response.key_findings) == 1
