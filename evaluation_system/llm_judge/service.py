"""
LLM Judge service for evaluating agent responses.
"""

import json
import logging
from typing import Optional, Dict, Any

import httpx

from ..config import settings
from ..models import (
    JudgeRequest,
    JudgeResponse,
)
from .prompts import (
    REASONING_JUDGE_PROMPT,
    WORKFLOW_JUDGE_PROMPT,
    ORCHESTRATION_JUDGE_PROMPT,
    SIMPLIFIED_REASONING_PROMPT,
    SIMPLIFIED_WORKFLOW_PROMPT,
    SIMPLIFIED_ORCHESTRATION_PROMPT,
    DIMENSION_WEIGHTS,
)

logger = logging.getLogger(__name__)


class LLMJudgeService:
    """Service for LLM-based evaluation of agent responses."""
    
    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.timeout = settings.llm_timeout
        self.max_retries = settings.llm_max_retries
        self.temperature = settings.llm_temperature
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _get_prompt(self, agent_type: str, simplified: bool = False) -> str:
        """Get the appropriate prompt template."""
        prompts = {
            "reasoning": (REASONING_JUDGE_PROMPT, SIMPLIFIED_REASONING_PROMPT),
            "workflow": (WORKFLOW_JUDGE_PROMPT, SIMPLIFIED_WORKFLOW_PROMPT),
            "orchestration": (ORCHESTRATION_JUDGE_PROMPT, SIMPLIFIED_ORCHESTRATION_PROMPT),
        }
        full, simple = prompts.get(agent_type, (REASONING_JUDGE_PROMPT, SIMPLIFIED_REASONING_PROMPT))
        return simple if simplified else full
    
    def _build_prompt_content(self, request: JudgeRequest) -> Dict[str, Any]:
        """Build the content dictionary for prompt formatting."""
        return {
            "user_query": request.user_query,
            "agent_response": request.agent_response or "[No response]",
            "tool_call_log": json.dumps(request.tool_call_log or [], ensure_ascii=False),
            "node_execution_log": json.dumps(request.node_execution_log or [], ensure_ascii=False),
            "sub_agent_call_log": json.dumps(request.sub_agent_call_log or [], ensure_ascii=False),
            "expected_tools": ", ".join(request.expected_tools or ["any"]) or "any",
            "expected_nodes": ", ".join(request.expected_nodes or []),
            "expected_sub_agents": ", ".join(request.expected_sub_agents or []),
            "expected_order": ", ".join(request.expected_order or []),
        }
    
    def _calculate_weighted_score(
        self,
        scores: Dict[str, float],
        agent_type: str,
    ) -> float:
        """Calculate weighted score from dimension scores."""
        weights = DIMENSION_WEIGHTS.get(agent_type, {})
        if not scores or not weights:
            return sum(scores.values()) / len(scores) if scores else 0.0
        
        total_weight = sum(weights.values())
        weighted = sum(
            scores.get(dim, 0) * (weights.get(dim, 0) / total_weight)
            for dim in scores
        )
        return round(weighted, 2)
    
    async def _call_llm(
        self,
        prompt: str,
        retry_count: int = 0,
    ) -> str:
        """Make an LLM API call."""
        client = await self._get_client()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert evaluation judge. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
        }
        
        try:
            response = await client.post(
                "/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.warning(f"LLM HTTP error: {e.response.status_code}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"LLM response parse error: {e}")
            raise ValueError(f"Invalid LLM response format: {e}")
        except Exception as e:
            if retry_count < self.max_retries:
                return await self._call_llm(prompt, retry_count + 1)
            raise
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with fallback handling."""
        # Try direct JSON parse
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from the text
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Could not parse JSON from: {content[:200]}")
    
    def _build_default_response(
        self,
        request: JudgeRequest,
        reason: str,
    ) -> JudgeResponse:
        """Build a default response when LLM call fails."""
        # Calculate reasonable defaults based on agent type
        scores = {}
        if request.agent_type == "reasoning":
            scores = {"correctness": 70, "tool_usage": 70, "efficiency": 70, "relevance": 70}
        elif request.agent_type == "workflow":
            scores = {"flow_completeness": 70, "node_performance": 70, "end_to_end_correctness": 70, "latency": 70}
        else:
            scores = {"orchestration_reasonableness": 70, "sub_agent_effectiveness": 70, "result_aggregation": 70, "end_to_end_effectiveness": 70}
        
        weighted = self._calculate_weighted_score(scores, request.agent_type)
        
        return JudgeResponse(
            scores=scores,
            weighted_score=weighted,
            confidence="low",
            needs_human_review=True,
            key_findings=[f"Default score due to: {reason}"],
            main_issues=["LLM evaluation unavailable, using default score"],
            raw_response=None,
        )
    
    async def judge_reasoning(self, request: JudgeRequest) -> JudgeResponse:
        """Evaluate a reasoning agent response."""
        return await self._judge(request, "reasoning")
    
    async def judge_workflow(self, request: JudgeRequest) -> JudgeResponse:
        """Evaluate a workflow agent response."""
        return await self._judge(request, "workflow")
    
    async def judge_orchestration(self, request: JudgeRequest) -> JudgeResponse:
        """Evaluate an orchestration agent response."""
        return await self._judge(request, "orchestration")
    
    async def _judge(self, request: JudgeRequest, agent_type: str) -> JudgeResponse:
        """
        Core judgment logic with three-tier fallback:
        1. Normal prompt with full parsing
        2. Simplified prompt
        3. Default scoring
        """
        # Tier 1: Try with full prompt
        try:
            prompt = self._get_prompt(agent_type, simplified=False)
            content = self._build_prompt_content(request)
            full_prompt = prompt.format(**content)
            
            raw_response = await self._call_llm(full_prompt)
            parsed = self._parse_json_response(raw_response)
            
            return self._build_response_from_parsed(parsed, raw_response, agent_type)
        
        except Exception as e:
            logger.warning(f"Tier 1 failed for {agent_type}: {e}")
        
        # Tier 2: Try with simplified prompt
        try:
            prompt = self._get_prompt(agent_type, simplified=True)
            content = self._build_prompt_content(request)
            simple_prompt = prompt.format(**content)
            
            raw_response = await self._call_llm(simple_prompt)
            parsed = self._parse_json_response(raw_response)
            
            return self._build_response_from_parsed(parsed, raw_response, agent_type)
        
        except Exception as e:
            logger.warning(f"Tier 2 failed for {agent_type}: {e}")
        
        # Tier 3: Default scoring
        return self._build_default_response(request, "LLM unavailable after retries")
    
    def _build_response_from_parsed(
        self,
        parsed: Dict[str, Any],
        raw_response: str,
        agent_type: str,
    ) -> JudgeResponse:
        """Build a JudgeResponse from parsed LLM output."""
        scores = parsed.get("scores", {})
        # Validate scores are within 0-100
        for k, v in list(scores.items()):
            scores[k] = max(0.0, min(100.0, float(v)))
        
        weighted_score = parsed.get("weighted_score")
        if weighted_score is None:
            weighted_score = self._calculate_weighted_score(scores, agent_type)
        
        confidence_str = parsed.get("confidence", "medium")
        if confidence_str not in ("high", "medium", "low"):
            confidence_str = "medium"
        
        return JudgeResponse(
            scores=scores,
            weighted_score=round(float(weighted_score), 2),
            confidence=confidence_str,
            needs_human_review=bool(parsed.get("needs_human_review", False)),
            key_findings=parsed.get("key_findings", []),
            main_issues=parsed.get("main_issues", []),
            raw_response=raw_response,
        )
