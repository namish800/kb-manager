"""Database setup and initialization."""

import logging

from kb_event_handler.common.repositories import (
    file_repository,
    job_repository,
    knowledge_base_repository,
    tenant_repository,
)
from kb_event_handler.common.supabase_client import supabase_client


logger = logging.getLogger(__name__)


async def init_database() -> None:
    """Initialize database connections and perform startup checks."""
    try:
        logger.info("Initializing database connections...")
        
        # Connect to Supabase
        await supabase_client.connect()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_database() -> None:
    """Close database connections and cleanup."""
    try:
        logger.info("Closing database connections...")
        
        # Disconnect from Supabase
        await supabase_client.disconnect()
        
        logger.info("Database connections closed successfully")
        
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


async def health_check_database() -> dict:
    """Perform database health check."""
    try:
        return await supabase_client.health_check()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "database": "inaccessible",
            "message": f"Health check failed: {str(e)}"
        }


# Export repositories for dependency injection
__all__ = [
    "init_database",
    "close_database", 
    "health_check_database",
    "supabase_client",
    "tenant_repository",
    "job_repository",
    "knowledge_base_repository",
    "file_repository",
] 