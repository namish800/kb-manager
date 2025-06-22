"""KB Event Handler - FastAPI service for knowledge base ingestion operations."""

from .main import app, create_app
from .config import settings

__version__ = "0.1.0"

__all__ = ["app", "create_app", "settings", "__version__"]
