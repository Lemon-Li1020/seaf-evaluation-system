"""
Workflow agent evaluator.
"""

import json
import logging
import time
import asyncio
import httpx
from typing import Optional, List, Dict, Any

from .base import BaseEvaluator
from ..config import settings
from ..models import EvalCase, EvaluationOutput, EvaluationResult, JudgeRequest
from ..llm_judge.service import LLMJudgeService

logger = logging.getLogger(__name__)


class WorkflowEvaluator(BaseEvaluator):
    """Evaluator for workflow-type agents."""
    
    def __init__(
        self,
        agent_id: int,
        agent_config: Dict[str, Any],
        seaf_api_base: str,
        seaf_api_key: str,
        llm_judge: LLMJudgeService,
    ) -> None:
        super().__init__(agent_id, agent_config, seaf_api_base, seaf_api_key, llm_judge)
        self.timeout = settings.evaluation_workflow_timeout
        self.max_retries = settings.evaluation_max_retries
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.seaf_api_base,
                timeout=self.timeout,
            )
        return self._client
    
    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def get_evaluation_dimensions(self) -> List[str]:
        return ["flow_completeness", "node_performance", "end_to_end_correctness", "latency"]
    
    async def _execute_workflow(
        self,
        query: str,
    ) -> Dict[str, Any]:
        """Call Seaf workflow_execute API."""
        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {self.seaf_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "agent_id": self.agent_id,
            "query": query,
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await client.post(
                    "/api/v1/agents/workflow/execute",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.warning(f"Workflow execute attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
        
        raise RuntimeError("Max retries exceeded for workflow_execute")
    
    async def _poll_workflow_status(
        self,
        execution_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> Dict[str, Any]:
        """Poll workflow execution status until completion."""
        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {self.seaf_api_key}",
            "Content-Type": "application/json",
        }
        
        elapsed = 0.0
        while elapsed < max_wait:
            try:
                response = await client.get(
                    f"/api/v1/agents/workflow/execution/{execution_id}",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                
                status = data.get("status", "")
                if status in ("completed", "failed", "cancelled"):
                    return data
                
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
            except Exception as e:
                logger.warning(f"Status poll failed: {e}")
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
        
        raise TimeoutError(f"Workflow execution {execution_id} timed out after {max_wait}s")
    
    def _extract_node_executions(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract node execution log from workflow response."""
        # Expected format: {"execution_id": "...", "status": "...", "nodes": [...]}
        nodes = response_data.get("nodes", [])
        node_log: List[Dict[str, Any]] = []
        
        for node in nodes:
            node_log.append({
                "node_id": node.get("id", ""),
                "node_name": node.get("name", ""),
                "status": node.get("status", ""),
                "output": node.get("output", ""),
                "latency_ms": node.get("latency_ms", 0),
                "error": node.get("error", ""),
            })
        
        return node_log
    
    def _get_final_response(self, response_data: Dict[str, Any]) -> str:
        """Extract final workflow output."""
        return response_data.get("output", "") or response_data.get("result", "")
    
    def judge(
        self,
        output: Dict[str, Any],
        expected_nodes: Optional[List[str]] = None,
        expected_order: Optional[List[str]] = None,
        max_total_latency_ms: Optional[int] = None,
    ) -> EvaluationResult:
        """Rule-based judgment for workflow execution."""
        node_log = self._extract_node_executions(output)
        expected_nodes = expected_nodes or []
        expected_order = expected_order or []
        
        # Check node completeness
        executed_names = {n.get("node_name") for n in node_log}
        expected_set = set(expected_nodes)
        matched = len(executed_names & expected_set) if expected_set else len(executed_names)
        completeness = (matched / len(expected_set)) * 100 if expected_set else 100.0
        
        # Check order
        order_score = 100.0
        if expected_order:
            executed_order = [n.get("node_name") for n in node_log if n.get("node_name")]
            correct_positions = sum(
                1 for i, name in enumerate(executed_order)
                if i < len(expected_order) and name == expected_order[i]
            )
            order_score = (correct_positions / len(expected_order)) * 100
        
        # Check latency
        total_latency = sum(n.get("latency_ms", 0) for n in node_log)
        latency_score = 100.0
        if max_total_latency_ms and total_latency > max_total_latency_ms:
            latency_score = max(0, 100 - (total_latency - max_total_latency_ms) / max_total_latency_ms * 100)
        
        status = output.get("status", "")
        passed = status == "completed" and completeness > 50
        
        return EvaluationResult(
            passed=passed,
            scores={
                "flow_completeness": completeness,
                "node_performance": 100.0 if all(n.get("status") == "completed" for n in node_log) else 50.0,
                "end_to_end_correctness": completeness * 0.5 + order_score * 0.5,
                "latency": latency_score,
            },
            weighted_score=(completeness + order_score + latency_score) / 3,
            node_execution_log=node_log,
        )
    
    async def evaluate(
        self,
        case: EvalCase,
        session_id: Optional[str] = None,
    ) -> EvaluationOutput:
        """Evaluate a workflow agent on a single test case."""
        start_time = time.time()
        
        try:
            # Step 1: Start workflow execution
            exec_response = await self._execute_workflow(case.query)
            
            execution_id = exec_response.get("execution_id")
            if not execution_id:
                raise ValueError("No execution_id in workflow response")
            
            # Step 2: Poll for completion
            final_response = await self._poll_workflow_status(execution_id)
            
            # Step 3: Extract node execution log
            node_log = self._extract_node_executions(final_response)
            agent_response = self._get_final_response(final_response)
            
            # Step 4: Rule-based pre-judgment
            pre_result = self.judge(
                final_response,
                expected_nodes=case.expected_nodes,
                expected_order=case.expected_order,
                max_total_latency_ms=case.max_total_latency_ms,
            )
            
            # Step 5: LLM-based evaluation
            judge_request = JudgeRequest(
                user_query=case.query,
                agent_response=agent_response,
                node_execution_log=node_log,
                expected_nodes=case.expected_nodes or [],
                expected_order=case.expected_order or [],
                agent_type="workflow",
            )
            
            judge_response = await self.llm_judge.judge_workflow(judge_request)
            
            # Combine scores (LLM takes precedence)
            final_result = EvaluationResult(
                passed=pre_result.passed,
                scores=judge_response.scores,
                weighted_score=judge_response.weighted_score,
                node_execution_log=node_log,
                judge_response=judge_response,
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            return EvaluationOutput(
                result=final_result,
                raw_response=agent_response,
                latency_ms=elapsed_ms,
            )
        
        except Exception as e:
            logger.error(f"Workflow evaluation failed for case {case.name}: {e}")
            elapsed_ms = int((time.time() - start_time) * 1000)
            return EvaluationOutput(
                result=EvaluationResult(
                    passed=False,
                    error_message=str(e),
                ),
                latency_ms=elapsed_ms,
            )
