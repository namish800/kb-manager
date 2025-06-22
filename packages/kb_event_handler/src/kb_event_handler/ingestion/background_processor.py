"""Background job processor for ingestion tasks."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from kb_event_handler.common.file_validation import FileValidationResult
from kb_event_handler.ingestion.interfaces.ingestion_service import IIngestionService
from kb_event_handler.ingestion.schemas import IngestionResult
from kb_event_handler.common import (
    FileValidationService,
    JobRepository,
    FileRepository,
    KnowledgeBaseRepository,
    KBJobUpdate,
    KnowledgeBaseUpdate,
)
from kb_event_handler.exceptions import KBEventHandlerException

logger = logging.getLogger(__name__)


class BackgroundJobProcessor:
    """Processes ingestion jobs in the background."""
    
    def __init__(
        self,
        document_ingestion_service: IIngestionService,
        website_ingestion_service: IIngestionService,
        file_validation_service: FileValidationService,
        job_repository: JobRepository,
        file_repository: FileRepository,
        knowledge_base_repository: KnowledgeBaseRepository,
    ):
        self.document_ingestion_service = document_ingestion_service
        self.website_ingestion_service = website_ingestion_service
        self.file_validation_service = file_validation_service
        self.job_repository = job_repository
        self.file_repository = file_repository
        self.knowledge_base_repository = knowledge_base_repository
        
        # Track running jobs to prevent duplicates
        self._running_jobs: Dict[int, asyncio.Task] = {}
        self._job_lock = asyncio.Lock() 
    
    async def process_ingestion_job(
        self,
        job_id: int,
        resource_type: str,
        tenant_id: int,
        knowledge_base_id: int,
        urls: Optional[List[str]] = None,
        file_path: Optional[str] = None,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Process an ingestion job in the background.
        
        Args:
            job_id: Database job ID
            resource_type: Type of resource to ingest (document, website)
            tenant_id: Tenant ID
            knowledge_base_id: Target knowledge base ID
            urls: List of URLs to ingest
            file_path: Path to file in storage
            filename: Original filename
            metadata: Additional metadata
        """
        # Check if job is already running
        async with self._job_lock:
            if job_id in self._running_jobs:
                logger.warning(f"Job {job_id} is already running, skipping")
                return
            
            # Create task for this job
            task = asyncio.create_task(
                self._process_job_internal(
                    job_id=job_id,
                    resource_type=resource_type,
                    tenant_id=tenant_id,
                    knowledge_base_id=knowledge_base_id,
                    urls=urls,
                    file_path=file_path,
                    filename=filename,
                    metadata=metadata
                )
            )
            self._running_jobs[job_id] = task
        
        try:
            await task
        finally:
            # Clean up completed task
            async with self._job_lock:
                self._running_jobs.pop(job_id, None)
    
    async def _process_job_internal(
        self,
        job_id: int,
        resource_type: str,
        tenant_id: int,
        knowledge_base_id: int,
        urls: Optional[List[str]] = None,
        file_path: Optional[str] = None,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Internal job processing logic."""
        
        logger.info(f"Starting background processing for job {job_id}: filename={filename}, file_path={file_path}, resource_type={resource_type}, urls={urls}")
        
        # Update job status to processing
        await self._update_job_status(
            job_id, 
            "processing", 
            started_at=datetime.now(timezone.utc)
        )
        
        # Update knowledge base status to processing
        await self._update_knowledge_base_status(knowledge_base_id, tenant_id, "processing")
        
        try:
            # Step 1: Validate file exists and is processable
            
            if resource_type == "document":
                logger.info(f"Validating file for job {job_id}: filename={filename}, file_path={file_path}")

                validation_result = await self.file_validation_service.validate_file(
                    filename=filename,
                    file_path=file_path,
                    check_existence=True
                )
                if not validation_result.is_valid:
                    raise KBEventHandlerException(
                        message=f"File validation failed: {', '.join(validation_result.errors)}",
                        error_code="FILE_VALIDATION_FAILED",
                        status_code=400
                    )
                
                # validate file size
                validation_result = await self.file_validation_service.validate_file_size_only(file_path)
                if not validation_result.is_valid:
                    raise KBEventHandlerException(
                        message=f"File size validation failed: {', '.join(validation_result.errors)}",
                        error_code="FILE_SIZE_VALIDATION_FAILED",
                        status_code=400
                    )
                
                # Call the document ingestion service
                ingestion_result = await self.document_ingestion_service.ingest_resource(
                    job_id=job_id,
                    resource_type="document",
                    tenant_id=tenant_id,
                    knowledge_base_id=knowledge_base_id,
                    file_path=file_path,
                    filename=filename,
                    metadata=metadata
                )

            elif resource_type == "website":
                # verify if the urls are valid
                validation_result = FileValidationResult(is_valid=True)
                ingestion_result = await self.website_ingestion_service.ingest_resource(
                    job_id=job_id,
                    resource_type="website",
                    tenant_id=tenant_id,
                    knowledge_base_id=knowledge_base_id,
                    urls=urls,
                    metadata=metadata
                )

            await self._complete_job(job_id, knowledge_base_id, tenant_id, ingestion_result)
            
            logger.info(f"Successfully completed job {job_id}: {filename}")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            await self._fail_job(job_id, knowledge_base_id, tenant_id, str(e))
    
    async def _update_job_status(
        self,
        job_id: int,
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        result_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update job status in database."""
        try:
            job_update = KBJobUpdate(
                status=status,
                started_at=started_at.isoformat() if started_at else None,
                completed_at=completed_at.isoformat() if completed_at else None,
                error_message=error_message,
            )
            await self.job_repository.update_job(job_id, job_update)
            
            logger.debug(f"Updated job {job_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update job {job_id} status: {e}")
            # Don't raise here to avoid masking the original error
    
    async def _update_knowledge_base_status(
        self,
        knowledge_base_id: int,
        tenant_id: int,
        status: str
    ) -> None:
        """Update knowledge base status."""
        try:
            kb_update = KnowledgeBaseUpdate(status=status)
            await self.knowledge_base_repository.update_kb(knowledge_base_id, kb_update, tenant_id)
            
            logger.debug(f"Updated knowledge base {knowledge_base_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update knowledge base {knowledge_base_id} status: {e}")
            # Don't raise here to avoid masking the original error
    
    async def _complete_job(self, job_id: int, knowledge_base_id: int, tenant_id: int, result: IngestionResult) -> None:
        """Mark job as completed with results."""
        status = "completed" if result.success else "failed"
        
        await self._update_job_status(
            job_id=job_id,
            status=status,
            completed_at=datetime.now(timezone.utc),
            error_message=result.error_message if not result.success else None,
            result_metadata={
                "success": result.success,
                "node_count": result.node_count,
                "processing_time_seconds": result.processing_time_seconds,
                **result.metadata
            }
        )
        
        # Update knowledge base status
        kb_status = "completed" if result.success else "failed"
        await self._update_knowledge_base_status(knowledge_base_id, tenant_id, kb_status)
    
    async def _fail_job(self, job_id: int, knowledge_base_id: int, tenant_id: int, error_message: str) -> None:
        """Mark job as failed with error message."""
        await self._update_job_status(
            job_id=job_id,
            status="failed",
            completed_at=datetime.now(timezone.utc),
            error_message=error_message
        )
        
        # Update knowledge base status to failed
        await self._update_knowledge_base_status(knowledge_base_id, tenant_id, "failed")
    
    async def get_running_jobs(self) -> Dict[int, str]:
        """
        Get currently running jobs.
        
        Returns:
            Dict mapping job_id to task status
        """
        async with self._job_lock:
            return {
                job_id: "running" if not task.done() else "done"
                for job_id, task in self._running_jobs.items()
            }
    
    async def cancel_job(self, job_id: int) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if job was cancelled, False if not running
        """
        async with self._job_lock:
            if job_id not in self._running_jobs:
                return False
            
            task = self._running_jobs[job_id]
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled job {job_id}")
                
                # Update job status
                await self._update_job_status(
                    job_id=job_id,
                    status="failed",
                    completed_at=datetime.now(timezone.utc),
                    error_message="Job cancelled"
                )
                
                return True
            
            return False
    
    async def cleanup_completed_tasks(self) -> int:
        """
        Clean up completed tasks from memory.
        
        Returns:
            Number of tasks cleaned up
        """
        cleanup_count = 0
        
        async with self._job_lock:
            completed_jobs = [
                job_id for job_id, task in self._running_jobs.items()
                if task.done()
            ]
            
            for job_id in completed_jobs:
                self._running_jobs.pop(job_id, None)
                cleanup_count += 1
        
        if cleanup_count > 0:
            logger.debug(f"Cleaned up {cleanup_count} completed job tasks")
        
        return cleanup_count 