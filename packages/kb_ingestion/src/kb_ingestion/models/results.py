"""Result data models for ingestion pipeline operations."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class IngestionResult:
    """Result of a single source ingestion operation.
    
    Contains all information about the processing of a single file or URL,
    including success status, generated node IDs, metadata, and timing information.
    """
    
    success: bool
    """Whether the ingestion operation was successful"""
    
    source_id: str
    """Unique identifier for the source (filename, URL, etc.)"""
    
    chunk_ids: List[str]
    """List of chunk IDs created during ingestion"""
    
    metadata: Dict[str, Any]
    """Additional metadata about the processing operation"""
    
    processing_time_seconds: float
    """Time taken to process this source in seconds"""
    
    error: Optional[Exception] = None
    """Exception that occurred during processing, if any"""
    
    timestamp: datetime = field(default_factory=datetime.now)
    """When the processing was completed"""
    
    def __post_init__(self):
        """Validate the result data."""
        if self.metadata is None:
            self.metadata = {}
        
        # If failed, ensure we have error information
        if not self.success and self.error is None:
            self.error = Exception("Unknown error occurred during processing")
    
    @property
    def chunk_count(self) -> int:
        """Get the number of chunks created."""
        return len(self.node_ids)
    
    @property
    def has_error(self) -> bool:
        """Check if this result contains an error."""
        return self.error is not None
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the result."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key."""
        return self.metadata.get(key, default)


@dataclass
class BatchIngestionResult:
    """Result of a batch ingestion operation.
    
    Contains aggregated information about processing multiple sources,
    including individual results and overall statistics.
    """
    
    results: List[IngestionResult]
    """Individual results for each processed source"""
    
    total_processed: int
    """Total number of sources that were processed"""
    
    total_succeeded: int
    """Number of sources that were successfully processed"""
    
    total_failed: int
    """Number of sources that failed processing"""
    
    total_processing_time_seconds: float
    """Total time taken for the entire batch operation"""
    
    batch_metadata: Dict[str, Any] = field(default_factory=dict)
    """Metadata for the entire batch operation"""
    
    timestamp: datetime = field(default_factory=datetime.now)
    """When the batch processing was completed"""
    
    def __post_init__(self):
        """Validate and compute batch statistics."""
        if self.batch_metadata is None:
            self.batch_metadata = {}
        
        # Validate counts match results
        if len(self.results) != self.total_processed:
            raise ValueError("Number of results must match total_processed count")
        
        # Verify success/failure counts
        actual_succeeded = sum(1 for r in self.results if r.success)
        actual_failed = sum(1 for r in self.results if not r.success)
        
        if actual_succeeded != self.total_succeeded:
            raise ValueError(f"total_succeeded ({self.total_succeeded}) doesn't match actual count ({actual_succeeded})")
        
        if actual_failed != self.total_failed:
            raise ValueError(f"total_failed ({self.total_failed}) doesn't match actual count ({actual_failed})")
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate as a percentage."""
        if self.total_processed == 0:
            return 0.0
        return (self.total_succeeded / self.total_processed) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate the failure rate as a percentage."""
        return 100.0 - self.success_rate
    
    @property
    def total_nodes_created(self) -> int:
        """Get the total number of nodes created across all successful results."""
        return sum(result.node_count for result in self.results if result.success)
    
    @property
    def average_processing_time(self) -> float:
        """Get the average processing time per source."""
        if self.total_processed == 0:
            return 0.0
        return self.total_processing_time_seconds / self.total_processed
    
    def get_successful_results(self) -> List[IngestionResult]:
        """Get only the successful results."""
        return [result for result in self.results if result.success]
    
    def get_failed_results(self) -> List[IngestionResult]:
        """Get only the failed results."""
        return [result for result in self.results if not result.success]
    
    def get_errors(self) -> List[Exception]:
        """Get all errors that occurred during processing."""
        return [result.error for result in self.results if result.error is not None] 