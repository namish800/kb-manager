from typing import Dict
from kb_event_handler.ingestion.interfaces.ipipeline_factory import IIngestionPipelineFactory
from kb_ingestion.interfaces.ingestion import IIngestionPipeline

class IngestionPipelineFactory(IIngestionPipelineFactory):
    """Factory for creating ingestion pipelines."""

    def __init__(self, pipelines_map: Dict[str, IIngestionPipeline]):
        self.pipelines_map = pipelines_map

    def get_pipeline(self, resource_type: str) -> IIngestionPipeline:
        """Get an ingestion pipeline instance."""
        if resource_type not in self.pipelines_map:
            raise ValueError(f"No pipeline found for resource type: {resource_type}")
        return self.pipelines_map[resource_type]

