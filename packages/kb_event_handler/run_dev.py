#!/usr/bin/env python3
"""Development runner for KB Event Handler API."""

import os
import sys
from pathlib import Path

# Add the package to Python path for development
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# # Set development environment variables if not set
# os.environ.setdefault("ENVIRONMENT", "development")
# os.environ.setdefault("API_SECRET_KEY", "dev-secret-key-change-in-production")
# os.environ.setdefault("SUPABASE_URL", "https://your-project.supabase.co")
# os.environ.setdefault("SUPABASE_SERVICE_KEY", "your-service-key")
# os.environ.setdefault("OPENAI_API_KEY", "sk-your-openai-key")
# os.environ.setdefault("PINECONE_API_KEY", "your-pinecone-key")
# os.environ.setdefault("PINECONE_INDEX_NAME", "kb-management")
# os.environ.setdefault("LOG_LEVEL", "INFO")
# os.environ.setdefault("LOG_FORMAT", "text")  # Use text format for development

if __name__ == "__main__":
    import uvicorn
    from kb_event_handler import app, settings
    
    print(f"🚀 Starting KB Event Handler API in {settings.environment} mode")
    print(f"📖 API Documentation: http://{settings.api_host}:{settings.api_port}/api/{settings.api_version}/docs")
    print(f"❤️  Health Check: http://{settings.api_host}:{settings.api_port}/api/{settings.api_version}/health")
    print(f"🔍 Environment: {settings.environment}")
    print()
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    ) 