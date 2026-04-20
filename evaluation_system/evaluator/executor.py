"""
Evaluation executor - orchestrates the full evaluation pipeline.
"""

import logging
from typing import Optional, List, Dict, Any, Callable

from ..config import settings
from ..models import (
    EvalCase,
    EvaluationTask,
    TestCaseResult,
    EvaluationReport,
    TestSet,
    AgentType,
)
from ..database import Database
from ..llm_judge.service import LLMJudgeService
from ..utils.grade import calculate_grade
from .base import BaseEvaluator
from .reasoning_evaluator import ReasoningEvaluator
from .workflow_evaluator import WorkflowEvaluator
from .orchestration_evaluator import OrchestrationEvaluator

logger = logging.getLogger(__name__)


class EvaluationExecutor:
    """Main executor for running evaluation tasks."""
    
    def __init__(
        self,
        db: Database,
        llm_judge: Optional[LLMJudgeService] = None,
    ) -> None:
        self.db = db
        self.llm_judge = llm_judge or LLMJudgeService()
        self.seaf_api_base = settings.seaf_api_base
        self.seaf_api_key = settings.seaf_api_key
        self.regression_threshold = settings.regression_threshold
    
    def _create_evaluator(
        self,
        agent_type: AgentType,
        agent_id: int,
        agent_config: Optional[Dict[str, Any]] = None,
    ) -> BaseEvaluator:
        """Factory method to create the appropriate evaluator."""
        agent_config = agent_config or {}
        llm = self.llm_judge
        
        if agent_type == "reasoning":
            return ReasoningEvaluator(
                agent_id=agent_id,
                agent_config=agent_config,
                seaf_api_base=self.seaf_api_base,
                seaf_api_key=self.seaf_api_key,
                llm_judge=llm,
            )
        elif agent_type == "workflow":
            return WorkflowEvaluator(
                agent_id=agent_id,
                agent_config=agent_config,
                seaf_api_base=self.seaf_api_base,
                seaf_api_key=self.seaf_api_key,
                llm_judge=llm,
            )
        else:  # orchestration
            return OrchestrationEvaluator(
                agent_id=agent_id,
                agent_config=agent_config,
                seaf_api_base=self.seaf_api_base,
                seaf_api_key=self.seaf_api_key,
                llm_judge=llm,
            )
    
    async def run_task(
        self,
        task_id: int,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ) -> EvaluationReport:
        """
        Run a full evaluation task.
        
        Args:
            task_id: The evaluation task ID
            progress_callback: Optional callback(completed, total, progress) for progress updates
            
        Returns:
            EvaluationReport with aggregated results
        """
        from datetime import datetime
        
        # Get task and test set
        task = await self.db.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        test_set = await self.db.get_test_set(task.test_set_id)
        if not test_set:
            raise ValueError(f"TestSet {task.test_set_id} not found")
        
        cases = await self.db.get_test_cases(task.test_set_id)
        if not cases:
            raise ValueError(f"No test cases found for test set {task.test_set_id}")
        
        # Update task status to running
        await self.db.update_task_status(
            task_id,
            "running",
            started_at=datetime.utcnow(),
        )
        
        # Create evaluator
        evaluator = self._create_evaluator(task.agent_type, task.agent_id)
        
        try:
            # Update total cases
            await self.db.update_task_status(task_id, "running")
            task.total_cases = len(cases)
            
            # Evaluate each case
            all_results: List[TestCaseResult] = []
            all_scores: List[Dict[str, float]] = []
            
            for idx, case in enumerate(cases):
                try:
                    output = await evaluator.evaluate(case)
                    result = output.result
                    
                    # Save case result
                    case_result = TestCaseResult(
                        task_id=task_id,
                        test_case_id=case.id or 0,
                        query=case.query,
                        agent_response=output.raw_response,
                        tool_call_log=result.tool_call_log,
                        node_execution_log=result.node_execution_log,
                        sub_agent_call_log=result.sub_agent_call_log,
                        scores=result.scores,
                        weighted_score=result.weighted_score,
                        passed=result.passed,
                        latency_ms=output.latency_ms,
                        llm_response=result.judge_response.raw_response if result.judge_response else None,
                        confidence=result.judge_response.confidence if result.judge_response else None,
                        needs_human_review=result.judge_response.needs_human_review if result.judge_response else False,
                        error_message=result.error_message,
                    )
                    
                    await self.db.save_case_result(case_result)
                    all_results.append(case_result)
                    
                    if result.scores:
                        all_scores.append(result.scores)
                    
                except Exception as e:
                    logger.error(f"Failed to evaluate case {case.name}: {e}")
                    error_result = TestCaseResult(
                        task_id=task_id,
                        test_case_id=case.id or 0,
                        query=case.query,
                        error_message=str(e),
                        passed=False,
                    )
                    await self.db.save_case_result(error_result)
                    all_results.append(error_result)
                
                # Update progress
                progress = (idx + 1) / len(cases)
                await self.db.update_task_progress(task_id, idx + 1, progress)
                
                if progress_callback:
                    progress_callback(idx + 1, len(cases), progress)
            
            # Calculate aggregated scores by dimension
            by_dimension = self._aggregate_scores(all_scores)
            
            # Calculate overall weighted score
            overall_score = sum(r.weighted_score for r in all_results) / len(all_results) if all_results else 0.0
            
            # Calculate grade
            grade = calculate_grade(overall_score, by_dimension)
            
            # Check for regression
            regression = await self._check_regression(
                task.agent_id,
                overall_score,
            )
            
            # Generate summary
            passed_count = sum(1 for r in all_results if r.passed)
            summary = {
                "total_cases": len(cases),
                "passed": passed_count,
                "failed": len(cases) - passed_count,
                "pass_rate": round(passed_count / len(cases) * 100, 2) if cases else 0,
                "overall_score": round(overall_score, 2),
                "grade": grade,
                "avg_latency_ms": round(
                    sum(r.latency_ms for r in all_results) / len(all_results)
                    if all_results else 0,
                    2,
                ),
                "needs_human_review_count": sum(
                    1 for r in all_results if r.needs_human_review
                ),
            }
            
            # Save report
            report = EvaluationReport(
                task_id=task_id,
                team_id=task.team_id,
                agent_id=task.agent_id,
                test_set_id=task.test_set_id,
                summary=summary,
                by_dimension=by_dimension,
                regression=regression,
            )
            
            saved_report = await self.db.save_report(report)
            
            # Update task as completed
            await self.db.update_task_status(
                task_id,
                "completed",
                completed_at=datetime.utcnow(),
                duration_ms=int(
                    (datetime.utcnow() - (task.started_at or datetime.utcnow())).total_seconds() * 1000
                ),
            )
            
            return saved_report
        
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await self.db.update_task_status(
                task_id,
                "failed",
                error_message=str(e),
            )
            raise
        
        finally:
            await evaluator.close()
    
    def _aggregate_scores(self, all_scores: List[Dict[str, float]]) -> Dict[str, float]:
        """Aggregate scores across all cases by dimension."""
        if not all_scores:
            return {}
        
        # Collect all dimension names
        dimensions: Dict[str, List[float]] = {}
        for scores in all_scores:
            for dim, score in scores.items():
                if dim not in dimensions:
                    dimensions[dim] = []
                dimensions[dim].append(score)
        
        # Calculate average per dimension
        return {
            dim: round(sum(vals) / len(vals), 2)
            for dim, vals in dimensions.items()
        }
    
    async def _check_regression(
        self,
        agent_id: int,
        current_score: float,
    ) -> Optional[Dict[str, Any]]:
        """Check if the current score represents a regression from the previous run."""
        previous_report = await self.db.get_latest_report(agent_id)
        
        if not previous_report:
            return None
        
        previous_score = previous_report.summary.get("overall_score", 0)
        diff = current_score - previous_score
        
        regression: Dict[str, Any] = {
            "previous_score": previous_score,
            "current_score": current_score,
            "diff": round(diff, 2),
            "is_regression": diff < -self.regression_threshold,
        }
        
        if regression["is_regression"]:
            regression["message"] = (
                f"Score dropped by {abs(diff):.1f} points "
                f"(threshold: {self.regression_threshold})"
            )
        
        return regression
    
    async def generate_report(self, task_id: int) -> Optional[EvaluationReport]:
        """Get or generate a report for a task."""
        report = await self.db.get_report(task_id)
        if not report:
            # Run the task to generate a report
            report = await self.run_task(task_id)
        return report
