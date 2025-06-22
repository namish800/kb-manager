"""Pydantic schemas for health check endpoints."""

from datetime import datetime
from typing import Dict, Literal

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Health check response model."""

    status: Literal["healthy", "unhealthy"] = Field(
        description="Overall health status"
    )
    timestamp: datetime = Field(
        description="Timestamp when health check was performed"
    )
    version: str = Field(
        description="Application version"
    )
    environment: str = Field(
        description="Current environment (development, staging, production)"
    )
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of external dependencies"
    ) 