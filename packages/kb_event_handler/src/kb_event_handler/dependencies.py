"""Global dependencies for the FastAPI application."""

import logging
import uuid
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import HTTPBearer
from kb_event_handler.common.repositories import FileRepository, JobRepository

from kb_event_handler.config import settings
from kb_event_handler.exceptions import AuthenticationError, ValidationError
# Import database repositories
from kb_event_handler.database import (
    file_repository,
    job_repository, 
    knowledge_base_repository,
    tenant_repository,
    supabase_client,
)
# Import file handling services
from kb_event_handler.common import (
    StorageClient,
    FileValidationService,
    TempFileManager,
)
# Import ingestion services
from kb_event_handler.ingestion.ingestion_service import DocumentIngestionService, WebsiteIngestionService
from kb_event_handler.ingestion.background_processor import BackgroundJobProcessor
from kb_event_handler.ingestion.interfaces.ingestion_service import IIngestionService
from kb_event_handler.ingestion.interfaces.ipipeline_factory import IIngestionPipelineFactory
from kb_event_handler.ingestion.pipeline_factory import IngestionPipelineFactory
from kb_ingestion.interfaces.ingestion import IIngestionPipeline
from kb_ingestion.llamaindex_document_ingestion import LlamaIndexDocumentIngestionToPinecone
from kb_ingestion.llamaindex_website_ingestion import LlamaIndexWebsiteIngestionToPinecone
from kb_ingestion.models.config import EmbeddingConfig, PipelineConfig
from llama_cloud_services import LlamaParse
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone
from firecrawl import FirecrawlApp


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

# Ingestion Pipelines
def get_firecrawl_reader():
    return FirecrawlApp(api_key=settings.firecrawl_api_key)

def get_llama_parse():
    return LlamaParse(api_key=settings.llama_parse_api_key)

def get_pinecone_vs():
    # Initialize Pinecone
    pc = Pinecone(api_key=settings.pinecone_api_key)
    pinecone_index = pc.Index(settings.pinecone_index_name)
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index,
    )
    return vector_store

async def get_document_ingestion_pipeline() -> IIngestionPipeline:
    """Get document ingestion pipeline instance."""
    openai_api_key = settings.openai_api_key
    embedding_config = EmbeddingConfig(
        api_key=openai_api_key, 
        model_name=settings.embedding_model
    )

    config = PipelineConfig(
        embedding_config=embedding_config,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    document_parser = get_llama_parse()
    pinecone_vs = get_pinecone_vs()
    
    return LlamaIndexDocumentIngestionToPinecone(config, pinecone_vs, document_parser)

async def get_website_ingestion_pipeline() -> IIngestionPipeline:
    """Get website ingestion pipeline instance."""
    openai_api_key = settings.openai_api_key
    embedding_config = EmbeddingConfig(
        api_key=openai_api_key, 
        model_name=settings.embedding_model
    )

    config = PipelineConfig(
        embedding_config=embedding_config,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    firecrawl_reader = get_firecrawl_reader()
    pinecone_vs = get_pinecone_vs()

    return LlamaIndexWebsiteIngestionToPinecone(config, pinecone_vs, firecrawl_reader)

async def get_ingestion_pipeline_factory() -> IIngestionPipelineFactory:
    """Get ingestion pipeline factory instance."""
    document_ingestion_pipeline = await get_document_ingestion_pipeline()
    website_ingestion_pipeline = await get_website_ingestion_pipeline()
    return IngestionPipelineFactory(
        pipelines_map={
            "document": document_ingestion_pipeline,
            "website": website_ingestion_pipeline
        }
    )

async def get_document_ingestion_service(
    temp_file_manager: Annotated[TempFileManager, Depends(get_temp_file_manager)]
) -> IIngestionService:
    """Get document ingestion service instance."""
    pipeline_factory = await get_ingestion_pipeline_factory()
    return DocumentIngestionService(pipeline_factory, temp_file_manager)

async def get_website_ingestion_service() -> IIngestionService:
    """Get website ingestion service instance."""
    pipeline_factory = await get_ingestion_pipeline_factory()
    return WebsiteIngestionService(pipeline_factory)


async def get_background_job_processor(
    document_ingestion_service: Annotated[IIngestionService, Depends(get_document_ingestion_service)],
    website_ingestion_service: Annotated[IIngestionService, Depends(get_website_ingestion_service)],
    file_validation_service: Annotated[FileValidationService, Depends(get_file_validation_service)],
    job_repository: Annotated[JobRepository, Depends(get_job_repository)],
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
):
    """Get background job processor instance."""
    return BackgroundJobProcessor(
        document_ingestion_service=document_ingestion_service,
        website_ingestion_service=website_ingestion_service,
        file_validation_service=file_validation_service,
        job_repository=job_repository,
        file_repository=file_repository,
    )


# Dependency aliases for common use
CorrelationIdDep = Annotated[str, Depends(get_correlation_id)]
ApiKeyDep = Annotated[str, Depends(authenticate_api_key)] # TODO: Move this to middleware
TenantIdDep = Annotated[int, Depends(get_tenant_id)] # TODO: Move this to middleware
ValidatedTenantIdDep = Annotated[int, Depends(validate_tenant_access)] # TODO: Move this to middleware

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
DocumentIngestionServiceDep = Annotated[IIngestionService, Depends(get_document_ingestion_service)]
WebsiteIngestionServiceDep = Annotated[IIngestionService, Depends(get_website_ingestion_service)]
BackgroundJobProcessorDep = Annotated[BackgroundJobProcessor, Depends(get_background_job_processor)] 
