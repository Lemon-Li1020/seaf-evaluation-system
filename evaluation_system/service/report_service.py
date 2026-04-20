"""
Report service for generating and comparing evaluation reports.
"""

from typing import List, Optional, Dict, Any

from ..database import Database
from ..models import EvaluationReport


class ReportService:
    """Service for managing evaluation reports."""
    
    def __init__(self, db: Database) -> None:
        self.db = db
    
    def _find_report_by_id(self, report_id: int) -> Optional[EvaluationReport]:
        """Find a report by its ID."""
        for r in self.db._reports.values():
            if r.id == report_id:
                return r
        return None
    
    async def get_report(self, task_id: int) -> Optional[EvaluationReport]:
        """Get report for a specific task."""
        return await self.db.get_report(task_id)
    
    async def list_reports(
        self,
        team_id: int,
        agent_id: Optional[int] = None,
    ) -> List[EvaluationReport]:
        """List reports with optional filters."""
        return await self.db.list_reports(team_id, agent_id)
    
    async def get_latest_report(self, agent_id: int) -> Optional[EvaluationReport]:
        """Get the most recent report for an agent."""
        return await self.db.get_latest_report(agent_id)
    
    async def compare_reports(
        self,
        report_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Compare multiple reports side by side.
        
        Args:
            report_ids: List of report IDs to compare
            
        Returns:
            Dict with comparison data
        """
        reports = []
        for rid in report_ids:
            # Find report by iterating through internal storage
            report = self._find_report_by_id(rid)
            if report:
                reports.append(report)
        
        if not reports:
            return {"error": "No reports found", "reports": []}
        
        # Build comparison
        comparison = {
            "reports": [],
            "dimensions": {},
        }
        
        all_dims = set()
        for r in reports:
            all_dims.update(r.by_dimension.keys())
        
        for report in reports:
            report_data = {
                "id": report.id,
                "task_id": report.task_id,
                "agent_id": report.agent_id,
                "summary": report.summary,
                "by_dimension": report.by_dimension,
                "regression": report.regression,
            }
            comparison["reports"].append(report_data)
        
        # Aggregate dimension comparisons
        for dim in all_dims:
            dim_scores = []
            for r in reports:
                if dim in r.by_dimension:
                    dim_scores.append(r.by_dimension[dim])
            
            if dim_scores:
                comparison["dimensions"][dim] = {
                    "scores": dim_scores,
                    "avg": round(sum(dim_scores) / len(dim_scores), 2),
                    "max": max(dim_scores),
                    "min": min(dim_scores),
                }
        
        return comparison
    
    async def get_report_summary(self, report: EvaluationReport) -> Dict[str, Any]:
        """Get a formatted summary of a report."""
        return {
            "report_id": report.id,
            "task_id": report.task_id,
            "agent_id": report.agent_id,
            "grade": report.summary.get("grade", "N/A"),
            "overall_score": report.summary.get("overall_score", 0),
            "pass_rate": report.summary.get("pass_rate", 0),
            "total_cases": report.summary.get("total_cases", 0),
            "by_dimension": report.by_dimension,
            "regression": report.regression,
        }
