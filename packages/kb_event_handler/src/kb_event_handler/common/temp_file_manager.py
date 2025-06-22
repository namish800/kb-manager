"""Temporary file manager for safe file handling."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from .storage_client import StorageClient
from ..exceptions import StorageError

logger = logging.getLogger(__name__)


class TempFileManager:
    """Manager for temporary file operations."""
    
    def __init__(self, storage_client: StorageClient, temp_dir: Optional[str] = None):
        self.storage_client = storage_client
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self._ensure_temp_dir()
    
    def _ensure_temp_dir(self):
        """Ensure temporary directory exists."""
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def _get_temp_file_path(self, filename: str) -> str:
        """Generate a temporary file path."""
        # Use a timestamp to avoid conflicts
        import time
        timestamp = int(time.time() * 1000)
        safe_filename = f"{timestamp}_{filename}"
        return os.path.join(self.temp_dir, safe_filename)
    
    async def download_to_temp_file(self, file_path: str, filename: str) -> str:
        """
        Download a file from storage to a temporary location.
        
        Args:
            file_path: Path to file in storage
            filename: Original filename (for temp file naming)
            
        Returns:
            Path to temporary file
            
        Raises:
            StorageError: If download fails
        """
        try:
            logger.info(f"Downloading {file_path} to temporary file")
            
            # Download file content
            file_content = await self.storage_client.download_file(file_path)
            
            # Create temporary file
            temp_file_path = self._get_temp_file_path(filename)
            
            # Write to temporary file
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(file_content)
            
            logger.info(f"File downloaded to temporary location: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Failed to download file to temp location: {str(e)}")
            raise StorageError(f"Failed to create temporary file: {str(e)}")
    
    def cleanup_temp_file(self, temp_file_path: str) -> bool:
        """
        Clean up a temporary file.
        
        Args:
            temp_file_path: Path to temporary file
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
                return True
            else:
                logger.warning(f"Temporary file not found for cleanup: {temp_file_path}")
                return True  # Consider this success since file doesn't exist
                
        except Exception as e:
            logger.error(f"Failed to cleanup temporary file {temp_file_path}: {str(e)}")
            return False
    
    @asynccontextmanager
    async def temp_file_context(self, file_path: str, filename: str) -> AsyncGenerator[str, None]:
        """
        Context manager for temporary file operations with automatic cleanup.
        
        Args:
            file_path: Path to file in storage
            filename: Original filename
            
        Yields:
            Path to temporary file
            
        Example:
            async with temp_manager.temp_file_context("path/to/file.pdf", "document.pdf") as temp_path:
                # Use temp_path for processing
                process_file(temp_path)
            # File is automatically cleaned up
        """
        temp_file_path = None
        try:
            # Download to temporary file
            temp_file_path = await self.download_to_temp_file(file_path, filename)
            yield temp_file_path
            
        finally:
            # Always cleanup, even if an exception occurred
            if temp_file_path:
                self.cleanup_temp_file(temp_file_path)
    
    def get_temp_file_info(self, temp_file_path: str) -> Optional[dict]:
        """
        Get information about a temporary file.
        
        Args:
            temp_file_path: Path to temporary file
            
        Returns:
            Dict with file info or None if file doesn't exist
        """
        try:
            if not os.path.exists(temp_file_path):
                return None
            
            stat = os.stat(temp_file_path)
            return {
                "path": temp_file_path,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "exists": True,
            }
            
        except Exception as e:
            logger.error(f"Failed to get temp file info: {str(e)}")
            return None
    
    def cleanup_old_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age in hours for temp files
            
        Returns:
            Number of files cleaned up
        """
        import time
        
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            cleanup_count = 0
            
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    
                    if file_age > max_age_seconds:
                        if self.cleanup_temp_file(file_path):
                            cleanup_count += 1
            
            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} old temporary files")
            
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old temp files: {str(e)}")
            return 0 