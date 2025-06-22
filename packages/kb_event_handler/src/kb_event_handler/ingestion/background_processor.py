"""Background job processor for ingestion tasks."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from kb_event_handler.ingestion.ingestion_service import IngestionService
from kb_event_handler.ingestion.schemas import IngestionResult
from kb_event_handler.common import (
    TempFileManager,
    FileValidationService,
    JobRepository,
    FileRepository,
    KBJob,
    KBJobUpdate,
    KBFile,
)
from kb_event_handler.exceptions import KBEventHandlerException

logger = logging.getLogger(__name__)


class BackgroundJobProcessor:
    """Processes ingestion jobs in the background."""
    
    def __init__(
        self,
        ingestion_service: IngestionService,
        temp_file_manager: TempFileManager,
        file_validation_service: FileValidationService,
        job_repository: JobRepository,
        file_repository: FileRepository,
    ):
        self.ingestion_service = ingestion_service
        self.temp_file_manager = temp_file_manager
        self.file_validation_service = file_validation_service
        self.job_repository = job_repository
        self.file_repository = file_repository
        
        # Track running jobs to prevent duplicates
        self._running_jobs: Dict[int, asyncio.Task] = {}
        self._job_lock = asyncio.Lock()
    
    async def process_ingestion_job(
        self,
        job_id: int,
        file_path: str,
        filename: str,
        tenant_id: int,
        knowledge_base_id: int,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Process an ingestion job in the background.
        
        Args:
            job_id: Database job ID
            file_path: Path to file in storage
            filename: Original filename
            tenant_id: Tenant ID
            knowledge_base_id: Target knowledge base ID
            chunk_size: Override chunk size
            chunk_overlap: Override chunk overlap
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
                    job_id, file_path, filename, tenant_id, 
                    knowledge_base_id, chunk_size, chunk_overlap, metadata
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
        file_path: str,
        filename: str,
        tenant_id: int,
        knowledge_base_id: int,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Internal job processing logic."""
        
        logger.info(f"Starting background processing for job {job_id}: {filename}")
        
        # Update job status to processing
        await self._update_job_status(
            job_id, 
            "processing", 
            started_at=datetime.now(timezone.utc)
        )
        
        try:
            # Step 1: Validate file exists and is processable
            logger.info(f"Validating file for job {job_id}: {file_path}")
            
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
            
            # Step 2: Download file to temporary location
            logger.info(f"Downloading file for job {job_id}: {file_path}")
            
            async with self.temp_file_manager.temp_file_context(file_path, filename) as temp_path:
                
                # Step 3: Additional validation on downloaded file
                if not await self.ingestion_service.validate_file_for_ingestion(temp_path, filename):
                    raise KBEventHandlerException(
                        message=f"File cannot be processed by ingestion pipeline: {filename}",
                        error_code="INGESTION_VALIDATION_FAILED",
                        status_code=400
                    )
                
                # Step 4: Process file through ingestion pipeline
                logger.info(f"Processing file through ingestion pipeline for job {job_id}")
                
                ingestion_result = await self.ingestion_service.ingest_file(
                    temp_file_path=temp_path,
                    filename=filename,
                    tenant_id=tenant_id,
                    knowledge_base_id=knowledge_base_id,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    metadata=metadata
                )
                
                # Step 5: Update job with results
                await self._complete_job(job_id, ingestion_result)
                
                # Temp file automatically cleaned up by context manager
            
            logger.info(f"Successfully completed job {job_id}: {filename}")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}")
            await self._fail_job(job_id, str(e))
    
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
            update_data = {"status": status}
            
            if started_at:
                update_data["started_at"] = started_at
            if completed_at:
                update_data["completed_at"] = completed_at
            if error_message:
                update_data["error_message"] = error_message
            if result_metadata:
                update_data["result_metadata"] = result_metadata
            
            job_update = KBJobUpdate(**update_data)
            await self.job_repository.update(job_id, job_update)
            
            logger.debug(f"Updated job {job_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update job {job_id} status: {e}")
            # Don't raise here to avoid masking the original error
    
    async def _complete_job(self, job_id: int, result: IngestionResult) -> None:
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
    
    async def _fail_job(self, job_id: int, error_message: str) -> None:
        """Mark job as failed with error message."""
        await self._update_job_status(
            job_id=job_id,
            status="failed",
            completed_at=datetime.now(timezone.utc),
            error_message=error_message
        )
    
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