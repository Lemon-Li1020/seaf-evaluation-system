"""
Tests for ReportService.
"""

import pytest

from evaluation_system.service.report_service import ReportService
from evaluation_system.database import Database
from evaluation_system.models import EvaluationReport


class TestReportService:
    """Test cases for ReportService."""
    
    @pytest.fixture
    def service(self, db):
        return ReportService(db)
    
    @pytest.fixture
    def sample_report(self):
        return EvaluationReport(
            id=1,
            task_id=1,
            team_id=1,
            agent_id=1,
            test_set_id=1,
            summary={
                "total_cases": 10,
                "passed": 8,
                "failed": 2,
                "pass_rate": 80.0,
                "overall_score": 85.5,
                "grade": "B",
            },
            by_dimension={
                "correctness": 88.0,
                "tool_usage": 82.0,
                "efficiency": 85.0,
                "relevance": 87.0,
            },
        )
    
    @pytest.mark.asyncio
    async def test_get_report(self, service, db, sample_report):
        """Test getting a report by task ID."""
        # Save report first
        await db.save_report(sample_report)
        
        report = await service.get_report(1)
        
        assert report is not None
        assert report.id == 1
        assert report.task_id == 1
    
    @pytest.mark.asyncio
    async def test_get_report_not_found(self, service):
        """Test getting a non-existent report."""
        report = await service.get_report(999)
        assert report is None
    
    @pytest.mark.asyncio
    async def test_list_reports(self, service, db):
        """Test listing reports with filters."""
        # Create multiple reports
        for i in range(3):
            report = EvaluationReport(
                task_id=i + 1,
                team_id=1,
                agent_id=1,
                test_set_id=1,
                summary={"grade": "B"},
                by_dimension={},
            )
            await db.save_report(report)
        
        reports = await service.list_reports(team_id=1)
        
        assert len(reports) == 3
    
    @pytest.mark.asyncio
    async def test_list_reports_filter_by_agent(self, service, db):
        """Test listing reports filtered by agent ID."""
        # Create reports for different agents
        for agent_id in [1, 2, 3]:
            report = EvaluationReport(
                task_id=agent_id,
                team_id=1,
                agent_id=agent_id,
                test_set_id=1,
                summary={"grade": "B"},
                by_dimension={},
            )
            await db.save_report(report)
        
        reports = await service.list_reports(team_id=1, agent_id=2)
        
        assert len(reports) == 1
        assert reports[0].agent_id == 2
    
    @pytest.mark.asyncio
    async def test_compare_reports(self, service, db):
        """Test comparing multiple reports."""
        # Create reports with same team_id
        for i, score in enumerate([85.0, 90.0, 78.0]):
            report = EvaluationReport(
                task_id=i + 1,
                team_id=1,
                agent_id=1,
                test_set_id=1,
                summary={"overall_score": score, "grade": "B"},
                by_dimension={
                    "correctness": score,
                    "tool_usage": score + 2,
                },
            )
            await db.save_report(report)
        
        # Get reports
        all_reports = await db.list_reports(team_id=1)
        report_ids = [r.id for r in all_reports]
        
        comparison = await service.compare_reports(report_ids)
        
        assert "reports" in comparison
        assert "dimensions" in comparison
        assert len(comparison["reports"]) == 3
        assert "correctness" in comparison["dimensions"]
    
    @pytest.mark.asyncio
    async def test_get_report_summary(self, service, sample_report):
        """Test generating a formatted report summary."""
        summary = await service.get_report_summary(sample_report)
        
        assert summary["report_id"] == 1
        assert summary["task_id"] == 1
        assert summary["grade"] == "B"
        assert summary["overall_score"] == 85.5
        assert summary["pass_rate"] == 80.0
        assert summary["total_cases"] == 10
        assert "by_dimension" in summary
        assert "regression" in summary
