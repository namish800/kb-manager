"""Health check router."""

import logging
from datetime import datetime

from fastapi import APIRouter, status

from ..config import settings
from .schemas import HealthStatus


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Get the health status of the API and its dependencies",
)
async def health_check() -> HealthStatus:
    """Perform health check and return system status."""
    logger.info("Health check requested")
    
    # TODO: In future phases, add actual dependency health checks
    # For now, we'll just return basic status
    dependencies = {
        "supabase": "unknown",  # Will implement in Phase 2
        "openai": "unknown",    # Will implement in Phase 4
        "pinecone": "unknown",  # Will implement in Phase 4
    }
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="0.1.0",  # TODO: Extract from package metadata
        environment=settings.environment,
        dependencies=dependencies,
    ) 