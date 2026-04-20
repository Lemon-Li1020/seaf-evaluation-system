"""
Celery application configuration.
"""

from celery import Celery

from ..config import settings


def create_celery_app() -> Celery:
    """Create and configure Celery application."""
    app = Celery(
        "evaluation_worker",
        broker=settings.celery_broker_url or "memory://",
        backend=settings.celery_result_backend or None,
    )
    
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Shanghai",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max per task
        task_soft_time_limit=3300,  # 55 minutes soft limit
        task_routes={
            "evaluation_system.worker.tasks.run_evaluation": {"queue": "evaluation"},
            "evaluation_system.worker.tasks.cleanup_old_results": {"queue": "maintenance"},
            "evaluation_system.worker.tasks.check_pending_tasks": {"queue": "maintenance"},
        },
    )
    
    return app


# Create global app instance
celery_app = create_celery_app()
