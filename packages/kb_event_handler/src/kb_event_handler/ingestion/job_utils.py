"""Job management utilities for ingestion operations."""

import logging
from datetime import datetime, timezone
from typing import Optional

from kb_event_handler.common import (
    JobRepository,
    KnowledgeBaseRepository,
    KBJob,
    KBJobCreate,
    KnowledgeBase,
)
from kb_event_handler.exceptions import ValidationError, ResourceNotFoundError
from kb_event_handler.ingestion.schemas import IngestionJobResponse, IngestionJobStatus

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
    ) -> KBJob:
        """
        Create a new ingestion job record.
        
        Args:
            tenant_id: Tenant ID
            knowledge_base_id: Target knowledge base ID
            
        Returns:
            Created job record
            
        Raises:
            ResourceNotFoundError: If knowledge base doesn't exist
            ValidationError: If knowledge base doesn't belong to tenant
        """
        logger.info(f"Creating ingestion job for tenant: {tenant_id}, kb: {knowledge_base_id}")
        
        # Validate knowledge base exists and belongs to tenant
        await self._validate_knowledge_base_access(tenant_id, knowledge_base_id)
        
        # Create job record
        job_data = KBJobCreate(
            knowledge_base_id=knowledge_base_id,
            job_type="ingestion",
        )

        job = await self.job_repository.create_job(job_data)
        
        logger.info(f"Created ingestion job {job.id}")
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
            file_path="", # TODO: Need to add file path to job
            filename="", # TODO: Need to add filename to job
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
    
    async def check_active_jobs_for_kb(
        self,
        knowledge_base_id: int,
        tenant_id: int,
    ) -> Optional[KBJob]:
        """
        Check if there are any active jobs for a knowledge base.
        
        Args:
            knowledge_base_id: Knowledge base ID
            tenant_id: Tenant ID
            
        Returns:
            First active job if found, None otherwise
        """
        logger.info(f"Checking for active jobs for knowledge base: {knowledge_base_id}")
        
        active_jobs = await self.job_repository.get_active_jobs_for_kb(
            knowledge_base_id=knowledge_base_id,
            tenant_id=tenant_id
        )
        
        if active_jobs:
            logger.info(f"Found {len(active_jobs)} active job(s) for knowledge base {knowledge_base_id}")
            return active_jobs[0]  # Return the first active job
        
        logger.info(f"No active jobs found for knowledge base {knowledge_base_id}")
        return None 