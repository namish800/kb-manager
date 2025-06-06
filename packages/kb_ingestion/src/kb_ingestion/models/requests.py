"""Request data models for the ingestion pipeline."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Union
from io import BytesIO


@dataclass
class FileWrapper:
    """Encapsulates uploaded file with metadata for ingestion processing.
    
    This class provides a consistent interface for handling file uploads
    from API endpoints, containing both the file content and associated metadata.
    """
    
    filename: str
    """The original filename of the uploaded file"""
    
    content_type: str
    """MIME type of the file (e.g., 'text/plain', 'application/pdf')"""
    
    size: int
    """Size of the file in bytes"""
    
    content: Union[BytesIO, bytes]
    """The actual file content as bytes or BytesIO stream"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata associated with the file"""
    
    def __post_init__(self):
        """Ensure metadata is always a dictionary."""
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def file_extension(self) -> str:
        """Get the file extension from the filename."""
        return self.filename.split('.')[-1].lower() if '.' in self.filename else ''
    
    def get_content_as_bytes(self) -> bytes:
        """Get the file content as bytes regardless of the original type."""
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, BytesIO):
            # Save current position
            current_pos = self.content.tell()
            # Go to beginning and read all
            self.content.seek(0)
            content_bytes = self.content.read()
            # Restore position
            self.content.seek(current_pos)
            return content_bytes
        else:
            raise ValueError(f"Unsupported content type: {type(self.content)}")
    
    def reset_content_stream(self):
        """Reset the content stream to the beginning if it's a BytesIO object."""
        if isinstance(self.content, BytesIO):
            self.content.seek(0)


@dataclass
class WebsiteWrapper:
    """Encapsulates a website with metadata for ingestion processing."""
    urls: List[str]
    """The URLs of the website"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata associated with the website"""
    
    
@dataclass 
class BatchRequest:
    """Request for batch processing multiple files."""
    
    sources: list[FileWrapper]
    """List of file wrappers to process"""
    
    batch_metadata: Dict[str, Any] = field(default_factory=dict)
    """Metadata for the entire batch operation"""
    
    def __post_init__(self):
        """Validate batch request."""
        if not self.sources:
            raise ValueError("Batch request must contain at least one source")
        
        if self.batch_metadata is None:
            self.batch_metadata = {}
    
    @property
    def total_size(self) -> int:
        """Calculate total size of all files in the batch."""
        return sum(source.size for source in self.sources)
    
    @property 
    def file_count(self) -> int:
        """Get the number of files in the batch."""
        return len(self.sources) 