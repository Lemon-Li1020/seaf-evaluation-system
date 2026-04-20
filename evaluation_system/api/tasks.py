"""
Evaluation tasks API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from ..models import (
    EvaluationTask,
    CreateTaskRequest,
    TaskProgressResponse,
    TaskStatus,
)
from ..service.task_service import TaskService
from ..database import db

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_service() -> TaskService:
    return TaskService(db)


@router.post("", response_model=EvaluationTask)
async def create_task(
    request: CreateTaskRequest,
    service: TaskService = Depends(get_service),
) -> EvaluationTask:
    """Create a new evaluation task and trigger execution."""
    return await service.create_task(request)


@router.get("", response_model=List[EvaluationTask])
async def list_tasks(
    team_id: int,
    agent_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    service: TaskService = Depends(get_service),
) -> List[EvaluationTask]:
    """List evaluation tasks with optional filters."""
    return await service.list_tasks(team_id, agent_id, status)


@router.get("/{task_id}", response_model=EvaluationTask)
async def get_task(
    task_id: int,
    service: TaskService = Depends(get_service),
) -> EvaluationTask:
    """Get a task by ID."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}/progress", response_model=TaskProgressResponse)
async def get_task_progress(
    task_id: int,
    service: TaskService = Depends(get_service),
) -> TaskProgressResponse:
    """Get task progress information."""
    progress = await service.get_task_progress(task_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskProgressResponse(**progress)


@router.get("/{task_id}/results")
async def get_task_results(
    task_id: int,
    service: TaskService = Depends(get_service),
) -> List[dict]:
    """Get all case results for a task."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return await service.get_task_results(task_id)
