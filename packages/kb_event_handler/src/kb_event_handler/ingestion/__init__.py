"""Ingestion module for file processing operations."""

from .schemas import (
    IngestionRequest,
    IngestionJobResponse,
    IngestionResult,
    JobStatusResponse,
    IngestionJobStatus,
    BatchIngestionRequest,
    BatchIngestionResponse,
)
from .config_mapper import IngestionConfigMapper
from .ingestion_service import IngestionService
from .background_processor import BackgroundJobProcessor

# TODO: Import router when created in Phase 5
# from .router import router

__all__ = [
    # Schemas
    "IngestionRequest",
    "IngestionJobResponse", 
    "IngestionResult",
    "JobStatusResponse",
    "IngestionJobStatus",
    "BatchIngestionRequest",
    "BatchIngestionResponse",
    # Services
    "IngestionConfigMapper",
    "IngestionService",
    "BackgroundJobProcessor",
    # TODO: Add router in Phase 5
    # "router",
] 