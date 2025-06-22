"""Job management utilities for ingestion operations."""

import logging
from datetime import datetime, timezone
from typing import Optional

from ..common import (
    JobRepository,
    KnowledgeBaseRepository,
    KBJob,
    KBJobCreate,
    KnowledgeBase,
)
from ..exceptions import ValidationError, ResourceNotFoundError
from .schemas import IngestionJobResponse, IngestionJobStatus

logger = logging.getLogger(__name__)


class JobManager:
    """Manages ingestion job operations."""
    
    def __init__(
        self,
        job_repository: JobRepository,
        knowledge_base_repository: KnowledgeBaseRepository,
    ):
        self.job_repository = job_repository
        self.knowledge_base_repository = knowledge_base_repository
    
    async def create_ingestion_job(
        self,
        tenant_id: int,
        knowledge_base_id: int,
        file_path: str,
        filename: str,
        mime_type: Optional[str] = None,
    ) -> KBJob:
        """
        Create a new ingestion job record.
        
        Args:
            tenant_id: Tenant ID
            knowledge_base_id: Target knowledge base ID
            file_path: Path to file in storage
            filename: Original filename
            mime_type: File MIME type
            
        Returns:
            Created job record
            
        Raises:
            ResourceNotFoundError: If knowledge base doesn't exist
            ValidationError: If knowledge base doesn't belong to tenant
        """
        logger.info(f"Creating ingestion job for file: {filename} (tenant: {tenant_id}, kb: {knowledge_base_id})")
        
        # Validate knowledge base exists and belongs to tenant
        await self._validate_knowledge_base_access(tenant_id, knowledge_base_id)
        
        # Create job record
        job_data = KBJobCreate(
            tenant_id=tenant_id,
            knowledge_base_id=knowledge_base_id,
            job_type="ingestion",
            status="queued",
            file_path=file_path,
            filename=filename,
            mime_type=mime_type,
            created_at=datetime.now(timezone.utc),
        )

        # TODO: Need to use create_job instead of create
        job = await self.job_repository.create(job_data)
        
        logger.info(f"Created ingestion job {job.id} for file: {filename}")
        return job
    
    async def _validate_knowledge_base_access(
        self,
        tenant_id: int,
        knowledge_base_id: int,
    ) -> KnowledgeBase:
        """
        Validate that knowledge base exists and belongs to tenant.
        
        Args:
            tenant_id: Tenant ID
            knowledge_base_id: Knowledge base ID
            
        Returns:
            Knowledge base record
            
        Raises:
            ResourceNotFoundError: If knowledge base doesn't exist
            ValidationError: If knowledge base doesn't belong to tenant
        """
        # Get knowledge base
        kb = await self.knowledge_base_repository.get_by_id(knowledge_base_id)
        if not kb:
            raise ResourceNotFoundError("KnowledgeBase", knowledge_base_id)
        
        # Verify ownership
        if kb.tenant_id != tenant_id:
            raise ValidationError(
                f"Knowledge base {knowledge_base_id} does not belong to tenant {tenant_id}",
                details={
                    "knowledge_base_id": knowledge_base_id,
                    "tenant_id": tenant_id,
                    "actual_tenant_id": kb.tenant_id,
                }
            )
        
        return kb
    
    async def validate_job_access(
        self,
        job_id: int,
        tenant_id: int,
    ) -> KBJob:
        """
        Validate that user has access to job.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            
        Returns:
            Job record
            
        Raises:
            ResourceNotFoundError: If job doesn't exist
            ValidationError: If job doesn't belong to tenant
        """
        job = await self.job_repository.get_by_id(job_id)
        if not job:
            raise ResourceNotFoundError("Job", job_id)
        
        if job.tenant_id != tenant_id:
            raise ValidationError(
                f"Job {job_id} does not belong to tenant {tenant_id}",
                details={
                    "job_id": job_id,
                    "tenant_id": tenant_id,
                    "actual_tenant_id": job.tenant_id,
                }
            )
        
        return job
    
    def convert_job_to_response(self, job: KBJob) -> IngestionJobResponse:
        """
        Convert database job record to API response.
        
        Args:
            job: Database job record
            
        Returns:
            API response model
        """
        return IngestionJobResponse(
            job_id=job.id,
            status=IngestionJobStatus(job.status),
            created_at=job.created_at,
            file_path=job.file_path,
            filename=job.filename,
            knowledge_base_id=job.knowledge_base_id,
        )
    
    async def get_job_by_id(
        self,
        job_id: int,
        tenant_id: int,
    ) -> KBJob:
        """
        Get job by ID with tenant validation.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            
        Returns:
            Job record
            
        Raises:
            ResourceNotFoundError: If job doesn't exist
            ValidationError: If job doesn't belong to tenant
        """
        return await self.validate_job_access(job_id, tenant_id) 