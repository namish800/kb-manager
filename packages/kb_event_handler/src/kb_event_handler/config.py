"""Global configuration management using Pydantic BaseSettings."""

import logging
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings."""

    # API Configuration
    api_secret_key: str = Field(..., description="Shared secret API key")
    api_version: str = Field(default="v1", description="API version")
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment name"
    )

    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_service_key: str = Field(..., description="Supabase service role key")
    supabase_storage_bucket: str = Field(default="files", description="Supabase storage bucket name")

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")

    # Pinecone Configuration
    pinecone_api_key: str = Field(..., description="Pinecone API key")
    pinecone_index_name: str = Field(..., description="Pinecone index name")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: Literal["json", "text"] = Field(
        default="json", description="Log format"
    )

    # File Processing Configuration
    max_file_size_mb: int = Field(default=25, description="Maximum file size in MB")
    temp_dir: str = Field(default="/tmp", description="Temporary directory for file processing")
    
    # Ingestion Pipeline Configuration
    chunk_size: int = Field(default=1024, description="Text chunk size for processing")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")
    embedding_model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model")
    embedding_dimensions: int = Field(default=1536, description="Embedding vector dimensions")
    
    # Processing Limits
    max_concurrent_jobs: int = Field(default=3, description="Maximum concurrent ingestion jobs")
    job_timeout_minutes: int = Field(default=30, description="Job timeout in minutes")
    
    # Vector Store Configuration
    pinecone_environment: str = Field(default="gcp-starter", description="Pinecone environment")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def configure_logging() -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.log_level.upper())
    
    if settings.log_format == "json":
        from pythonjsonlogger import jsonlogger
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING) 