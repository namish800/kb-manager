"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import configure_logging, settings
from .database import close_database, init_database
from .exceptions import (
    KBEventHandlerException,
    general_exception_handler,
    http_exception_handler,
    kb_event_handler_exception_handler,
)
from .health import router as health_router
from .ingestion import router as ingestion_router
from .middleware import CorrelationIdMiddleware, RequestLoggingMiddleware


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting KB Event Handler API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API Version: {settings.api_version}")
    
    try:
        # Initialize database connections
        await init_database()
        logger.info("Database initialization completed")
        
        # TODO: Add other startup checks in future phases
        # - OpenAI API key validation (Phase 4)
        # - Pinecone connection test (Phase 4)
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down KB Event Handler API")
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Configure logging first
    configure_logging()
    
    # Determine if docs should be shown
    show_docs = settings.environment in ["development", "staging"]
    
    app = FastAPI(
        title="KB Event Handler API",
        description="FastAPI service for knowledge base ingestion operations",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url=f"/openapi.json" if show_docs else None,
        docs_url=f"/docs" if show_docs else None,
        redoc_url=f"/redoc" if show_docs else None,
    )
    
    # Add middleware (order matters - added in reverse order of execution)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Request logging middleware (executes after correlation ID middleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Correlation ID middleware (executes first)
    app.add_middleware(CorrelationIdMiddleware)
    
    # Add exception handlers
    app.add_exception_handler(KBEventHandlerException, kb_event_handler_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    # Include routers
    app.include_router(
        health_router,
        prefix=f"/api/{settings.api_version}",
    )
    
    app.include_router(
        ingestion_router,
        prefix=f"/api/{settings.api_version}",
    )
    
    # Root redirect
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint that redirects to health check."""
        return {"message": "KB Event Handler API", "health": f"/api/{settings.api_version}/health"}
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    ) 