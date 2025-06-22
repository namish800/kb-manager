"""Abstract interface for ingestion pipelines following SOLID principles."""

from abc import ABC, abstractmethod
from typing import List

from kb_ingestion.models.requests import FileWrapper, WebsiteWrapper
from kb_ingestion.models.results import IngestionResult, BatchIngestionResult


class IIngestionPipeline(ABC):
    """Main ingestion pipeline interface.
    
    This interface defines the contract that all ingestion pipeline implementations
    must follow, supporting both single and batch processing modes.
    """
    
    @abstractmethod
    async def ingest(self, source: FileWrapper | WebsiteWrapper) -> IngestionResult:
        """Process a single source and return ingestion result.
        
        Args:
            source: The file wrapper containing content and metadata to process
            
        Returns:
            IngestionResult containing processing status, node IDs, and metadata
        """
        pass
    
    @abstractmethod
    async def validate_source(self, source: FileWrapper | WebsiteWrapper) -> bool:
        """Validate if source can be processed by this pipeline.
        
        Args:
            source: The file wrapper to validate
            
        Returns:
            True if the source can be processed, False otherwise
        """
        pass 