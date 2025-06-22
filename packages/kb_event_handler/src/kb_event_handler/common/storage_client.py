"""Supabase Storage client for file operations."""

import logging
from typing import Optional

from supabase import Client

from ..config import Settings
from ..exceptions import StorageError

logger = logging.getLogger(__name__)


class StorageClient:
    """Wrapper for Supabase Storage operations."""
    
    def __init__(self, supabase_client: Client, config: Settings):
        self.client = supabase_client
        self.config = config
        self.bucket_name = config.supabase_storage_bucket
        
    async def download_file(self, file_path: str) -> bytes:
        """
        Download a file from Supabase Storage.
        
        Args:
            file_path: Path to the file in storage
            
        Returns:
            File content as bytes
            
        Raises:
            StorageError: If file download fails
        """
        try:
            logger.info(f"Downloading file from storage: {file_path}")
            
            # Download file from Supabase Storage
            response = self.client.storage.from_(self.bucket_name).download(file_path)
            
            if not response:
                raise StorageError(f"File not found in storage: {file_path}")
                
            logger.info(f"Successfully downloaded file: {file_path} ({len(response)} bytes)")
            return response
            
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {str(e)}")
            raise StorageError(f"Failed to download file from storage: {str(e)}")
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            file_path: Path to the file in storage
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            # List files in the directory to check existence
            # This is a workaround since Supabase doesn't have a direct exists method
            response = self.client.storage.from_(self.bucket_name).list(
                path=file_path.rsplit('/', 1)[0] if '/' in file_path else ""
            )
            
            filename = file_path.split('/')[-1]
            return any(file.get('name') == filename for file in response)
            
        except Exception as e:
            logger.warning(f"Could not check file existence for {file_path}: {str(e)}")
            return False
    
    async def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        Get file metadata from storage.
        
        Args:
            file_path: Path to the file in storage
            
        Returns:
            File metadata dict or None if not found
        """
        try:
            # List files to get metadata
            response = self.client.storage.from_(self.bucket_name).list(
                path=file_path.rsplit('/', 1)[0] if '/' in file_path else ""
            )
            
            filename = file_path.split('/')[-1]
            for file_info in response:
                if file_info.get('name') == filename:
                    return file_info
                    
            return None
            
        except Exception as e:
            logger.warning(f"Could not get file info for {file_path}: {str(e)}")
            return None
    
    async def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Get file size from storage.
        
        Args:
            file_path: Path to the file in storage
            
        Returns:
            File size in bytes or None if not found
        """
        file_info = await self.get_file_info(file_path)
        if file_info:
            return file_info.get('metadata', {}).get('size')
        return None 