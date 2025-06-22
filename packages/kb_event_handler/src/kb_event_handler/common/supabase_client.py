"""Supabase client setup and configuration."""

import logging
from typing import Any, Dict, Optional

from supabase import Client, create_client

from ..config import settings
from ..exceptions import KBEventHandlerException


logger = logging.getLogger(__name__)


class SupabaseClient:
    """Async Supabase client wrapper with connection management."""
    
    def __init__(self):
        """Initialize the Supabase client."""
        self._client: Optional[Client] = None
        self._connected = False
    
    @property
    def client(self) -> Client:
        """Get the Supabase client instance."""
        if not self._client:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return self._client
    
    async def connect(self) -> None:
        """Establish connection to Supabase and test connectivity."""
        try:
            logger.info("Connecting to Supabase...")
            
            # Test connection by querying a system table
            result = self.client.from_("tenants").select("count", count="exact").limit(0).execute()
            
            if result:
                self._connected = True
                logger.info("Successfully connected to Supabase")
            else:
                raise KBEventHandlerException(
                    message="Failed to connect to Supabase: No response",
                    error_code="SUPABASE_CONNECTION_ERROR"
                )
                
        except Exception as e:
            self._connected = False
            logger.error(f"Failed to connect to Supabase: {e}")
            raise KBEventHandlerException(
                message=f"Supabase connection failed: {str(e)}",
                error_code="SUPABASE_CONNECTION_ERROR"
            ) from e
    
    async def disconnect(self) -> None:
        """Cleanup Supabase connection."""
        if self._client:
            # Supabase Python client doesn't require explicit disconnection
            # but we can clean up the reference
            self._client = None
            self._connected = False
            logger.info("Disconnected from Supabase")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Supabase connection."""
        try:
            if not self._connected:
                await self.connect()
            
            # Simple query to test connection
            start_time = logger.info("Performing Supabase health check...")
            result = self.client.from_("tenants").select("count", count="exact").limit(0).execute()
            
            if result is not None:
                return {
                    "status": "connected",
                    "database": "accessible",
                    "message": "Supabase connection healthy"
                }
            else:
                return {
                    "status": "error",
                    "database": "inaccessible", 
                    "message": "Supabase query returned no result"
                }
                
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return {
                "status": "error",
                "database": "inaccessible",
                "message": f"Health check failed: {str(e)}"
            }
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected


# Global Supabase client instance
supabase_client = SupabaseClient() 