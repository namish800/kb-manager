"""Ingestion service wrapper for the kb_ingestion pipeline."""

import asyncio
import logging
import time
from typing import Optional, Dict, Any

from .config_mapper import IngestionConfigMapper
from .schemas import IngestionResult
from ..config import Settings
from ..exceptions import KBEventHandlerException

logger = logging.getLogger(__name__)


class IngestionService:
    """Service wrapper for the kb_ingestion pipeline."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config_mapper = IngestionConfigMapper(settings)
        self._pipeline = None
        self._pipeline_lock = asyncio.Lock()
    
    async def get_pipeline(self):
        """
        Lazy load the ingestion pipeline.
        
        Returns:
            Initialized ingestion pipeline instance
            
        Raises:
            KBEventHandlerException: If pipeline initialization fails
        """
        if self._pipeline is None:
            async with self._pipeline_lock:
                if self._pipeline is None:  # Double-check locking
                    await self._initialize_pipeline()
        
        return self._pipeline
    
    async def _initialize_pipeline(self):
        """Initialize the ingestion pipeline with current configuration."""
        try:
            logger.info("Initializing ingestion pipeline...")
            
            # Validate configuration first
            if not self.config_mapper.validate_configuration():
                raise KBEventHandlerException(
                    message="Invalid ingestion configuration",
                    error_code="INVALID_CONFIGURATION",
                    status_code=500
                )
            
            # Import here to avoid circular imports and heavy dependencies at startup
            from kb_ingestion.interfaces import IIngestionPipeline
            from kb_ingestion.models import PipelineConfig, EmbeddingConfig, VectorStoreConfig
            
            # Create pipeline configuration
            pipeline_config_dict = self.config_mapper.create_pipeline_config()
            
            # Create configuration objects
            pipeline_config = PipelineConfig(
                chunk_size=pipeline_config_dict["chunk_size"],
                chunk_overlap=pipeline_config_dict["chunk_overlap"],
                concurrent_processing=True,
                max_concurrent_docs=pipeline_config_dict["max_concurrent_jobs"]
            )
            
            embedding_config = EmbeddingConfig(
                provider="openai",
                model=pipeline_config_dict["embedding_model"],
                api_key=pipeline_config_dict["openai_api_key"],
                dimensions=pipeline_config_dict["embedding_dimensions"]
            )
            
            vector_store_config = VectorStoreConfig(
                provider="pinecone",
                index_name=pipeline_config_dict["pinecone_index_name"],
                api_key=pipeline_config_dict["pinecone_api_key"],
                environment=pipeline_config_dict["pinecone_environment"],
                dimensions=pipeline_config_dict["embedding_dimensions"]
            )
            
            # Import and initialize the concrete implementation
            from kb_ingestion.llamaindex_document_ingestion import LlamaIndexDocumentIngestionToPinecone
            
            self._pipeline = LlamaIndexDocumentIngestionToPinecone(
                pipeline_config=pipeline_config,
                embedding_config=embedding_config,
                vector_store_config=vector_store_config
            )
            
            logger.info("Ingestion pipeline initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import ingestion pipeline: {e}")
            raise KBEventHandlerException(
                message="Ingestion pipeline not available",
                error_code="PIPELINE_IMPORT_ERROR",
                status_code=500,
                details={"import_error": str(e)}
            )
        except Exception as e:
            logger.error(f"Failed to initialize ingestion pipeline: {e}")
            raise KBEventHandlerException(
                message="Failed to initialize ingestion pipeline",
                error_code="PIPELINE_INIT_ERROR", 
                status_code=500,
                details={"error": str(e)}
            )
    
    async def ingest_file(
        self,
        temp_file_path: str,
        filename: str,
        tenant_id: int,
        knowledge_base_id: int,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IngestionResult:
        """
        Process a single file through the ingestion pipeline.
        
        Args:
            temp_file_path: Path to temporary file
            filename: Original filename
            tenant_id: Tenant ID for multi-tenancy
            knowledge_base_id: Target knowledge base ID
            chunk_size: Override default chunk size
            chunk_overlap: Override default chunk overlap
            metadata: Additional metadata to include
            
        Returns:
            IngestionResult with processing details
            
        Raises:
            KBEventHandlerException: If ingestion fails
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting ingestion for file: {filename} (tenant: {tenant_id}, kb: {knowledge_base_id})")
            
            # Get the pipeline
            pipeline = await self.get_pipeline()
            
            # Import FileWrapper from kb_ingestion
            from kb_ingestion.models import FileWrapper
            
            # Create FileWrapper
            file_wrapper = FileWrapper(
                file_path=temp_file_path,
                filename=filename,
                metadata={
                    "tenant_id": tenant_id,
                    "knowledge_base_id": knowledge_base_id,
                    "original_filename": filename,
                    **(metadata or {})
                }
            )
            
            # Validate the file source
            if not await pipeline.validate_source(file_wrapper):
                raise KBEventHandlerException(
                    message=f"File validation failed for {filename}",
                    error_code="FILE_VALIDATION_FAILED",
                    status_code=400
                )
            
            # Process the file
            logger.info(f"Processing file through ingestion pipeline: {filename}")
            ingestion_result = await pipeline.ingest(file_wrapper)
            
            processing_time = time.time() - start_time
            
            # Convert to our schema
            result = IngestionResult(
                success=ingestion_result.success,
                node_count=len(ingestion_result.node_ids) if ingestion_result.node_ids else 0,
                processing_time_seconds=processing_time,
                error_message=ingestion_result.error_message if not ingestion_result.success else None,
                metadata={
                    "file_size_bytes": ingestion_result.metadata.get("file_size_bytes", 0),
                    "embedding_model": self.settings.embedding_model,
                    "chunk_size": chunk_size or self.settings.chunk_size,
                    "chunk_overlap": chunk_overlap or self.settings.chunk_overlap,
                    "tenant_id": tenant_id,
                    "knowledge_base_id": knowledge_base_id,
                    "node_ids": ingestion_result.node_ids,
                    **ingestion_result.metadata
                }
            )
            
            if result.success:
                logger.info(f"Successfully ingested {filename}: {result.node_count} chunks in {processing_time:.2f}s")
            else:
                logger.error(f"Failed to ingest {filename}: {result.error_message}")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"Ingestion failed for {filename}: {str(e)}"
            logger.error(error_message)
            
            return IngestionResult(
                success=False,
                node_count=0,
                processing_time_seconds=processing_time,
                error_message=error_message,
                metadata={
                    "tenant_id": tenant_id,
                    "knowledge_base_id": knowledge_base_id,
                    "error_type": type(e).__name__,
                    **(metadata or {})
                }
            )
    
    async def validate_file_for_ingestion(self, temp_file_path: str, filename: str) -> bool:
        """
        Validate if a file can be processed by the ingestion pipeline.
        
        Args:
            temp_file_path: Path to temporary file
            filename: Original filename
            
        Returns:
            True if file can be processed, False otherwise
        """
        try:
            pipeline = await self.get_pipeline()
            
            from kb_ingestion.models import FileWrapper
            
            file_wrapper = FileWrapper(
                file_path=temp_file_path,
                filename=filename,
                metadata={}
            )
            
            return await pipeline.validate_source(file_wrapper)
            
        except Exception as e:
            logger.error(f"File validation failed for {filename}: {e}")
            return False
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get status information about the ingestion pipeline.
        
        Returns:
            Dictionary with pipeline status information
        """
        return {
            "initialized": self._pipeline is not None,
            "configuration_valid": self.config_mapper.validate_configuration(),
            "processing_limits": self.config_mapper.get_processing_limits(),
            "embedding_model": self.settings.embedding_model,
            "chunk_size": self.settings.chunk_size,
            "chunk_overlap": self.settings.chunk_overlap,
        } 