"""Common utilities and shared components."""

from kb_event_handler.common.models import (
    KBFile,
    KBJob,
    KBJobCreate,
    KBJobUpdate,
    KnowledgeBase,
    KnowledgeBaseUpdate,
    Profile,
    Tenant,
    TenantUser,
)
from kb_event_handler.common.repositories import (
    BaseRepository,
    FileRepository,
    JobRepository,
    KnowledgeBaseRepository,
    TenantRepository,
    file_repository,
    job_repository,
    knowledge_base_repository,
    tenant_repository,
)
from kb_event_handler.common.supabase_client import SupabaseClient, supabase_client
from kb_event_handler.common.storage_client import StorageClient
from kb_event_handler.common.file_validation import FileValidationService, FileValidationResult
from kb_event_handler.common.temp_file_manager import TempFileManager
from kb_event_handler.common.file_types import (
    MAX_FILE_SIZE_BYTES,
    ALLOWED_MIME_TYPES,
    ALLOWED_EXTENSIONS,
    is_supported_file_type,
    is_valid_mime_type,
    format_file_size,
)

__all__ = [
    # Models
    "Tenant",
    "Profile", 
    "TenantUser",
    "KnowledgeBase",
    "KBFile",
    "KBJob",
    "KBJobCreate",
    "KBJobUpdate", 
    "KnowledgeBaseUpdate",
    # Repository classes
    "BaseRepository",
    "TenantRepository",
    "JobRepository",
    "KnowledgeBaseRepository", 
    "FileRepository",
    # Repository instances
    "tenant_repository",
    "job_repository",
    "knowledge_base_repository",
    "file_repository",
    # Supabase client
    "SupabaseClient",
    "supabase_client",
    # File handling
    "StorageClient",
    "FileValidationService",
    "FileValidationResult",
    "TempFileManager",
    # File type constants
    "MAX_FILE_SIZE_BYTES",
    "ALLOWED_MIME_TYPES",
    "ALLOWED_EXTENSIONS",
    "is_supported_file_type",
    "is_valid_mime_type",
    "format_file_size",
] 