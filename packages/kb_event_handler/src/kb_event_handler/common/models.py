"""Database models for Supabase entities."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# Core Tables Models
class Tenant(BaseModel):
    """Tenant model representing organizations/workspaces."""
    
    id: int = Field(description="Unique tenant identifier")
    name: str = Field(description="Tenant display name")
    slug: str = Field(description="Unique tenant slug for URLs")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class Profile(BaseModel):
    """User profile model linked to Supabase Auth users."""
    
    id: str = Field(description="UUID matching auth.users.id")
    full_name: Optional[str] = Field(default=None, description="User's full name")
    avatar_url: Optional[str] = Field(default=None, description="Avatar image URL")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class TenantUser(BaseModel):
    """Junction table for user-tenant relationships."""
    
    id: int = Field(description="Unique relationship identifier")
    tenant_id: int = Field(description="Reference to tenant")
    user_id: str = Field(description="Reference to user profile UUID")
    role: Literal["owner", "admin", "member"] = Field(description="User role within tenant")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


# Knowledge Base Tables Models
class KnowledgeBase(BaseModel):
    """Knowledge base model for document collections."""
    
    id: int = Field(description="Unique knowledge base identifier")
    tenant_id: int = Field(description="Reference to owning tenant")
    name: str = Field(description="Knowledge base display name")
    description: Optional[str] = Field(default=None, description="Optional description")
    type: Literal["document", "website"] = Field(description="Knowledge base type")
    status: Literal["queued", "processing", "completed", "failed", "refreshing"] = Field(
        default="queued", description="Processing status"
    )
    progress: Optional[int] = Field(
        default=0, ge=0, le=100, description="Processing progress percentage"
    )
    url: Optional[str] = Field(default=None, description="URL for website-type KBs")
    pinecone_namespace: Optional[str] = Field(
        default=None, description="Pinecone namespace for vector storage"
    )
    document_count: Optional[int] = Field(
        default=0, description="Number of processed documents"
    )
    token_count: Optional[int] = Field(
        default=0, description="Total tokens processed"
    )
    created_by: Optional[str] = Field(
        default=None, description="UUID of creating user"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class KBFile(BaseModel):
    """File model for document-type knowledge bases."""
    
    id: int = Field(description="Unique file identifier")
    knowledge_base_id: int = Field(description="Reference to knowledge base")
    original_name: str = Field(description="Original filename")
    storage_path: str = Field(description="Path in Supabase Storage")
    file_url: Optional[str] = Field(default=None, description="Public file URL")
    size_bytes: int = Field(description="File size in bytes")
    mime_type: str = Field(description="MIME type of the file")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class KBJob(BaseModel):
    """Job model for tracking processing operations."""
    
    id: int = Field(description="Unique job identifier")
    knowledge_base_id: int = Field(description="Reference to knowledge base")
    job_type: Literal["ingestion", "refresh", "delete"] = Field(
        description="Type of job operation"
    )
    status: Literal["queued", "processing", "completed", "failed"] = Field(
        default="queued", description="Job status"
    )
    progress: Optional[int] = Field(
        default=0, ge=0, le=100, description="Job progress percentage"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if job failed"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Job start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Job completion timestamp"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


# Create/Update Models (for API requests)
class KBJobCreate(BaseModel):
    """Model for creating new jobs."""
    
    knowledge_base_id: int = Field(description="Reference to knowledge base")
    job_type: Literal["ingestion", "refresh", "delete"] = Field(
        description="Type of job operation"
    )


class KBJobUpdate(BaseModel):
    """Model for updating job status and progress."""
    
    status: Optional[Literal["queued", "processing", "completed", "failed"]] = Field(
        default=None, description="Job status"
    )
    progress: Optional[int] = Field(
        default=None, ge=0, le=100, description="Job progress percentage"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if job failed"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Job start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Job completion timestamp"
    )


class KnowledgeBaseUpdate(BaseModel):
    """Model for updating knowledge base status."""
    
    status: Optional[Literal["queued", "processing", "completed", "failed", "refreshing"]] = Field(
        default=None, description="Processing status"
    )
    progress: Optional[int] = Field(
        default=None, ge=0, le=100, description="Processing progress percentage"
    )
    pinecone_namespace: Optional[str] = Field(
        default=None, description="Pinecone namespace for vector storage"
    )
    document_count: Optional[int] = Field(
        default=None, description="Number of processed documents"
    )
    token_count: Optional[int] = Field(
        default=None, description="Total tokens processed"
    ) 