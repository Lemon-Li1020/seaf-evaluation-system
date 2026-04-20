"""
Tests for OrchestrationEvaluator.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from evaluation_system.models import EvalCase
from evaluation_system.evaluator.orchestration_evaluator import OrchestrationEvaluator
from tests.conftest import MockLLMJudge


class TestOrchestrationEvaluator:
    """Test cases for OrchestrationEvaluator."""
    
    @pytest.fixture
    def evaluator(self, mock_llm_judge):
        return OrchestrationEvaluator(
            agent_id=1,
            agent_config={},
            seaf_api_base="http://localhost:9000",
            seaf_api_key="test-key",
            llm_judge=mock_llm_judge,
        )
    
    def test_get_evaluation_dimensions(self, evaluator):
        """Test that evaluator returns correct dimensions."""
        dims = evaluator.get_evaluation_dimensions()
        assert "orchestration_reasonableness" in dims
        assert "sub_agent_effectiveness" in dims
        assert "result_aggregation" in dims
        assert "end_to_end_effectiveness" in dims
        assert len(dims) == 4
    
    def test_extract_sub_agent_calls_simple(self, evaluator):
        """Test extraction of sub-agent calls from simple call chain."""
        response = {
            "call_chain": [
                {
                    "sub_agent_id": "agent_1",
                    "sub_agent_name": "data_collector",
                    "query": "Collect data",
                    "result": "Data collected",
                    "calls": [],
                },
                {
                    "sub_agent_id": "agent_2",
                    "sub_agent_name": "report_generator",
                    "query": "Generate report",
                    "result": "Report generated",
                    "calls": [],
                },
            ]
        }
        
        chain = evaluator._extract_sub_agent_calls(response)
        
        assert len(chain) == 2
        assert chain[0]["sub_agent_name"] == "data_collector"
        assert chain[1]["sub_agent_name"] == "report_generator"
    
    def test_extract_sub_agent_calls_nested(self, evaluator):
        """Test extraction with nested sub-agent calls."""
        response = {
            "call_chain": [
                {
                    "sub_agent_id": "agent_1",
                    "sub_agent_name": "parent",
                    "query": "Parent task",
                    "result": "Done",
                    "calls": [
                        {
                            "sub_agent_id": "agent_2",
                            "sub_agent_name": "child",
                            "query": "Child task",
                            "result": "Done",
                            "calls": [],
                        },
                    ],
                },
            ]
        }
        
        chain = evaluator._extract_sub_agent_calls(response)
        
        assert len(chain) == 2
        assert chain[0]["sub_agent_name"] == "parent"
        assert chain[0]["depth"] == 0
        assert chain[1]["sub_agent_name"] == "child"
        assert chain[1]["depth"] == 1
    
    def test_detect_dead_loop_no_loop(self, evaluator):
        """Test dead loop detection when there's no loop."""
        call_chain = [
            {"sub_agent_name": "agent_a"},
            {"sub_agent_name": "agent_b"},
            {"sub_agent_name": "agent_c"},
        ]
        
        assert evaluator._detect_dead_loop(call_chain) is False
    
    def test_detect_dead_loop_with_loop(self, evaluator):
        """Test dead loop detection when same agent called repeatedly."""
        call_chain = [
            {"sub_agent_name": "agent_a"},
            {"sub_agent_name": "agent_a"},
            {"sub_agent_name": "agent_a"},
            {"sub_agent_name": "agent_a"},
        ]
        
        assert evaluator._detect_dead_loop(call_chain) is True
    
    def test_detect_dead_loop_boundary(self, evaluator):
        """Test dead loop detection at threshold boundary."""
        # Exactly 3 calls is the threshold
        call_chain = [
            {"sub_agent_name": "agent_a"},
            {"sub_agent_name": "agent_a"},
            {"sub_agent_name": "agent_a"},
        ]
        
        assert evaluator._detect_dead_loop(call_chain) is True
    
    def test_check_sub_agent_order_correct(self, evaluator):
        """Test sub-agent order checking with correct order."""
        call_chain = [
            {"sub_agent_name": "collector"},
            {"sub_agent_name": "processor"},
            {"sub_agent_name": "writer"},
        ]
        
        expected_order = ["collector", "processor", "writer"]
        score = evaluator._check_sub_agent_order(call_chain, expected_order)
        
        assert score == 100.0
    
    def test_check_sub_agent_order_partial(self, evaluator):
        """Test sub-agent order checking with partial match."""
        call_chain = [
            {"sub_agent_name": "collector"},
            {"sub_agent_name": "writer"},  # Wrong order
            {"sub_agent_name": "processor"},
        ]
        
        expected_order = ["collector", "processor", "writer"]
        score = evaluator._check_sub_agent_order(call_chain, expected_order)
        
        assert score == pytest.approx(33.33, rel=0.1)
    
    def test_check_sub_agent_order_empty(self, evaluator):
        """Test sub-agent order checking with no expected order."""
        call_chain = [
            {"sub_agent_name": "any"},
            {"sub_agent_name": "order"},
        ]
        
        score = evaluator._check_sub_agent_order(call_chain, [])
        
        assert score == 100.0
    
    def test_get_final_response(self, evaluator):
        """Test extraction of final orchestration response."""
        response = {
            "response": "Analysis complete. Report generated.",
        }
        
        final = evaluator._get_final_response(response)
        assert final == "Analysis complete. Report generated."
    
    @pytest.mark.asyncio
    async def test_evaluate_orchestration_success(self, evaluator, sample_orchestration_cases):
        """Test successful evaluation of an orchestration case."""
        mock_response = {
            "call_chain": [
                {
                    "sub_agent_id": "agent_1",
                    "sub_agent_name": "data_collector",
                    "query": "Collect data",
                    "result": "Data collected",
                    "calls": [],
                },
                {
                    "sub_agent_id": "agent_2",
                    "sub_agent_name": "report_generator",
                    "query": "Generate report",
                    "result": "Report generated",
                    "calls": [],
                },
            ],
            "response": "Analysis complete.",
        }
        
        with patch.object(evaluator, "_call_orchestration_ask", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            with patch.object(evaluator, "_evaluate_sub_agents", new_callable=AsyncMock) as mock_sub:
                mock_sub.return_value = []
                
                case = sample_orchestration_cases[0]
                output = await evaluator.evaluate(case)
                
                assert output.result.passed is True
                assert len(output.result.sub_agent_call_log) == 2
    
    @pytest.mark.asyncio
    async def test_dead_loop_detection_integration(self, evaluator, sample_orchestration_cases):
        """Test that dead loop is detected and marked as failed."""
        mock_response = {
            "call_chain": [
                {"sub_agent_id": "a1", "sub_agent_name": "search", "query": "q1", "result": "r1", "calls": []},
                {"sub_agent_id": "a1", "sub_agent_name": "search", "query": "q1", "result": "r1", "calls": []},
                {"sub_agent_id": "a1", "sub_agent_name": "search", "query": "q1", "result": "r1", "calls": []},
                {"sub_agent_id": "a1", "sub_agent_name": "search", "query": "q1", "result": "r1", "calls": []},
            ],
            "response": "Stuck in loop",
        }
        
        with patch.object(evaluator, "_call_orchestration_ask", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            with patch.object(evaluator, "_evaluate_sub_agents", new_callable=AsyncMock) as mock_sub:
                mock_sub.return_value = []
                
                case = sample_orchestration_cases[0]
                output = await evaluator.evaluate(case)
                
                # Should fail due to dead loop
                assert output.result.passed is False
                assert "orchestration_reasonableness" in output.result.scores
                # Score should be capped
                assert output.result.scores["orchestration_reasonableness"] <= 30
    
    @pytest.mark.asyncio
    async def test_judge_orchestration_reasonableness(self, evaluator):
        """Test orchestration reasonableness judgment."""
        response = {
            "call_chain": [
                {"sub_agent_id": "a1", "sub_agent_name": "data", "query": "", "result": "", "calls": []},
                {"sub_agent_id": "a2", "sub_agent_name": "analyze", "query": "", "result": "", "calls": []},
                {"sub_agent_id": "a3", "sub_agent_name": "report", "query": "", "result": "", "calls": []},
            ],
            "response": "Done",
        }
        
        result = evaluator.judge(response)  # No expected - uses defaults
        
        # Basic pass check
        assert "orchestration_reasonableness" in result.scores
    
    @pytest.mark.asyncio
    async def test_judge_result_aggregation(self, evaluator):
        """Test that result aggregation is evaluated."""
        # Create a case with expected sub-agents
        case = EvalCase(
            name="aggregation_test",
            query="Complex multi-step task",
            expected_sub_agents=["step1", "step2", "step3"],
        )
        
        mock_response = {
            "call_chain": [
                {"sub_agent_id": "a1", "sub_agent_name": "step1", "query": "", "result": "Step 1 result", "calls": []},
                {"sub_agent_id": "a2", "sub_agent_name": "step2", "query": "", "result": "Step 2 result", "calls": []},
            ],
            "response": "All steps completed and aggregated",
        }
        
        with patch.object(evaluator, "_call_orchestration_ask", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response
            
            with patch.object(evaluator, "_evaluate_sub_agents", new_callable=AsyncMock) as mock_sub:
                mock_sub.return_value = []
                
                output = await evaluator.evaluate(case)
                
                assert "result_aggregation" in output.result.scores
