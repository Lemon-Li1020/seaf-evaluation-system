"""
Orchestration agent evaluator.
"""

import json
import logging
import time
from typing import Optional, List, Dict, Any, Set

from .base import BaseEvaluator
from .reasoning_evaluator import ReasoningEvaluator
from ..config import settings
from ..models import EvalCase, EvaluationOutput, EvaluationResult, JudgeRequest
from ..llm_judge.service import LLMJudgeService

logger = logging.getLogger(__name__)


class OrchestrationEvaluator(BaseEvaluator):
    """Evaluator for orchestration-type agents."""
    
    def __init__(
        self,
        agent_id: int,
        agent_config: Dict[str, Any],
        seaf_api_base: str,
        seaf_api_key: str,
        llm_judge: LLMJudgeService,
    ) -> None:
        super().__init__(agent_id, agent_config, seaf_api_base, seaf_api_key, llm_judge)
        self.timeout = settings.evaluation_reasoning_timeout
        self.max_retries = settings.evaluation_max_retries
        self._reasoning_evaluator: Optional[ReasoningEvaluator] = None
    
    def _get_reasoning_evaluator(self) -> ReasoningEvaluator:
        """Get or create the sub-agent reasoning evaluator."""
        if self._reasoning_evaluator is None:
            self._reasoning_evaluator = ReasoningEvaluator(
                agent_id=self.agent_id,
                agent_config=self.agent_config,
                seaf_api_base=self.seaf_api_base,
                seaf_api_key=self.seaf_api_key,
                llm_judge=self.llm_judge,
            )
        return self._reasoning_evaluator
    
    async def close(self) -> None:
        if self._reasoning_evaluator:
            await self._reasoning_evaluator.close()
    
    def get_evaluation_dimensions(self) -> List[str]:
        return [
            "orchestration_reasonableness",
            "sub_agent_effectiveness",
            "result_aggregation",
            "end_to_end_effectiveness",
        ]
    
    async def _call_orchestration_ask(
        self,
        query: str,
        include_call_chain: bool = True,
    ) -> Dict[str, Any]:
        """Call Seaf orchestration_ask API."""
        import httpx
        async with httpx.AsyncClient(
            base_url=self.seaf_api_base,
            timeout=self.timeout,
        ) as client:
            headers = {
                "Authorization": f"Bearer {self.seaf_api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "agent_id": self.agent_id,
                "query": query,
                "include_call_chain": include_call_chain,
            }
            
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        "/api/v1/agents/orchestration/ask",
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    logger.warning(f"Orchestration attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        raise
    
    def _extract_sub_agent_calls(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract sub-agent call chain from orchestration response.
        
        Expected format:
        {
            "call_chain": [
                {
                    "sub_agent_id": "...",
                    "sub_agent_name": "...",
                    "query": "...",
                    "result": "...",
                    "calls": [...]  # nested calls
                }
            ]
        }
        """
        call_chain: List[Dict[str, Any]] = []
        raw_chain = response_data.get("call_chain", [])
        
        def flatten_chain(chain: List[Dict[str, Any]], depth: int = 0) -> None:
            for item in chain:
                call_chain.append({
                    "sub_agent_id": item.get("sub_agent_id", ""),
                    "sub_agent_name": item.get("sub_agent_name", ""),
                    "query": item.get("query", ""),
                    "result": item.get("result", ""),
                    "depth": depth,
                    "calls": item.get("calls", []),
                })
                if item.get("calls"):
                    flatten_chain(item["calls"], depth + 1)
        
        flatten_chain(raw_chain)
        return call_chain
    
    def _detect_dead_loop(self, call_chain: List[Dict[str, Any]]) -> bool:
        """
        Detect if there's a dead loop (same sub-agent called repeatedly).
        A dead loop is detected if the same sub-agent appears consecutively
        more than a threshold (e.g., 3 times).
        """
        if not call_chain:
            return False
        
        recent_calls: List[str] = []
        threshold = 3
        
        for call in call_chain:
            agent_name = call.get("sub_agent_name", "")
            recent_calls.append(agent_name)
            
            # Keep only the last `threshold + 1` calls
            if len(recent_calls) > threshold + 1:
                recent_calls.pop(0)
            
            # Check for repeating pattern
            if len(recent_calls) >= threshold:
                if len(set(recent_calls)) == 1:
                    return True
        
        return False
    
    def _check_sub_agent_order(
        self,
        call_chain: List[Dict[str, Any]],
        expected_order: List[str],
    ) -> float:
        """Check if sub-agents were called in the expected order."""
        if not expected_order:
            return 100.0
        
        actual_order = [
            call.get("sub_agent_name", "") 
            for call in call_chain 
            if call.get("sub_agent_name")
        ]
        
        if not actual_order:
            return 0.0
        
        correct_positions = 0
        for i, name in enumerate(expected_order):
            if i < len(actual_order) and actual_order[i] == name:
                correct_positions += 1
        
        return (correct_positions / len(expected_order)) * 100
    
    def _get_final_response(self, response_data: Dict[str, Any]) -> str:
        """Extract final orchestration response."""
        return response_data.get("response", "") or response_data.get("result", "")
    
    def judge(
        self,
        output: Dict[str, Any],
        expected_sub_agents: Optional[List[str]] = None,
        expected_order: Optional[List[str]] = None,
        max_sub_agent_calls: Optional[int] = None,
    ) -> EvaluationResult:
        """Rule-based judgment for orchestration execution."""
        call_chain = self._extract_sub_agent_calls(output)
        has_dead_loop = self._detect_dead_loop(call_chain)
        order_score = self._check_sub_agent_order(call_chain, expected_order or [])
        
        # Check sub-agent coverage
        expected_set = set(expected_sub_agents or [])
        actual_agents = {c.get("sub_agent_name") for c in call_chain}
        matched = len(actual_agents & expected_set) if expected_set else len(actual_agents)
        coverage = (matched / len(expected_set)) * 100 if expected_set else 100.0
        
        # Check max calls
        exceeded_max = max_sub_agent_calls and len(call_chain) > max_sub_agent_calls
        
        orchestration_score = 100.0 if not has_dead_loop else 30.0
        sub_agent_score = 100.0 if not exceeded_max else 50.0
        
        passed = not has_dead_loop and not exceeded_max
        
        return EvaluationResult(
            passed=passed,
            scores={
                "orchestration_reasonableness": orchestration_score,
                "sub_agent_effectiveness": sub_agent_score,
                "result_aggregation": coverage,
                "end_to_end_effectiveness": order_score,
            },
            weighted_score=(orchestration_score + sub_agent_score + coverage + order_score) / 4,
            sub_agent_call_log=call_chain,
        )
    
    async def _evaluate_sub_agents(
        self,
        call_chain: List[Dict[str, Any]],
        test_case: EvalCase,
    ) -> List[EvaluationOutput]:
        """Evaluate sub-agents using the reasoning evaluator."""
        reasoning_eval = self._get_reasoning_evaluator()
        results: List[EvaluationOutput] = []
        
        for call in call_chain:
            query = call.get("query", "")
            if not query:
                continue
            
            # Create a minimal test case for sub-agent evaluation
            sub_case = EvalCase(
                name=f"sub_agent_{call.get('sub_agent_name', 'unknown')}",
                query=query,
                expected_tools=test_case.expected_tools,
            )
            
            try:
                result = await reasoning_eval.evaluate(sub_case)
                results.append(result)
            except Exception as e:
                logger.warning(f"Sub-agent evaluation failed: {e}")
                results.append(EvaluationOutput(
                    result=EvaluationResult(passed=False, error_message=str(e)),
                    latency_ms=0,
                ))
        
        return results
    
    async def evaluate(
        self,
        case: EvalCase,
        session_id: Optional[str] = None,
    ) -> EvaluationOutput:
        """
        Evaluate an orchestration agent on a single test case.
        
        1. Call Seaf orchestration_ask API with include_call_chain=true
        2. Parse sub_agent_call_log
        3. Detect dead loops
        4. Call LLM judge for orchestration evaluation
        5. Call reasoning evaluator for sub-agent tool usage
        6. Return combined evaluation result
        """
        start_time = time.time()
        
        try:
            # Step 1: Call orchestration API
            response_data = await self._call_orchestration_ask(case.query)
            
            # Step 2: Extract sub-agent call chain
            call_chain = self._extract_sub_agent_calls(response_data)
            agent_response = self._get_final_response(response_data)
            
            # Step 3: Dead loop detection
            has_dead_loop = self._detect_dead_loop(call_chain)
            if has_dead_loop:
                logger.warning(f"Dead loop detected in call chain for case {case.name}")
            
            # Step 4: Check max_sub_agent_calls constraint
            max_calls = case.max_sub_agent_calls or 10
            exceeded_max = len(call_chain) > max_calls
            
            # Step 5: Order checking
            order_score = self._check_sub_agent_order(call_chain, case.expected_order or [])
            
            # Step 6: LLM-based orchestration evaluation
            judge_request = JudgeRequest(
                user_query=case.query,
                agent_response=agent_response,
                sub_agent_call_log=call_chain,
                expected_sub_agents=case.expected_sub_agents or [],
                expected_order=case.expected_order or [],
                agent_type="orchestration",
            )
            
            judge_response = await self.llm_judge.judge_orchestration(judge_request)
            
            # Step 7: Evaluate sub-agents for tool usage
            sub_agent_results = await self._evaluate_sub_agents(call_chain, case)
            
            # Step 8: Combine scores
            # Adjust orchestration scores based on dead loop and max calls
            adjusted_scores = dict(judge_response.scores)
            if has_dead_loop:
                adjusted_scores["orchestration_reasonableness"] = min(
                    adjusted_scores.get("orchestration_reasonableness", 100), 30
                )
            if exceeded_max:
                adjusted_scores["sub_agent_effectiveness"] = min(
                    adjusted_scores.get("sub_agent_effectiveness", 100), 50
                )
            
            final_result = EvaluationResult(
                passed=not has_dead_loop and not exceeded_max,
                scores=adjusted_scores,
                weighted_score=judge_response.weighted_score,
                sub_agent_call_log=call_chain,
                judge_response=judge_response,
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            return EvaluationOutput(
                result=final_result,
                raw_response=agent_response,
                latency_ms=elapsed_ms,
            )
        
        except Exception as e:
            logger.error(f"Orchestration evaluation failed for case {case.name}: {e}")
            elapsed_ms = int((time.time() - start_time) * 1000)
            return EvaluationOutput(
                result=EvaluationResult(
                    passed=False,
                    error_message=str(e),
                ),
                latency_ms=elapsed_ms,
            )
