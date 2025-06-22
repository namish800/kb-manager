"""KB Event Handler - FastAPI service for knowledge base ingestion operations."""

from kb_event_handler.main import app, create_app
from kb_event_handler.config import settings

__version__ = "0.1.0"

__all__ = ["app", "create_app", "settings", "__version__"]
