"""Configuration data models for ingestion pipelines."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Set
from enum import Enum


class ProcessingMode(Enum):
    """Enumeration of processing modes for ingestion pipelines."""
    SEQUENTIAL = "sequential"
    CONCURRENT = "concurrent"
    BATCH = "batch"

@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""

    api_key: str
    """API key for the embedding service"""
    
    model_name: str = "text-embedding-ada-002"
    """Name of the embedding model to use"""
    
    batch_size: int = 100
    """Number of texts to process in a single embedding request"""
    
    max_tokens: int = 8192
    """Maximum number of tokens per text for embedding"""
    
    dimensions: Optional[int] = None
    """Number of dimensions for the embeddings (model-dependent)"""
    
    extra_params: Dict[str, Any] = field(default_factory=dict)
    """Additional parameters for the embedding service"""
    
    def __post_init__(self):
        """Validate embedding configuration."""
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        
        if self.dimensions is not None and self.dimensions <= 0:
            raise ValueError("dimensions must be positive")
        
        if self.extra_params is None:
            self.extra_params = {}

@dataclass
class PipelineConfig:
    """Configuration for pipeline instantiation and operation.
    
    Contains all settings that control how the ingestion pipeline
    processes documents and manages resources.
    """

    embedding_config: EmbeddingConfig
    
    # Text processing settings
    chunk_size: int = 1024
    """Size of text chunks in tokens"""
    
    chunk_overlap: int = 100
    """Number of overlapping tokens between chunks"""
    
    # Performance settings
    max_retries: int = 3
    """Maximum number of retry attempts for failed operations"""
    
    timeout_seconds: int = 300
    """Timeout for individual operations in seconds"""
    
    processing_mode: ProcessingMode = ProcessingMode.CONCURRENT
    """How to process multiple sources (sequential, concurrent, or batch)"""
    
    max_concurrent_tasks: int = 5
    """Maximum number of concurrent processing tasks"""
    
    # Cache settings
    enable_caching: bool = True
    """Whether to enable caching of processed results"""
    
    cache_ttl_seconds: int = 3600
    """Time-to-live for cached items in seconds"""
    
    # Validation settings
    max_file_size_mb: int = 100
    """Maximum allowed file size in megabytes"""
    
    supported_file_types: Set[str] = field(default_factory=lambda: {
        'text/plain',
        'application/pdf', 
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/markdown',
        'text/html'
    })
    """Set of supported MIME types"""
    
    # Additional configuration
    extra_config: Dict[str, Any] = field(default_factory=dict)
    """Additional configuration parameters"""
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        
        if self.max_concurrent_tasks <= 0:
            raise ValueError("max_concurrent_tasks must be positive")
        
        if self.cache_ttl_seconds <= 0:
            raise ValueError("cache_ttl_seconds must be positive")
        
        if self.max_file_size_mb <= 0:
            raise ValueError("max_file_size_mb must be positive")
        
        if self.extra_config is None:
            self.extra_config = {}
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    def is_file_type_supported(self, content_type: str) -> bool:
        """Check if a content type is supported."""
        return content_type in self.supported_file_types
    
    def add_supported_file_type(self, content_type: str) -> None:
        """Add a new supported file type."""
        self.supported_file_types.add(content_type)
    
    def remove_supported_file_type(self, content_type: str) -> None:
        """Remove a supported file type."""
        self.supported_file_types.discard(content_type)
    
    def get_extra_config(self, key: str, default: Any = None) -> Any:
        """Get an extra configuration value."""
        return self.extra_config.get(key, default)
    
    def set_extra_config(self, key: str, value: Any) -> None:
        """Set an extra configuration value."""
        self.extra_config[key] = value


@dataclass
class VectorStoreConfig:
    """Configuration for vector storage."""
    
    index_name: str
    """Name of the vector index"""
    
    namespace: Optional[str] = None
    """Namespace for the vectors (if supported by the store)"""
    
    metadata_filter: Optional[Dict[str, Any]] = None
    """Default metadata filters to apply"""
    
    upsert_batch_size: int = 100
    """Number of vectors to upsert in a single operation"""
    
    extra_params: Dict[str, Any] = field(default_factory=dict)
    """Additional parameters for the vector store"""
    
    def __post_init__(self):
        """Validate vector store configuration."""
        if not self.index_name:
            raise ValueError("index_name cannot be empty")
        
        if self.upsert_batch_size <= 0:
            raise ValueError("upsert_batch_size must be positive")
        
        if self.extra_params is None:
            self.extra_params = {}
        
        if self.metadata_filter is None:
            self.metadata_filter = {} 