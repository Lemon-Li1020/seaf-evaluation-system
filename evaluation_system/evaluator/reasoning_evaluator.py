"""
Reasoning agent evaluator.
"""

import json
import logging
import time
import httpx
from typing import Optional, List, Dict, Any

from .base import BaseEvaluator
from ..config import settings
from ..models import (
    EvalCase,
    EvaluationOutput,
    EvaluationResult,
    JudgeRequest,
)
from ..llm_judge.service import LLMJudgeService

logger = logging.getLogger(__name__)


class ReasoningEvaluator(BaseEvaluator):
    """Evaluator for reasoning-type agents."""
    
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
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.seaf_api_base,
                timeout=self.timeout,
            )
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def get_evaluation_dimensions(self) -> List[str]:
        return ["correctness", "tool_usage", "efficiency", "relevance"]
    
    async def _call_chat_agent(
        self,
        query: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Call the Seaf chat_agent_ask API.
        Returns the response dict.
        """
        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {self.seaf_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "agent_id": self.agent_id,
            "query": query,
            "session_id": session_id or "",
        }
        
        for attempt in range(self.max_retries):
            try:
                response = await client.post(
                    "/api/v1/agents/chat",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    raise
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
        
        raise RuntimeError("Max retries exceeded for chat_agent_ask")
    
    def _extract_tool_calls(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract tool call log from the response.
        
        Expected response format:
        {
            "messages": [
                {"role": "assistant", "content": "..."},
                {"role": "tool", "tool_call_id": "...", "name": "...", ...}
            ]
        }
        """
        tool_calls: List[Dict[str, Any]] = []
        messages = response_data.get("messages", [])
        
        for msg in messages:
            if msg.get("role") == "assistant":
                # Check for tool_calls in the message
                msg_tool_calls = msg.get("tool_calls", [])
                for tc in msg_tool_calls:
                    tool_calls.append({
                        "name": tc.get("name", "unknown"),
                        "arguments": tc.get("arguments", {}),
                        "tool_call_id": tc.get("id", ""),
                    })
            elif msg.get("role") == "tool":
                tool_calls.append({
                    "name": msg.get("name", "unknown"),
                    "tool_call_id": msg.get("tool_call_id", ""),
                    "content": msg.get("content", ""),
                    "is_result": True,
                })
        
        return tool_calls
    
    def _get_final_response(self, response_data: Dict[str, Any]) -> str:
        """Extract the final text response from the messages."""
        messages = response_data.get("messages", [])
        # Find the last assistant message without tool calls
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and not msg.get("tool_calls"):
                return msg.get("content", "")
        return ""
    
    def judge(
        self,
        output: Dict[str, Any],
        expected_tools: Optional[List[str]] = None,
    ) -> EvaluationResult:
        """
        Judge the evaluation output based on expected tools and response quality.
        
        This is a rule-based judgment used before LLM scoring.
        """
        tool_calls = self._extract_tool_calls(output)
        expected_tools = expected_tools or []
        
        # Check if expected tools were used
        tool_names_used = {tc.get("name") for tc in tool_calls if not tc.get("is_result")}
        expected_set = set(expected_tools)
        
        # Calculate tool match score (0-100)
        if not expected_set:
            tool_score = 100.0
        else:
            matched = len(tool_names_used & expected_set)
            tool_score = (matched / len(expected_set)) * 100 if expected_set else 100.0
        
        # Check for keyword presence in response
        response_text = self._get_final_response(output)
        
        return EvaluationResult(
            passed=len(tool_calls) > 0 or response_text != "",
            scores={"tool_match": tool_score},
            weighted_score=tool_score,
            tool_call_log=tool_calls,
        )
    
    async def evaluate(
        self,
        case: EvalCase,
        session_id: Optional[str] = None,
    ) -> EvaluationOutput:
        """
        Evaluate a reasoning agent on a single test case.
        
        1. Call Seaf chat_agent_ask API
        2. Extract tool call log
        3. Call LLM judge for scoring
        4. Return combined evaluation result
        """
        start_time = time.time()
        
        try:
            # Step 1: Call the agent
            response_data = await self._call_chat_agent(case.query, session_id)
            
            # Step 2: Extract tool calls and response
            tool_calls = self._extract_tool_calls(response_data)
            agent_response = self._get_final_response(response_data)
            
            # Step 3: Rule-based pre-judgment
            pre_result = self.judge(response_data, case.expected_tools)
            
            # Step 4: LLM-based evaluation
            judge_request = JudgeRequest(
                user_query=case.query,
                agent_response=agent_response,
                tool_call_log=tool_calls,
                expected_tools=case.expected_tools or [],
                agent_type="reasoning",
            )
            
            judge_response = await self.llm_judge.judge_reasoning(judge_request)
            
            # Step 5: Combine results
            final_result = EvaluationResult(
                passed=pre_result.passed,
                scores=judge_response.scores,
                weighted_score=judge_response.weighted_score,
                tool_call_log=tool_calls,
                judge_response=judge_response,
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            return EvaluationOutput(
                result=final_result,
                raw_response=agent_response,
                latency_ms=elapsed_ms,
            )
        
        except Exception as e:
            logger.error(f"Evaluation failed for case {case.name}: {e}")
            elapsed_ms = int((time.time() - start_time) * 1000)
            return EvaluationOutput(
                result=EvaluationResult(
                    passed=False,
                    error_message=str(e),
                ),
                latency_ms=elapsed_ms,
            )
