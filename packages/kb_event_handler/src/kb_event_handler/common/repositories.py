"""Repository classes for database operations following the Repository pattern."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from supabase import Client

from kb_event_handler.common.models import (
    KBFile,
    KBJob,
    KBJobCreate, 
    KBJobUpdate,
    KnowledgeBase,
    KnowledgeBaseUpdate,
    Tenant,
)
from kb_event_handler.common.supabase_client import supabase_client
from kb_event_handler.exceptions import ResourceNotFoundError, TenantNotFoundError


logger = logging.getLogger(__name__)

# Generic type for repository models
T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, table_name: str):
        """Initialize repository with table name."""
        self.table_name = table_name
        self._client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get Supabase client instance."""
        return supabase_client.client
    
    @abstractmethod
    def _map_to_model(self, data: Dict[str, Any]) -> T:
        """Map database row to Pydantic model."""
        pass
    
    async def get_by_id(self, id: Union[int, str], tenant_id: Optional[int] = None) -> Optional[T]:
        """Get entity by ID with optional tenant scoping."""
        try:
            query = self.client.from_(self.table_name).select("*").eq("id", id)
            
            # Add tenant scoping if provided and table has tenant_id column
            if tenant_id is not None and self.table_name != "tenants":
                query = query.eq("tenant_id", tenant_id)
            
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                return self._map_to_model(result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting {self.table_name} by ID {id}: {e}")
            raise
    
    async def get_all(self, tenant_id: Optional[int] = None, limit: int = 100) -> List[T]:
        """Get all entities with optional tenant scoping."""
        try:
            query = self.client.from_(self.table_name).select("*").limit(limit)
            
            # Add tenant scoping if provided and table has tenant_id column
            if tenant_id is not None and self.table_name != "tenants":
                query = query.eq("tenant_id", tenant_id)
            
            result = query.execute()
            
            return [self._map_to_model(row) for row in result.data or []]
            
        except Exception as e:
            logger.error(f"Error getting all {self.table_name}: {e}")
            raise
    
    async def create(self, data: Dict[str, Any], tenant_id: Optional[int] = None) -> T:
        """Create new entity."""
        try:
            # Convert datetime objects to ISO strings for JSON serialization
            serialized_data = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    serialized_data[key] = value.isoformat()
                else:
                    serialized_data[key] = value
            
            # Add tenant_id if provided and table supports it
            if tenant_id is not None and self.table_name != "tenants":
                serialized_data["tenant_id"] = tenant_id
            
            # Add timestamps
            now = datetime.now(timezone.utc)
            serialized_data["created_at"] = now.isoformat()
            serialized_data["updated_at"] = now.isoformat()
            
            result = self.client.from_(self.table_name).insert(serialized_data).execute()
            
            if result.data and len(result.data) > 0:
                return self._map_to_model(result.data[0])
            else:
                raise Exception("No data returned from insert operation")
                
        except Exception as e:
            logger.error(f"Error creating {self.table_name}: {e}")
            raise
    
    async def update(self, id: Union[int, str], data: Dict[str, Any], tenant_id: Optional[int] = None) -> Optional[T]:
        """Update entity by ID."""
        try:
            # Convert datetime objects to ISO strings for JSON serialization
            serialized_data = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    serialized_data[key] = value.isoformat()
                else:
                    serialized_data[key] = value
            
            # Add updated timestamp
            serialized_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            query = self.client.from_(self.table_name).update(serialized_data).eq("id", id)
            
            # Add tenant scoping if provided
            if tenant_id is not None and self.table_name != "tenants":
                query = query.eq("tenant_id", tenant_id)
            
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                return self._map_to_model(result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error updating {self.table_name} with ID {id}: {e}")
            raise
    
    async def delete(self, id: Union[int, str], tenant_id: Optional[int] = None) -> bool:
        """Delete entity by ID."""
        try:
            query = self.client.from_(self.table_name).delete().eq("id", id)
            
            # Add tenant scoping if provided
            if tenant_id is not None and self.table_name != "tenants":
                query = query.eq("tenant_id", tenant_id)
            
            result = query.execute()
            
            return result.data is not None and len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error deleting {self.table_name} with ID {id}: {e}")
            raise


class TenantRepository(BaseRepository[Tenant]):
    """Repository for tenant operations."""
    
    def __init__(self):
        super().__init__("tenants")
    
    def _map_to_model(self, data: Dict[str, Any]) -> Tenant:
        """Map database row to Tenant model."""
        return Tenant(**data)
    
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        try:
            result = self.client.from_(self.table_name).select("*").eq("slug", slug).execute()
            
            if result.data and len(result.data) > 0:
                return self._map_to_model(result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting tenant by slug {slug}: {e}")
            raise
    
    async def validate_tenant_exists(self, tenant_id: int) -> bool:
        """Validate that a tenant exists."""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(tenant_id)
        return True


class JobRepository(BaseRepository[KBJob]):
    """Repository for job operations."""
    
    def __init__(self):
        super().__init__("kb_jobs")
    
    def _map_to_model(self, data: Dict[str, Any]) -> KBJob:
        """Map database row to KBJob model."""
        return KBJob(**data)
    
    async def create_job(self, job_data: KBJobCreate) -> KBJob:
        """Create a new job."""
        data = job_data.model_dump()
        return await self.create(data, None)
    
    async def update_job(self, job_id: int, job_update: KBJobUpdate) -> Optional[KBJob]:
        """Update job status and progress."""
        # Remove None values from update data
        data = {k: v for k, v in job_update.model_dump().items() if v is not None}
        
        if not data:
            # No updates to make
            return await self.get_by_id(job_id)
        
        return await self.update(job_id, data)
    
    async def get_jobs_by_kb(self, knowledge_base_id: int, tenant_id: int) -> List[KBJob]:
        """Get all jobs for a specific knowledge base."""
        try:
            result = (
                self.client.from_(self.table_name)
                .select("*")
                .eq("knowledge_base_id", knowledge_base_id)
                .execute()
            )
            
            return [self._map_to_model(row) for row in result.data or []]
            
        except Exception as e:
            logger.error(f"Error getting jobs for KB {knowledge_base_id}: {e}")
            raise
    
    async def get_active_jobs(self, tenant_id: int) -> List[KBJob]:
        """Get all active (queued or processing) jobs for a tenant."""
        try:
            result = (
                self.client.from_(self.table_name)
                .select("*")
                .in_("status", ["queued", "processing"])
                .execute()
            )
            
            return [self._map_to_model(row) for row in result.data or []]
            
        except Exception as e:
            logger.error(f"Error getting active jobs for tenant {tenant_id}: {e}")
            raise


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    """Repository for knowledge base operations."""
    
    def __init__(self):
        super().__init__("knowledge_bases")
    
    def _map_to_model(self, data: Dict[str, Any]) -> KnowledgeBase:
        """Map database row to KnowledgeBase model."""
        return KnowledgeBase(**data)
    
    async def update_kb(self, kb_id: int, kb_update: KnowledgeBaseUpdate, tenant_id: int) -> Optional[KnowledgeBase]:
        """Update knowledge base status and metadata."""
        # Remove None values from update data
        data = {k: v for k, v in kb_update.model_dump().items() if v is not None}
        
        if not data:
            # No updates to make
            return await self.get_by_id(kb_id, tenant_id)
        
        return await self.update(kb_id, data, tenant_id)
    
    async def get_by_tenant(self, tenant_id: int) -> List[KnowledgeBase]:
        """Get all knowledge bases for a tenant."""
        return await self.get_all(tenant_id)


class FileRepository(BaseRepository[KBFile]):
    """Repository for file operations."""
    
    def __init__(self):
        super().__init__("kb_files")
    
    def _map_to_model(self, data: Dict[str, Any]) -> KBFile:
        """Map database row to KBFile model."""
        return KBFile(**data)
    
    async def get_files_by_kb(self, knowledge_base_id: int) -> List[KBFile]:
        """Get all files for a specific knowledge base."""
        try:
            result = (
                self.client.from_(self.table_name)
                .select("*")
                .eq("knowledge_base_id", knowledge_base_id)
                .execute()
            )
            
            return [self._map_to_model(row) for row in result.data or []]
            
        except Exception as e:
            logger.error(f"Error getting files for KB {knowledge_base_id}: {e}")
            raise
    
    async def create_file(self, file_data: Dict[str, Any]) -> KBFile:
        """Create a new file record."""
        return await self.create(file_data)


# Repository instances for dependency injection
tenant_repository = TenantRepository()
job_repository = JobRepository() 
knowledge_base_repository = KnowledgeBaseRepository()
file_repository = FileRepository() 