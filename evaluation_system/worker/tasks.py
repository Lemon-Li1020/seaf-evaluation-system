"""
Celery tasks for evaluation system.
"""

import logging
from datetime import datetime, timedelta

from .celery_app import celery_app
from ..database import db
from ..evaluator.executor import EvaluationExecutor

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="evaluation_system.worker.tasks.run_evaluation")
def run_evaluation(self, task_id: int) -> dict:
    """
    Run an evaluation task asynchronously.
    
    Args:
        task_id: The evaluation task ID to run
        
    Returns:
        Dict with task result summary
    """
    import asyncio
    
    async def _run():
        executor = EvaluationExecutor(db)
        try:
            report = await executor.run_task(task_id)
            return {
                "status": "completed",
                "report_id": report.id,
                "task_id": task_id,
            }
        except Exception as e:
            logger.error(f"Evaluation task {task_id} failed: {e}")
            return {
                "status": "failed",
                "task_id": task_id,
                "error": str(e),
            }
        finally:
            await executor.llm_judge.close()
    
    return asyncio.run(_run())


@celery_app.task(name="evaluation_system.worker.tasks.cleanup_old_results")
def cleanup_old_results(days: int = 30) -> dict:
    """
    Clean up old evaluation results.
    
    Args:
        days: Number of days to keep results for
        
    Returns:
        Dict with cleanup summary
    """
    logger.info(f"Starting cleanup of results older than {days} days")
    
    # Note: In a real implementation, this would clean up database records
    # For the in-memory mock, this is a no-op
    return {
        "status": "completed",
        "days_threshold": days,
        "cleaned_count": 0,
    }


@celery_app.task(name="evaluation_system.worker.tasks.check_pending_tasks")
def check_pending_tasks() -> dict:
    """
    Check for pending tasks and queue them for processing.
    This is a maintenance task that can run periodically.
    
    Returns:
        Dict with check summary
    """
    logger.info("Checking for pending tasks")
    
    # In a real implementation, this would:
    # 1. Query for pending tasks
    # 2. Queue them for processing
    # 3. Update their status
    
    return {
        "status": "completed",
        "pending_count": 0,
    }
