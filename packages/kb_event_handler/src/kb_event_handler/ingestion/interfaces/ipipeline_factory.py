from abc import ABC, abstractmethod

from kb_ingestion.interfaces.ingestion import IIngestionPipeline

class IIngestionPipelineFactory(ABC):
    """Factory interface for creating ingestion pipelines."""

    @abstractmethod
    def get_pipeline(self) -> IIngestionPipeline:
        """Get an ingestion pipeline instance."""
        pass
