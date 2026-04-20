"""
API router aggregation.
"""

from fastapi import APIRouter

from . import test_sets, tasks, reports, config_api

router = APIRouter(prefix="/api/v1/evaluation")

router.include_router(test_sets.router)
router.include_router(tasks.router)
router.include_router(reports.router)
router.include_router(config_api.router)
