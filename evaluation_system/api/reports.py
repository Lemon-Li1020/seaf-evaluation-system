"""
Reports API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from ..models import EvaluationReport, CompareRequest
from ..service.report_service import ReportService
from ..database import db

router = APIRouter(prefix="/reports", tags=["reports"])


def get_service() -> ReportService:
    return ReportService(db)


@router.get("/tasks/{task_id}/report")
async def get_task_report(
    task_id: int,
    service: ReportService = Depends(get_service),
) -> dict:
    """Get report for a specific task."""
    report = await service.get_report(task_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return await service.get_report_summary(report)


@router.get("")
async def list_reports(
    team_id: int,
    agent_id: Optional[int] = None,
    service: ReportService = Depends(get_service),
) -> List[dict]:
    """List reports with optional filters."""
    reports = await service.list_reports(team_id, agent_id)
    return [await service.get_report_summary(r) for r in reports]


@router.post("/compare")
async def compare_reports(
    request: CompareRequest,
    service: ReportService = Depends(get_service),
) -> dict:
    """Compare multiple reports side by side."""
    return await service.compare_reports(request.report_ids)


@router.get("/agents/{agent_id}/latest")
async def get_latest_report(
    agent_id: int,
    service: ReportService = Depends(get_service),
) -> Optional[dict]:
    """Get the most recent report for an agent."""
    report = await service.get_latest_report(agent_id)
    if not report:
        return None
    return await service.get_report_summary(report)
