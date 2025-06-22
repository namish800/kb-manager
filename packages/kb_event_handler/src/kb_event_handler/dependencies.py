"""Global dependencies for the FastAPI application."""

import logging
import uuid
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import HTTPBearer
from kb_event_handler.common.repositories import FileRepository, JobRepository

from .config import settings
from .exceptions import AuthenticationError, ValidationError
# Import database repositories
from .database import (
    file_repository,
    job_repository, 
    knowledge_base_repository,
    tenant_repository,
    supabase_client,
)
# Import file handling services
from .common import (
    StorageClient,
    FileValidationService,
    TempFileManager,
)
# Import ingestion services
from .ingestion.ingestion_service import IngestionService
from .ingestion.background_processor import BackgroundJobProcessor


logger = logging.getLogger(__name__)

# Security scheme for OpenAPI docs
security = HTTPBearer(auto_error=False)


async def get_correlation_id(request: Request) -> str:
    """Get or generate correlation ID for request tracking."""
    correlation_id = getattr(request.state, "correlation_id", None)
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
    return correlation_id


async def authenticate_api_key(
    x_api_key: Annotated[str, Header(alias="X-API-Key")]
) -> str:
    """Validate the API key from request headers."""
    if not x_api_key:
        raise AuthenticationError("API key is required")
    
    if x_api_key != settings.api_secret_key:
        raise AuthenticationError("Invalid API key")
    
    return x_api_key


async def get_tenant_id(
    x_tenant_id: Annotated[str, Header(alias="X-Tenant-ID")]
) -> int:
    """Extract and validate tenant ID from request headers."""
    if not x_tenant_id:
        raise ValidationError("Tenant ID is required in X-Tenant-ID header")
    
    try:
        tenant_id = int(x_tenant_id)
        if tenant_id <= 0:
            raise ValueError("Tenant ID must be positive")
        return tenant_id
    except (ValueError, TypeError) as e:
        raise ValidationError(
            f"Invalid tenant ID format: {x_tenant_id}",
            details={"provided_value": x_tenant_id, "error": str(e)}
        )


async def validate_tenant_access(
    tenant_id: Annotated[int, Depends(get_tenant_id)],
    _: Annotated[str, Depends(authenticate_api_key)],  # Ensure API key is valid
):
    """Validate that the tenant exists and user has access."""
    # Validate tenant exists in database
    await tenant_repository.validate_tenant_exists(tenant_id)
    return tenant_id


# Database dependencies
async def get_tenant_repository():
    """Get tenant repository instance."""
    return tenant_repository


async def get_job_repository():
    """Get job repository instance."""
    return job_repository


async def get_knowledge_base_repository():
    """Get knowledge base repository instance."""
    return knowledge_base_repository


async def get_file_repository():
    """Get file repository instance."""
    return file_repository


# File handling service dependencies
async def get_storage_client():
    """Get storage client instance."""
    return StorageClient(supabase_client.client, settings)


async def get_file_validation_service(
    storage_client: Annotated[StorageClient, Depends(get_storage_client)]
):
    """Get file validation service instance."""
    return FileValidationService(storage_client)


async def get_temp_file_manager(
    storage_client: Annotated[StorageClient, Depends(get_storage_client)]
):
    """Get temporary file manager instance.""" 
    return TempFileManager(storage_client, settings.temp_dir)


# Ingestion service dependencies
async def get_ingestion_service():
    """Get ingestion service instance."""
    return IngestionService(settings)


async def get_background_job_processor(
    ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)],
    temp_file_manager: Annotated[TempFileManager, Depends(get_temp_file_manager)],
    file_validation_service: Annotated[FileValidationService, Depends(get_file_validation_service)],
    job_repository: Annotated[JobRepository, Depends(get_job_repository)],
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
):
    """Get background job processor instance."""
    return BackgroundJobProcessor(
        ingestion_service=ingestion_service,
        temp_file_manager=temp_file_manager,
        file_validation_service=file_validation_service,
        job_repository=job_repository,
        file_repository=file_repository,
    )


# Dependency aliases for common use
CorrelationIdDep = Annotated[str, Depends(get_correlation_id)]
ApiKeyDep = Annotated[str, Depends(authenticate_api_key)]
TenantIdDep = Annotated[int, Depends(get_tenant_id)]
ValidatedTenantIdDep = Annotated[int, Depends(validate_tenant_access)]

# Repository dependencies  
TenantRepoDep = Annotated[tenant_repository.__class__, Depends(get_tenant_repository)]
JobRepoDep = Annotated[job_repository.__class__, Depends(get_job_repository)]
KnowledgeBaseRepoDep = Annotated[knowledge_base_repository.__class__, Depends(get_knowledge_base_repository)]
FileRepoDep = Annotated[file_repository.__class__, Depends(get_file_repository)]

# File service dependencies
StorageClientDep = Annotated[StorageClient, Depends(get_storage_client)]
FileValidationServiceDep = Annotated[FileValidationService, Depends(get_file_validation_service)]
TempFileManagerDep = Annotated[TempFileManager, Depends(get_temp_file_manager)]

# Ingestion service dependencies
IngestionServiceDep = Annotated[IngestionService, Depends(get_ingestion_service)]
BackgroundJobProcessorDep = Annotated[BackgroundJobProcessor, Depends(get_background_job_processor)] 