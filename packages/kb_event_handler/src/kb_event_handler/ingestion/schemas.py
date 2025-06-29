"""Pydantic schemas for ingestion operations."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field


class IngestionJobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionRequest(BaseModel):
    """Request to start file ingestion."""
    resource_type: str = Field(..., description="Type of resource to ingest (document, website)")
    urls: Optional[List[str]] = Field(None, description="List of URLs to ingest")
    file_path: Optional[str] = Field(None, description="Path to file in storage")
    filename: Optional[str] = Field(None, description="Original filename")
    knowledge_base_id: int = Field(..., description="Target knowledge base ID")
    kb_key: str = Field(..., description="Target knowledge base key")
    mime_type: Optional[str] = Field(None, description="File MIME type")
    
    # Optional processing parameters
    chunk_size: Optional[int] = Field(None, description="Override default chunk size")
    chunk_overlap: Optional[int] = Field(None, description="Override default chunk overlap")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resource_type": "document",
                "urls": ["https://www.google.com", "https://www.wikipedia.org"],
                "file_path": "tenant_123/kb_456/documents/report.pdf",
                "filename": "quarterly_report.pdf",
                "knowledge_base_id": 456,
                "kb_key": "uuid",
                "mime_type": "application/pdf"
            }
        }


class IngestionJobResponse(BaseModel):
    """Response after creating an ingestion job."""
    
    job_id: int = Field(..., description="Unique job identifier")
    status: IngestionJobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    file_path: str = Field(..., description="Path to file in storage")
    filename: str = Field(..., description="Original filename")
    knowledge_base_id: int = Field(..., description="Target knowledge base ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": 789,
                "status": "queued",
                "created_at": "2024-01-15T10:30:00Z",
                "file_path": "tenant_123/kb_456/documents/report.pdf",
                "filename": "quarterly_report.pdf",
                "knowledge_base_id": 456
            }
        }


class IngestionResult(BaseModel):
    """Result of ingestion processing."""
    
    success: bool = Field(..., description="Whether ingestion succeeded")
    node_count: int = Field(default=0, description="Number of text chunks created")
    processing_time_seconds: float = Field(default=0.0, description="Processing duration")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    
    # Metadata about the processing
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional processing metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "node_count": 45,
                "processing_time_seconds": 12.5,
                "metadata": {
                    "file_size_bytes": 2048576,
                    "embedding_model": "text-embedding-3-small",
                    "chunk_size": 1024
                }
            }
        }


class JobStatusResponse(BaseModel):
    """Response for job status queries."""
    
    job_id: int = Field(..., description="Job identifier")
    status: IngestionJobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    
    # File information
    file_path: str = Field(..., description="Path to file in storage")
    filename: str = Field(..., description="Original filename")
    knowledge_base_id: int = Field(..., description="Target knowledge base ID")
    
    # Results (only present when completed)
    result: Optional[IngestionResult] = Field(None, description="Processing result")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": 789,
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z",
                "started_at": "2024-01-15T10:30:05Z",
                "completed_at": "2024-01-15T10:30:18Z",
                "file_path": "tenant_123/kb_456/documents/report.pdf",
                "filename": "quarterly_report.pdf",
                "knowledge_base_id": 456,
                "result": {
                    "success": True,
                    "node_count": 45,
                    "processing_time_seconds": 12.5
                }
            }
        }


class BatchIngestionRequest(BaseModel):
    """Request to start batch file ingestion (future enhancement)."""
    
    files: List[IngestionRequest] = Field(..., description="List of files to process")
    knowledge_base_id: int = Field(..., description="Target knowledge base ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "knowledge_base_id": 456,
                "files": [
                    {
                        "file_path": "tenant_123/kb_456/documents/report1.pdf",
                        "filename": "report1.pdf",
                        "knowledge_base_id": 456
                    },
                    {
                        "file_path": "tenant_123/kb_456/documents/report2.pdf", 
                        "filename": "report2.pdf",
                        "knowledge_base_id": 456
                    }
                ]
            }
        }


class BatchIngestionResponse(BaseModel):
    """Response after creating batch ingestion jobs."""
    
    job_ids: List[int] = Field(..., description="List of created job IDs")
    total_jobs: int = Field(..., description="Total number of jobs created")
    knowledge_base_id: int = Field(..., description="Target knowledge base ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_ids": [789, 790, 791],
                "total_jobs": 3,
                "knowledge_base_id": 456
            }
        } 