from fastapi import APIRouter

from ..config import settings


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Health check endpoint."""

    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }

