from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional    
from kb_event_handler.ingestion.schemas import IngestionResult

class IIngestionService(ABC):

    @abstractmethod
    async def ingest_resource(self, job_id: int,
                                resource_type: str,
                                tenant_id: int,
                                knowledge_base_id: int,
                                urls: Optional[List[str]] = None,
                                file_path: Optional[str] = None,
                                filename: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None,) -> IngestionResult:
        """Ingest a resource into the knowledge base."""
        pass
