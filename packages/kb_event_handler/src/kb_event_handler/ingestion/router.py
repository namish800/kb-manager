"""Ingestion API router."""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse

from kb_event_handler.ingestion.schemas import IngestionRequest, IngestionJobResponse
from kb_event_handler.ingestion.job_utils import JobManager
from kb_event_handler.dependencies import (
    ValidatedTenantIdDep,
    CorrelationIdDep,
    JobRepoDep,
    KnowledgeBaseRepoDep,
    FileValidationServiceDep,
    BackgroundJobProcessorDep,
)
from kb_event_handler.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["ingestion"],
    responses={
        401: {"description": "Authentication failed"},
        400: {"description": "Validation error"},
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"},
    },
)


async def get_job_manager(
    job_repo: JobRepoDep,
    kb_repo: KnowledgeBaseRepoDep,
) -> JobManager:
    """Get job manager instance."""
    return JobManager(job_repo, kb_repo)


JobManagerDep = Annotated[JobManager, Depends(get_job_manager)]


@router.post(
    "/ingest",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start file ingestion",
    description="Start processing a file for ingestion into a knowledge base. "
                "The file must already be uploaded to storage. Returns a job ID for tracking progress. "
                "If the knowledge base is already being processed, returns the existing job instead of creating a new one.",
    responses={
        202: {
            "description": "Ingestion job created successfully or existing job returned",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": 789,
                        "status": "queued",
                        "created_at": "2024-01-15T10:30:00Z",
                        "file_path": "tenant_123/kb_456/documents/report.pdf",
                        "filename": "quarterly_report.pdf",
                        "knowledge_base_id": 456
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": "VALIDATION_ERROR",
                        "message": "File validation failed: Unsupported file type",
                        "correlation_id": "abc123",
                        "details": {
                            "filename": "image.jpg",
                            "supported_types": ["pdf", "docx", "pptx", "md"]
                        }
                    }
                }
            }
        },
        404: {
            "description": "Knowledge base not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "RESOURCE_NOT_FOUND",
                        "message": "KnowledgeBase with ID 456 not found",
                        "correlation_id": "abc123"
                    }
                }
            }
        },
    },
)
async def ingest_file(
    request: IngestionRequest,
    background_tasks: BackgroundTasks,
    tenant_id: ValidatedTenantIdDep,
    correlation_id: CorrelationIdDep,
    job_manager: JobManagerDep,
    file_validation: FileValidationServiceDep,
    processor: BackgroundJobProcessorDep,
) -> IngestionJobResponse:
    """
    Start file ingestion job.
    
    This endpoint creates a background job to process a file for ingestion into
    a knowledge base. The file must already be uploaded to storage.
    
    **Duplicate Prevention:**
    If the knowledge base is already being processed by another job, this endpoint
    will return the existing job instead of creating a new one. This prevents
    multiple simultaneous ingestion jobs on the same knowledge base.
    
    **Process:**
    1. Validates the knowledge base exists and belongs to the tenant
    2. Checks if the knowledge base is already being processed
    3. If already processing, returns the existing job details
    4. If not processing, validates the file exists and is supported
    5. Creates a job record with status "queued"
    6. Starts background processing
    7. Returns job ID for status tracking
    
    **File Requirements:**
    - Must be uploaded to storage first
    - Supported formats: PDF, Word (DOC/DOCX), PowerPoint (PPT/PPTX), Markdown (MD)
    - Maximum size: 25MB
    
    **Background Processing:**
    The actual ingestion happens asynchronously. Use the returned job_id
    to check processing status via the job status endpoint.
    """
    logger.info(
        f"Ingestion request received for file: {request.filename} "
        f"(tenant: {tenant_id}, kb: {request.knowledge_base_id})",
        extra={"correlation_id": correlation_id}
    )
    
    try:
        # Step 1: Validate if the resource is atleast a file or a website
        logger.info(f"Validating resource: {request.file_path} and {request.urls}")
        
        if request.file_path is None and request.urls is None:
            logger.error(f"Either file_path or urls must be provided")
            raise ValidationError(
                "Either file_path or urls must be provided",
                details={
                    "file_path": request.file_path,
                    "urls": request.urls,
                }
            )
        
        # Step 2: Check if knowledge base is already being processed
        logger.info(f"Checking if knowledge base {request.knowledge_base_id} is already being processed")
        
        existing_job = await job_manager.check_active_jobs_for_kb(
            knowledge_base_id=request.knowledge_base_id,
            tenant_id=tenant_id
        )
        
        if existing_job:
            logger.info(
                f"Knowledge base {request.knowledge_base_id} is already being processed by job {existing_job.id}. "
                f"Returning existing job instead of creating new one.",
                extra={"correlation_id": correlation_id}
            )
            
            # Return the existing job response
            response = job_manager.convert_job_to_response(existing_job)
            return response
        
        # Step 3: Create job record (this also validates KB ownership)
        logger.info(f"Creating job record for knowledge base: {request.knowledge_base_id}")
        
        job = await job_manager.create_ingestion_job(
            tenant_id=tenant_id,
            knowledge_base_id=request.knowledge_base_id,
        )
        
        # Step 4: Queue background processing task
        logger.info(f"Queueing background task for job {job.id}")
        
        background_tasks.add_task(
            processor.process_ingestion_job,
            job_id=job.id,
            urls=request.urls, # this is optional
            resource_type=request.resource_type,
            file_path=request.file_path, # this is optional
            filename=request.filename, # this is optional
            tenant_id=tenant_id,
            knowledge_base_id=request.knowledge_base_id,
            metadata={
                "correlation_id": correlation_id,
                "mime_type": request.mime_type, # this is optional
            }
        )
        
        # Step 5: Return job response
        response = job_manager.convert_job_to_response(job)
        
        logger.info(
            f"Ingestion job {job.id} created successfully for file: {request.filename}",
            extra={"correlation_id": correlation_id}
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Failed to create ingestion job for file: {request.filename}. Error: {str(e)}",
            extra={"correlation_id": correlation_id}
        )
        raise  # Re-raise to let FastAPI exception handlers deal with it 