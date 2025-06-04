"""Knowledge Base Ingestion Pipeline Package.

A SOLID-principle compliant ingestion pipeline for processing documents and websites
into knowledge bases using LlamaIndex and vector stores.
"""

from .interfaces import IIngestionPipeline
from .models import (
    FileWrapper,
    BatchRequest,
    IngestionResult,
    BatchIngestionResult,
    PipelineConfig,
    EmbeddingConfig,
    VectorStoreConfig,
    ProcessingMode,
)
from .llamaindex_document_ingestion import LlamaIndexDocumentIngestionToPinecone

__version__ = "0.1.0"
__author__ = "namish800"

__all__ = [
    # Core interface
    "IIngestionPipeline",
    
    # Request models
    "FileWrapper",
    "BatchRequest",
    
    # Result models
    "IngestionResult", 
    "BatchIngestionResult",
    
    # Configuration models
    "PipelineConfig",
    "EmbeddingConfig",
    "VectorStoreConfig",
    "ProcessingMode",

    # Ingestion pipelines
    "LlamaIndexDocumentIngestionToPinecone",
] 