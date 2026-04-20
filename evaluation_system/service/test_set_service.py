"""
Test set service for managing evaluation test sets.
"""

from typing import List, Optional
from datetime import datetime

from ..database import Database
from ..models import TestSet, EvalCase, AgentType


class TestSetService:
    """Service for managing test sets and test cases."""
    
    def __init__(self, db: Database) -> None:
        self.db = db
    
    async def create_test_set(
        self,
        team_id: int,
        agent_id: int,
        name: str,
        agent_type: AgentType,
        description: str = "",
    ) -> TestSet:
        """Create a new test set."""
        test_set = TestSet(
            team_id=team_id,
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
            description=description,
            total_cases=0,
            version="v1.0",
        )
        return await self.db.create_test_set(test_set)
    
    async def get_test_set(self, test_set_id: int) -> Optional[TestSet]:
        """Get a test set by ID."""
        return await self.db.get_test_set(test_set_id)
    
    async def list_test_sets(
        self,
        team_id: int,
        agent_id: Optional[int] = None,
        agent_type: Optional[AgentType] = None,
    ) -> List[TestSet]:
        """List test sets with optional filters."""
        return await self.db.list_test_sets(team_id, agent_id, agent_type)
    
    async def update_test_set(
        self,
        test_set_id: int,
        **kwargs,
    ) -> Optional[TestSet]:
        """Update a test set."""
        return await self.db.update_test_set(test_set_id, **kwargs)
    
    async def delete_test_set(self, test_set_id: int) -> bool:
        """Delete a test set and its cases."""
        return await self.db.delete_test_set(test_set_id)
    
    async def add_test_cases(
        self,
        test_set_id: int,
        cases: List[EvalCase],
    ) -> int:
        """Add test cases to a test set. Returns count added."""
        return await self.db.add_test_cases(test_set_id, cases)
    
    async def get_test_cases(self, test_set_id: int) -> List[EvalCase]:
        """Get all test cases for a test set."""
        return await self.db.get_test_cases(test_set_id)
    
    async def delete_test_case(self, case_id: int) -> bool:
        """Delete a single test case."""
        return await self.db.delete_test_case(case_id)
