"""
Base evaluator class for agent evaluation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Any, Dict

from ..models import EvalCase, EvaluationOutput, EvaluationResult, AgentType
from ..llm_judge.service import LLMJudgeService


class BaseEvaluator(ABC):
    """Abstract base class for all agent evaluators."""
    
    def __init__(
        self,
        agent_id: int,
        agent_config: Dict[str, Any],
        seaf_api_base: str,
        seaf_api_key: str,
        llm_judge: LLMJudgeService,
    ) -> None:
        self.agent_id = agent_id
        self.agent_config = agent_config
        self.seaf_api_base = seaf_api_base
        self.seaf_api_key = seaf_api_key
        self.llm_judge = llm_judge
    
    @abstractmethod
    async def evaluate(
        self,
        case: EvalCase,
        session_id: Optional[str] = None,
    ) -> EvaluationOutput:
        """
        Evaluate a single test case against the agent.
        
        Args:
            case: The test case to evaluate
            session_id: Optional session ID for maintaining context
            
        Returns:
            EvaluationOutput containing the evaluation result
        """
        ...
    
    @abstractmethod
    def get_evaluation_dimensions(self) -> List[str]:
        """Return list of evaluation dimension names."""
        ...
    
    async def batch_evaluate(
        self,
        cases: List[EvalCase],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[EvaluationOutput]:
        """
        Evaluate multiple test cases.
        
        Args:
            cases: List of test cases to evaluate
            progress_callback: Optional callback(completed, total) for progress updates
            
        Returns:
            List of evaluation outputs
        """
        results: List[EvaluationOutput] = []
        total = len(cases)
        
        for idx, case in enumerate(cases):
            try:
                result = await self.evaluate(case)
                results.append(result)
            except Exception as e:
                # Return a failed result
                results.append(EvaluationOutput(
                    result=EvaluationResult(
                        passed=False,
                        error_message=str(e),
                    ),
                    latency_ms=0,
                ))
            
            if progress_callback:
                progress_callback(idx + 1, total)
        
        return results
