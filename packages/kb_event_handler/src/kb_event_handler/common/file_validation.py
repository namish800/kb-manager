"""File validation service."""

import logging
from typing import Dict, Any

from .file_types import (
    MAX_FILE_SIZE_BYTES,
    is_supported_file_type,
    get_expected_mime_type,
    is_valid_mime_type,
    format_file_size,
    get_file_type_description,
)
from .storage_client import StorageClient
from ..exceptions import ValidationError

logger = logging.getLogger(__name__)


class FileValidationResult:
    """Result of file validation."""
    
    def __init__(self, is_valid: bool, errors: list[str] = None, metadata: Dict[str, Any] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.metadata = metadata or {}
    
    def add_error(self, error: str):
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False


class FileValidationService:
    """Service for validating file uploads."""
    
    def __init__(self, storage_client: StorageClient):
        self.storage_client = storage_client
    
    async def validate_file(
        self,
        filename: str,
        file_path: str,
        mime_type: str = None,
        check_existence: bool = True
    ) -> FileValidationResult:
        """
        Validate a file for ingestion.
        
        Args:
            filename: Original filename
            file_path: Path to file in storage
            mime_type: MIME type of the file (optional)
            check_existence: Whether to check if file exists in storage
            
        Returns:
            FileValidationResult with validation details
        """
        result = FileValidationResult(is_valid=True)
        
        logger.info(f"Validating file: {filename} at {file_path}")
        
        # 1. Validate file type by extension
        if not is_supported_file_type(filename):
            result.add_error(
                f"Unsupported file type. File '{filename}' is not a supported format. "
                f"Supported formats: PDF, PowerPoint (PPT/PPTX), Word (DOC/DOCX), Markdown (MD)"
            )
        
        # 2. Validate MIME type if provided
        if mime_type:
            if not is_valid_mime_type(mime_type):
                expected_mime = get_expected_mime_type(filename)
                result.add_error(
                    f"Invalid MIME type '{mime_type}' for file '{filename}'. "
                    f"Expected: '{expected_mime}'"
                )
        
        # 3. Check file existence in storage
        if check_existence:
            try:
                exists = await self.storage_client.file_exists(file_path)
                if not exists:
                    result.add_error(f"File not found in storage: {file_path}")
                else:
                    # Get file size for validation
                    file_size = await self.storage_client.get_file_size(file_path)
                    if file_size is not None:
                        result.metadata["file_size"] = file_size
                        
                        # 4. Validate file size
                        if file_size > MAX_FILE_SIZE_BYTES:
                            result.add_error(
                                f"File too large. Size: {format_file_size(file_size)} "
                                f"(max allowed: {format_file_size(MAX_FILE_SIZE_BYTES)})"
                            )
                    else:
                        logger.warning(f"Could not determine file size for {file_path}")
                        
            except Exception as e:
                logger.error(f"Error checking file existence: {str(e)}")
                result.add_error(f"Could not validate file existence: {str(e)}")
        
        # Add metadata
        result.metadata.update({
            "filename": filename,
            "file_path": file_path,
            "file_type": get_file_type_description(filename),
            "expected_mime_type": get_expected_mime_type(filename),
        })
        
        if result.is_valid:
            logger.info(f"File validation passed: {filename}")
        else:
            logger.warning(f"File validation failed: {filename}. Errors: {result.errors}")
        
        return result
    
    def validate_filename(self, filename: str) -> FileValidationResult:
        """
        Quick validation of just the filename (no storage checks).
        
        Args:
            filename: Filename to validate
            
        Returns:
            FileValidationResult
        """
        result = FileValidationResult(is_valid=True)
        
        if not filename or not filename.strip():
            result.add_error("Filename cannot be empty")
            return result
        
        if not is_supported_file_type(filename):
            result.add_error(
                f"Unsupported file type. File '{filename}' is not a supported format. "
                f"Supported formats: PDF, PowerPoint (PPT/PPTX), Word (DOC/DOCX), Markdown (MD)"
            )
        
        result.metadata.update({
            "filename": filename,
            "file_type": get_file_type_description(filename),
            "expected_mime_type": get_expected_mime_type(filename),
        })
        
        return result
    
    async def validate_file_size_only(self, file_path: str) -> FileValidationResult:
        """
        Validate only file size from storage.
        
        Args:
            file_path: Path to file in storage
            
        Returns:
            FileValidationResult
        """
        result = FileValidationResult(is_valid=True)
        
        try:
            file_size = await self.storage_client.get_file_size(file_path)
            if file_size is None:
                result.add_error(f"Could not determine file size for {file_path}")
                return result
            
            result.metadata["file_size"] = file_size
            
            if file_size > MAX_FILE_SIZE_BYTES:
                result.add_error(
                    f"File too large. Size: {format_file_size(file_size)} "
                    f"(max allowed: {format_file_size(MAX_FILE_SIZE_BYTES)})"
                )
                
        except Exception as e:
            logger.error(f"Error validating file size: {str(e)}")
            result.add_error(f"Could not validate file size: {str(e)}")
        
        return result 