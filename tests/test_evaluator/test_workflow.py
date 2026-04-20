"""
Tests for WorkflowEvaluator.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from evaluation_system.models import EvalCase as TestCase
from evaluation_system.evaluator.workflow_evaluator import WorkflowEvaluator
from tests.conftest import MockLLMJudge


class TestWorkflowEvaluator:
    """Test cases for WorkflowEvaluator."""
    
    @pytest.fixture
    def evaluator(self, mock_llm_judge):
        return WorkflowEvaluator(
            agent_id=1,
            agent_config={},
            seaf_api_base="http://localhost:9000",
            seaf_api_key="test-key",
            llm_judge=mock_llm_judge,
        )
    
    def test_get_evaluation_dimensions(self, evaluator):
        """Test that evaluator returns correct dimensions."""
        dims = evaluator.get_evaluation_dimensions()
        assert "flow_completeness" in dims
        assert "node_performance" in dims
        assert "end_to_end_correctness" in dims
        assert "latency" in dims
        assert len(dims) == 4
    
    def test_extract_node_executions(self, evaluator):
        """Test extraction of node execution log."""
        response = {
            "execution_id": "exec_001",
            "status": "completed",
            "nodes": [
                {"id": "n1", "name": "validate", "status": "completed", "latency_ms": 100, "output": "OK"},
                {"id": "n2", "name": "process", "status": "completed", "latency_ms": 200, "output": "Done"},
            ],
        }
        
        nodes = evaluator._extract_node_executions(response)
        
        assert len(nodes) == 2
        assert nodes[0]["node_name"] == "validate"
        assert nodes[1]["node_name"] == "process"
    
    def test_get_final_response(self, evaluator):
        """Test extraction of final workflow output."""
        response = {
            "status": "completed",
            "output": "Order processed successfully",
        }
        
        final = evaluator._get_final_response(response)
        assert final == "Order processed successfully"
    
    def test_judge_flow_completeness(self, evaluator):
        """Test rule-based judgment for flow completeness."""
        response = {
            "status": "completed",
            "nodes": [
                {"id": "n1", "name": "validate", "status": "completed"},
                {"id": "n2", "name": "process", "status": "completed"},
                {"id": "n3", "name": "confirm", "status": "completed"},
            ],
        }
        
        result = evaluator.judge(
            response,
            expected_nodes=["validate", "process", "confirm"],
        )
        
        assert result.scores["flow_completeness"] == 100.0
        assert result.passed is True
    
    def test_judge_node_performance(self, evaluator):
        """Test judgment of node performance."""
        response = {
            "status": "completed",
            "nodes": [
                {"id": "n1", "name": "validate", "status": "completed"},
                {"id": "n2", "name": "process", "status": "failed"},  # One node failed
            ],
        }
        
        result = evaluator.judge(response)
        
        assert result.scores["node_performance"] < 100.0
    
    def test_judge_end_to_end_latency(self, evaluator):
        """Test latency judgment with max constraint."""
        response = {
            "status": "completed",
            "nodes": [
                {"id": "n1", "name": "fast", "status": "completed", "latency_ms": 100},
                {"id": "n2", "name": "slow", "status": "completed", "latency_ms": 400},
            ],
        }
        
        # Within limit
        result = evaluator.judge(
            response,
            max_total_latency_ms=1000,
        )
        assert result.scores["latency"] == 100.0
        
        # Exceeds limit
        result = evaluator.judge(
            response,
            max_total_latency_ms=300,
        )
        assert result.scores["latency"] < 100.0
    
    @pytest.mark.asyncio
    async def test_workflow_execute_and_poll(self, evaluator):
        """Test workflow execution and status polling."""
        execute_response = {"execution_id": "exec_123", "status": "running"}
        status_response = {
            "execution_id": "exec_123",
            "status": "completed",
            "nodes": [
                {"id": "n1", "name": "step1", "status": "completed", "latency_ms": 50, "output": ""},
            ],
        }
        
        with patch.object(evaluator, "_execute_workflow", new_callable=AsyncMock) as mock_exec:
            with patch.object(evaluator, "_poll_workflow_status", new_callable=AsyncMock) as mock_poll:
                mock_exec.return_value = execute_response
                mock_poll.return_value = status_response
                
                response = await evaluator._execute_workflow("Test query")
                assert response["execution_id"] == "exec_123"
                
                final = await evaluator._poll_workflow_status("exec_123")
                assert final["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_evaluate_workflow_success(self, evaluator, sample_workflow_cases):
        """Test successful evaluation of a workflow case."""
        execute_response = {"execution_id": "exec_001", "status": "running"}
        status_response = {
            "execution_id": "exec_001",
            "status": "completed",
            "nodes": [
                {"id": "n1", "name": "validate_order", "status": "completed", "latency_ms": 100, "output": "OK"},
                {"id": "n2", "name": "process_payment", "status": "completed", "latency_ms": 200, "output": "OK"},
            ],
        }
        
        with patch.object(evaluator, "_execute_workflow", new_callable=AsyncMock) as mock_exec:
            with patch.object(evaluator, "_poll_workflow_status", new_callable=AsyncMock) as mock_poll:
                mock_exec.return_value = execute_response
                mock_poll.return_value = status_response
                
                case = sample_workflow_cases[0]
                output = await evaluator.evaluate(case)
                
                assert output.result.passed is True
                assert len(output.result.node_execution_log) == 2
                assert "flow_completeness" in output.result.scores
    
    @pytest.mark.asyncio
    async def test_judge_flow_completeness_integration(self, evaluator, sample_workflow_cases):
        """Test flow completeness judgment in integration."""
        status_response = {
            "execution_id": "exec_001",
            "status": "completed",
            "nodes": [
                {"id": "n1", "name": "validate_order", "status": "completed", "latency_ms": 100, "output": ""},
                {"id": "n2", "name": "process_payment", "status": "completed", "latency_ms": 200, "output": ""},
                {"id": "n3", "name": "send_confirmation", "status": "completed", "latency_ms": 50, "output": ""},
            ],
        }
        
        result = evaluator.judge(
            status_response,
            expected_nodes=["validate_order", "process_payment", "send_confirmation"],
        )
        
        assert result.scores["flow_completeness"] == 100.0
        assert result.passed is True
    
    @pytest.mark.asyncio
    async def test_judge_node_performance_integration(self, evaluator):
        """Test node performance judgment with mixed results."""
        response = {
            "status": "completed",
            "nodes": [
                {"id": "n1", "name": "good_node", "status": "completed", "latency_ms": 100, "output": ""},
                {"id": "n2", "name": "failed_node", "status": "failed", "latency_ms": 0, "error": "Timeout"},
            ],
        }
        
        result = evaluator.judge(response)
        
        assert result.scores["node_performance"] == 50.0  # 1 of 2 completed
    
    @pytest.mark.asyncio
    async def test_judge_end_to_end_latency_integration(self, evaluator):
        """Test end-to-end latency judgment."""
        response = {
            "status": "completed",
            "nodes": [
                {"id": "n1", "name": "fast", "status": "completed", "latency_ms": 100, "output": ""},
                {"id": "n2", "name": "medium", "status": "completed", "latency_ms": 300, "output": ""},
            ],
        }
        
        # Under limit
        result = evaluator.judge(response, max_total_latency_ms=500)
        assert result.scores["latency"] == 100.0
        
        # Just under limit
        result = evaluator.judge(response, max_total_latency_ms=401)
        assert result.scores["latency"] == 100.0
        
        # Exceeds limit
        result = evaluator.judge(response, max_total_latency_ms=300)
        assert result.scores["latency"] < 100.0
