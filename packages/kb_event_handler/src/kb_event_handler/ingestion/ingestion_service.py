"""Ingestion service for processing files using the kb_ingestion pipeline."""

import logging
import os
import time
from typing import List, Optional, Dict, Any

from kb_event_handler.common.temp_file_manager import TempFileManager
from kb_event_handler.ingestion.interfaces.ingestion_service import IIngestionService
from kb_event_handler.ingestion.schemas import IngestionResult
from kb_event_handler.ingestion.interfaces.ipipeline_factory import IIngestionPipelineFactory
from kb_ingestion.interfaces.ingestion import IIngestionPipeline
from kb_ingestion.models import IngestionResult as PipelineIngestionResult

logger = logging.getLogger(__name__)

class DocumentIngestionService(IIngestionService):
    """Service for ingesting documents into the knowledge base."""

    def __init__(self, pipeline_factory: IIngestionPipelineFactory, temp_file_manager: TempFileManager):
        self.pipeline_factory = pipeline_factory
        self.temp_file_manager = temp_file_manager

    async def ingest_resource(self, job_id: int, 
                              resource_type: str, 
                              tenant_id: int, 
                              knowledge_base_id: int, 
                              urls: Optional[List[str]] = None,
                              file_path: Optional[str] = None,
                              filename: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> IngestionResult:
        
        """Ingest a document into the knowledge base."""
        start_time = time.time()

        try:
            logger.info(f"Starting ingestion for file: {filename} (tenant: {tenant_id}, kb: {knowledge_base_id})")
            
            # Step 2: Download file to temporary location
            logger.info(f"Downloading file for job {job_id}: {file_path}")
            
            # Step 3: Process file through ingestion pipeline
            async with self.temp_file_manager.temp_file_context(file_path, filename) as temp_path:
                
                logger.info(f"Processing file through ingestion pipeline for job {job_id}")
                
                # Step 4: Get the pipeline
                pipeline: IIngestionPipeline = self.pipeline_factory.get_pipeline(resource_type)
                
                # Step 5: Create the file wrapper
                from kb_ingestion.models import FileWrapper


                file_wrapper = FileWrapper(
                    filename=filename,
                    content_type=metadata.get("mime_type", "application/pdf"),
                    size=os.path.getsize(temp_path),
                    content=open(temp_path, "rb").read(),
                    metadata={
                        "tenant_id": tenant_id,
                        "knowledge_base_id": knowledge_base_id,
                        "original_filename": filename,
                        **(metadata or {})
                    }
                )

                ingestion_result: PipelineIngestionResult = await pipeline.ingest(file_wrapper)

                processing_time = time.time() - start_time
            
                # Convert to our schema
                result = IngestionResult(
                    success=ingestion_result.success,
                    node_count=len(ingestion_result.chunk_ids) if ingestion_result.chunk_ids else 0,
                    processing_time_seconds=processing_time,
                    error_message=str(ingestion_result.error) if not ingestion_result.success and ingestion_result.error else None,
                    metadata={
                        "node_ids": ingestion_result.chunk_ids,
                        "tenant_id": tenant_id,
                        "knowledge_base_id": knowledge_base_id,
                        **ingestion_result.metadata
                    }
                )
                
                if result.success:
                    logger.info(f"Successfully ingested {filename}: {result.node_count} chunks in {processing_time:.2f}s")
                else:
                    logger.error(f"Failed to ingest {filename}: {result.error_message}")
                
                return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"Ingestion failed for {filename}: {str(e)}"
            logger.error(error_message)
            
            return IngestionResult(
                success=False,
                node_count=0,
                processing_time_seconds=processing_time,
                error_message=error_message,
                metadata={
                    "tenant_id": tenant_id,
                    "knowledge_base_id": knowledge_base_id,
                    "error_type": type(e).__name__,
                    **(metadata or {})
                }
            )

class WebsiteIngestionService(IIngestionService):
    """Service for ingesting websites into the knowledge base."""

    def __init__(self, pipeline_factory: IIngestionPipelineFactory):
        self.pipeline_factory = pipeline_factory

    async def ingest_resource(self, job_id: int, 
                              resource_type: str, 
                              tenant_id: int,   
                              knowledge_base_id: int,
                              urls: Optional[List[str]] = None,
                              file_path: Optional[str] = None,
                              filename: Optional[str] = None, 
                              metadata: Optional[Dict[str, Any]] = None) -> IngestionResult:
        """Ingest a website into the knowledge base."""
            
        return IngestionResult(
            success=True,
            node_count=0,
            processing_time_seconds=0,
            error_message="Not implemented",
            metadata={}
        )

