"""
Task service for managing evaluation tasks.
"""

import uuid
from typing import List, Optional
from datetime import datetime

from ..database import Database
from ..models import (
    EvaluationTask,
    CreateTaskRequest,
    TaskStatus,
    AgentType,
)
from ..evaluator.executor import EvaluationExecutor
from ..worker.celery_app import celery_app


class TaskService:
    """Service for managing evaluation tasks."""
    
    def __init__(self, db: Database) -> None:
        self.db = db
        self._executor: Optional[EvaluationExecutor] = None
    
    @property
    def executor(self) -> EvaluationExecutor:
        if self._executor is None:
            self._executor = EvaluationExecutor(self.db)
        return self._executor
    
    async def create_task(
        self,
        request: CreateTaskRequest,
    ) -> EvaluationTask:
        """Create a new evaluation task."""
        task = EvaluationTask(
            task_uuid=str(uuid.uuid4()),
            team_id=request.team_id,
            test_set_id=request.test_set_id,
            agent_id=request.agent_id,
            agent_type=request.agent_type,
            agent_version=request.agent_version or "latest",
            trigger=request.trigger,
            status="pending",
            total_cases=0,
            completed_cases=0,
            progress=0.0,
        )
        created = await self.db.create_task(task)
        
        # Trigger async execution via Celery
        if celery_app.conf.task_always_eager:
            # Run synchronously in test mode
            await self.executor.run_task(created.id)
        else:
            celery_app.send_task(
                "evaluation_system.worker.tasks.run_evaluation",
                args=[created.id],
            )
        
        return created
    
    async def get_task(self, task_id: int) -> Optional[EvaluationTask]:
        """Get a task by ID."""
        return await self.db.get_task(task_id)
    
    async def list_tasks(
        self,
        team_id: int,
        agent_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
    ) -> List[EvaluationTask]:
        """List tasks with optional filters."""
        return await self.db.list_tasks(team_id, agent_id, status)
    
    async def update_task_status(
        self,
        task_id: int,
        status: TaskStatus,
        error_message: Optional[str] = None,
    ) -> None:
        """Update task status."""
        await self.db.update_task_status(task_id, status, error_message=error_message)
    
    async def get_task_progress(self, task_id: int) -> Optional[dict]:
        """Get task progress information."""
        task = await self.db.get_task(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.id,
            "status": task.status,
            "total_cases": task.total_cases,
            "completed_cases": task.completed_cases,
            "progress": task.progress,
            "error_message": task.error_message,
        }
    
    async def get_task_results(self, task_id: int) -> List[dict]:
        """Get all case results for a task."""
        results = await self.db.get_case_results(task_id)
        return [
            {
                "id": r.id,
                "test_case_id": r.test_case_id,
                "query": r.query,
                "agent_response": r.agent_response,
                "scores": r.scores,
                "weighted_score": r.weighted_score,
                "passed": r.passed,
                "latency_ms": r.latency_ms,
                "confidence": r.confidence,
                "needs_human_review": r.needs_human_review,
                "error_message": r.error_message,
            }
            for r in results
        ]
