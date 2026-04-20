"""
Test sets API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from ..models import TestSet, EvalCase, CreateTestSetRequest, AgentType
from ..service.test_set_service import TestSetService
from ..database import db

router = APIRouter(prefix="/test-sets", tags=["test-sets"])


def get_service() -> TestSetService:
    return TestSetService(db)


@router.post("", response_model=TestSet)
async def create_test_set(
    request: CreateTestSetRequest,
    service: TestSetService = Depends(get_service),
) -> TestSet:
    """Create a new test set."""
    return await service.create_test_set(
        team_id=request.team_id,
        agent_id=request.agent_id,
        name=request.name,
        agent_type=request.agent_type,
        description=request.description or "",
    )


@router.get("", response_model=List[TestSet])
async def list_test_sets(
    team_id: int,
    agent_id: Optional[int] = None,
    agent_type: Optional[AgentType] = None,
    service: TestSetService = Depends(get_service),
) -> List[TestSet]:
    """List test sets with optional filters."""
    return await service.list_test_sets(team_id, agent_id, agent_type)


@router.get("/{test_set_id}", response_model=TestSet)
async def get_test_set(
    test_set_id: int,
    service: TestSetService = Depends(get_service),
) -> TestSet:
    """Get a test set by ID."""
    test_set = await service.get_test_set(test_set_id)
    if not test_set:
        raise HTTPException(status_code=404, detail="Test set not found")
    return test_set


@router.put("/{test_set_id}", response_model=TestSet)
async def update_test_set(
    test_set_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    service: TestSetService = Depends(get_service),
) -> TestSet:
    """Update a test set."""
    updates = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    
    test_set = await service.update_test_set(test_set_id, **updates)
    if not test_set:
        raise HTTPException(status_code=404, detail="Test set not found")
    return test_set


@router.delete("/{test_set_id}")
async def delete_test_set(
    test_set_id: int,
    service: TestSetService = Depends(get_service),
) -> dict:
    """Delete a test set."""
    deleted = await service.delete_test_set(test_set_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Test set not found")
    return {"status": "deleted", "test_set_id": test_set_id}


@router.post("/{test_set_id}/cases/batch")
async def add_test_cases_batch(
    test_set_id: int,
    cases: List[EvalCase],
    service: TestSetService = Depends(get_service),
) -> dict:
    """Add multiple test cases to a test set."""
    test_set = await service.get_test_set(test_set_id)
    if not test_set:
        raise HTTPException(status_code=404, detail="Test set not found")
    
    count = await service.add_test_cases(test_set_id, cases)
    return {"added": count, "test_set_id": test_set_id}


@router.get("/{test_set_id}/cases", response_model=List[EvalCase])
async def get_test_cases(
    test_set_id: int,
    service: TestSetService = Depends(get_service),
) -> List[EvalCase]:
    """Get all test cases for a test set."""
    return await service.get_test_cases(test_set_id)


@router.delete("/cases/{case_id}")
async def delete_test_case(
    case_id: int,
    service: TestSetService = Depends(get_service),
) -> dict:
    """Delete a single test case."""
    deleted = await service.delete_test_case(case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Test case not found")
    return {"status": "deleted", "case_id": case_id}
