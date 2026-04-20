"""
Database operations for Seaf Evaluation System.
In-memory mock implementation using dictionaries with __slots__ pattern.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import copy

from .models import (
    TestSet,
    EvalCase,
    EvaluationTask,
    TestCaseResult,
    EvaluationReport,
    TaskStatus,
)


class Database:
    """
    In-memory database mock using dictionaries.
    Implements the same interface as a real database would.
    """
    
    __slots__ = (
        "_test_sets",
        "_test_cases",
        "_tasks",
        "_case_results",
        "_reports",
        "_counters",
    )
    
    def __init__(self) -> None:
        self._test_sets: Dict[int, TestSet] = {}
        self._test_cases: Dict[int, EvalCase] = {}
        self._tasks: Dict[int, EvaluationTask] = {}
        self._case_results: Dict[int, TestCaseResult] = {}
        self._reports: Dict[int, EvaluationReport] = {}
        self._counters: Dict[str, int] = {
            "test_set": 0,
            "test_case": 0,
            "task": 0,
            "case_result": 0,
            "report": 0,
        }
    
    # ---- TestSet Operations ----
    
    async def create_test_set(self, test_set: TestSet) -> TestSet:
        """Create a new test set."""
        self._counters["test_set"] += 1
        test_set.id = self._counters["test_set"]
        self._test_sets[test_set.id] = copy.deepcopy(test_set)
        return copy.deepcopy(test_set)
    
    async def get_test_set(self, test_set_id: int) -> Optional[TestSet]:
        """Get a test set by ID."""
        ts = self._test_sets.get(test_set_id)
        return copy.deepcopy(ts) if ts else None
    
    async def list_test_sets(
        self,
        team_id: int,
        agent_id: Optional[int] = None,
        agent_type: Optional[str] = None,
    ) -> List[TestSet]:
        """List test sets filtered by criteria."""
        results = [ts for ts in self._test_sets.values() if ts.team_id == team_id]
        if agent_id is not None:
            results = [ts for ts in results if ts.agent_id == agent_id]
        if agent_type is not None:
            results = [ts for ts in results if ts.agent_type == agent_type]
        return copy.deepcopy(results)
    
    async def update_test_set(
        self,
        test_set_id: int,
        **kwargs: Any,
    ) -> Optional[TestSet]:
        """Update a test set fields."""
        ts = self._test_sets.get(test_set_id)
        if not ts:
            return None
        for key, value in kwargs.items():
            if hasattr(ts, key):
                setattr(ts, key, value)
        return copy.deepcopy(ts)
    
    async def delete_test_set(self, test_set_id: int) -> bool:
        """Delete a test set and its cases."""
        if test_set_id not in self._test_sets:
            return False
        del self._test_sets[test_set_id]
        # Cascade delete test cases
        case_ids = [
            cid for cid, c in self._test_cases.items()
            if c.test_set_id == test_set_id
        ]
        for cid in case_ids:
            del self._test_cases[cid]
        return True
    
    # ---- TestCase Operations ----
    
    async def add_test_cases(
        self,
        test_set_id: int,
        cases: List[EvalCase],
    ) -> int:
        """Add test cases to a test set. Returns count added."""
        count = 0
        for case in cases:
            self._counters["test_case"] += 1
            case.id = self._counters["test_case"]
            case.test_set_id = test_set_id
            self._test_cases[case.id] = copy.deepcopy(case)
            count += 1
        # Update total_cases on test set
        if test_set_id in self._test_sets:
            self._test_sets[test_set_id].total_cases = len([
                c for c in self._test_cases.values()
                if c.test_set_id == test_set_id
            ])
        return count
    
    async def get_test_cases(self, test_set_id: int) -> List[EvalCase]:
        """Get all test cases for a test set."""
        return copy.deepcopy([
            c for c in self._test_cases.values()
            if c.test_set_id == test_set_id
        ])
    
    async def delete_test_case(self, case_id: int) -> bool:
        """Delete a single test case."""
        if case_id not in self._test_cases:
            return False
        case = self._test_cases.pop(case_id)
        # Update total_cases on test set
        if case.test_set_id in self._test_sets:
            self._test_sets[case.test_set_id].total_cases = len([
                c for c in self._test_cases.values()
                if c.test_set_id == case.test_set_id
            ])
        return True
    
    # ---- EvaluationTask Operations ----
    
    async def create_task(self, task: EvaluationTask) -> EvaluationTask:
        """Create a new evaluation task."""
        self._counters["task"] += 1
        task.id = self._counters["task"]
        self._tasks[task.id] = copy.deepcopy(task)
        return copy.deepcopy(task)
    
    async def get_task(self, task_id: int) -> Optional[EvaluationTask]:
        """Get a task by ID."""
        t = self._tasks.get(task_id)
        return copy.deepcopy(t) if t else None
    
    async def update_task_status(
        self,
        task_id: int,
        status: TaskStatus,
        error_message: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        """Update task status and related fields."""
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = status
        if error_message is not None:
            task.error_message = error_message
        if started_at is not None:
            task.started_at = started_at
        if completed_at is not None:
            task.completed_at = completed_at
        if duration_ms is not None:
            task.duration_ms = duration_ms
    
    async def update_task_progress(
        self,
        task_id: int,
        completed_cases: int,
        progress: float,
    ) -> None:
        """Update task progress counters."""
        task = self._tasks.get(task_id)
        if not task:
            return
        task.completed_cases = completed_cases
        task.progress = progress
    
    async def list_tasks(
        self,
        team_id: int,
        agent_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
    ) -> List[EvaluationTask]:
        """List tasks filtered by criteria."""
        results = [t for t in self._tasks.values() if t.team_id == team_id]
        if agent_id is not None:
            results = [t for t in results if t.agent_id == agent_id]
        if status is not None:
            results = [t for t in results if t.status == status]
        return copy.deepcopy(results)
    
    # ---- TestCaseResult Operations ----
    
    async def save_case_result(
        self,
        result: TestCaseResult,
    ) -> TestCaseResult:
        """Save a test case result."""
        self._counters["case_result"] += 1
        result.id = self._counters["case_result"]
        self._case_results[result.id] = copy.deepcopy(result)
        return copy.deepcopy(result)
    
    async def get_case_results(self, task_id: int) -> List[TestCaseResult]:
        """Get all results for a task."""
        return copy.deepcopy([
            r for r in self._case_results.values()
            if r.task_id == task_id
        ])
    
    # ---- EvaluationReport Operations ----
    
    async def save_report(self, report: EvaluationReport) -> EvaluationReport:
        """Save an evaluation report."""
        self._counters["report"] += 1
        report.id = self._counters["report"]
        self._reports[report.id] = copy.deepcopy(report)
        return copy.deepcopy(report)
    
    async def get_report(self, task_id: int) -> Optional[EvaluationReport]:
        """Get report for a specific task."""
        for r in self._reports.values():
            if r.task_id == task_id:
                return copy.deepcopy(r)
        return None
    
    async def get_latest_report(self, agent_id: int) -> Optional[EvaluationReport]:
        """Get the most recent report for an agent."""
        agent_reports = [r for r in self._reports.values() if r.agent_id == agent_id]
        if not agent_reports:
            return None
        return copy.deepcopy(max(agent_reports, key=lambda r: r.id))
    
    async def list_reports(
        self,
        team_id: int,
        agent_id: Optional[int] = None,
    ) -> List[EvaluationReport]:
        """List reports filtered by criteria."""
        results = [r for r in self._reports.values() if r.team_id == team_id]
        if agent_id is not None:
            results = [r for r in results if r.agent_id == agent_id]
        return copy.deepcopy(results)


# Global database instance
db = Database()
