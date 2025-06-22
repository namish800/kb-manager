"""Health check router."""

import logging
from datetime import datetime

from fastapi import APIRouter, status

from ..config import settings
from ..database import health_check_database
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
    
    # Check database health
    db_health = await health_check_database()
    
    # TODO: Add other dependency health checks in future phases
    dependencies = {
        "supabase": db_health.get("status", "unknown"),
        "openai": "unknown",    # Will implement in Phase 4
        "pinecone": "unknown",  # Will implement in Phase 4
    }
    
    # Determine overall health status
    overall_status = "healthy"
    if any(status != "connected" for status in dependencies.values() if status != "unknown"):
        overall_status = "unhealthy"
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="0.1.0",  # TODO: Extract from package metadata
        environment=settings.environment,
        dependencies=dependencies,
    ) 