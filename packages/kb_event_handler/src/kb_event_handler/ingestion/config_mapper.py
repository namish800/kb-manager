"""Configuration mapping between FastAPI settings and ingestion pipeline."""

import logging
from typing import Optional

from ..config import Settings

logger = logging.getLogger(__name__)


class IngestionConfigMapper:
    """Maps FastAPI settings to ingestion pipeline configurations."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def create_pipeline_config(
        self, 
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> dict:
        """
        Create configuration dict for the ingestion pipeline.
        
        Args:
            chunk_size: Override default chunk size
            chunk_overlap: Override default chunk overlap
            
        Returns:
            Configuration dict for LlamaIndexDocumentIngestionToPinecone
        """
        config = {
            # Text splitting configuration
            "chunk_size": chunk_size or self.settings.chunk_size,
            "chunk_overlap": chunk_overlap or self.settings.chunk_overlap,
            
            # OpenAI embedding configuration
            "openai_api_key": self.settings.openai_api_key,
            "embedding_model": self.settings.embedding_model,
            "embedding_dimensions": self.settings.embedding_dimensions,
            
            # Pinecone configuration
            "pinecone_api_key": self.settings.pinecone_api_key,
            "pinecone_index_name": self.settings.pinecone_index_name,
            "pinecone_environment": self.settings.pinecone_environment,
            
            # Processing configuration
            "max_concurrent_jobs": self.settings.max_concurrent_jobs,
            "timeout_minutes": self.settings.job_timeout_minutes,
        }
        
        logger.debug(f"Created pipeline config: chunk_size={config['chunk_size']}, "
                    f"chunk_overlap={config['chunk_overlap']}, "
                    f"embedding_model={config['embedding_model']}")
        
        return config
    
    def create_embedding_config(self) -> dict:
        """Create embedding-specific configuration."""
        return {
            "api_key": self.settings.openai_api_key,
            "model": self.settings.embedding_model,
            "dimensions": self.settings.embedding_dimensions,
        }
    
    def create_vector_store_config(self) -> dict:
        """Create vector store configuration."""
        return {
            "api_key": self.settings.pinecone_api_key,
            "index_name": self.settings.pinecone_index_name,
            "environment": self.settings.pinecone_environment,
            "dimensions": self.settings.embedding_dimensions,
        }
    
    def validate_configuration(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        required_settings = [
            ("openai_api_key", self.settings.openai_api_key),
            ("pinecone_api_key", self.settings.pinecone_api_key),
            ("pinecone_index_name", self.settings.pinecone_index_name),
        ]
        
        missing_settings = []
        for name, value in required_settings:
            if not value or (isinstance(value, str) and not value.strip()):
                missing_settings.append(name)
        
        if missing_settings:
            logger.error(f"Missing required configuration: {', '.join(missing_settings)}")
            return False
        
        # Validate numeric settings
        if self.settings.chunk_size <= 0:
            logger.error(f"Invalid chunk_size: {self.settings.chunk_size}")
            return False
            
        if self.settings.chunk_overlap < 0:
            logger.error(f"Invalid chunk_overlap: {self.settings.chunk_overlap}")
            return False
            
        if self.settings.chunk_overlap >= self.settings.chunk_size:
            logger.error(f"chunk_overlap ({self.settings.chunk_overlap}) must be less than chunk_size ({self.settings.chunk_size})")
            return False
        
        logger.info("Ingestion configuration validation passed")
        return True
    
    def get_processing_limits(self) -> dict:
        """Get processing limits configuration."""
        return {
            "max_concurrent_jobs": self.settings.max_concurrent_jobs,
            "job_timeout_minutes": self.settings.job_timeout_minutes,
            "max_file_size_mb": self.settings.max_file_size_mb,
        } 