import asyncio
import io
import time
from typing import List
from uuid import uuid4

from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.extractors import TitleExtractor
from pinecone import Pinecone

from kb_ingestion.models.config import PipelineConfig
from kb_ingestion.models.requests import FileWrapper
from kb_ingestion.models.results import IngestionResult
from kb_ingestion.interfaces.ingestion import IIngestionPipeline
from llama_cloud_services import LlamaParse
from llama_cloud_services.parse.types import JobResult



class LlamaIndexDocumentIngestionToPinecone(IIngestionPipeline):
    def __init__(self, config: PipelineConfig, vector_store: PineconeVectorStore, document_parser: LlamaParse):
        self.config = config
        self.vector_store = vector_store
        
        # Initialize the ingestion pipeline 
        self.pipeline = IngestionPipeline(
            transformations=[
                SentenceSplitter(
                    chunk_size=config.chunk_size,
                    chunk_overlap=config.chunk_overlap,
                ),
                OpenAIEmbedding(
                    api_key=config.embedding_config.api_key,
                    model=config.embedding_config.model_name,
                ),
            ],
            vector_store=self.vector_store,
        )
        self.document_parser = document_parser

    async def ingest(self, source: FileWrapper) -> IngestionResult:
        """Ingest a single file using LlamaIndex pipeline."""
        start_time = time.time()
        
        try:
            # Create a Document from the FileWrapper
            documents = await self._parse_document(source)
            
            # Run the ingestion pipeline
            nodes = await self.pipeline.arun(documents=documents)
            
            # Extract node IDs
            node_ids = [node.node_id for node in nodes if hasattr(node, 'node_id')]
            
            processing_time = time.time() - start_time
            
            return IngestionResult(
                success=True,
                source_id=source.filename,
                chunk_ids=node_ids,
                metadata={
                    "source_file": source.filename,
                    "content_type": source.content_type,
                    "file_size": source.size,
                    "nodes_created": len(nodes),
                    **source.metadata,
                },
                processing_time_seconds=processing_time,
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return IngestionResult(
                success=False,
                source_id=source.filename,
                chunk_ids=[],
                metadata={
                    "source_file": source.filename,
                    "content_type": source.content_type,
                    "file_size": source.size,
                    **source.metadata,
                },
                processing_time_seconds=processing_time,
                error=e
            )

    async def validate_source(self, source: FileWrapper) -> bool:
        """Validate if the source file can be processed."""
        try:
            # Check file size
            if source.size > self.config.max_file_size_mb * 1024 * 1024:
                return False
            
            # Check content type if specified
            allowed_types = self.config.supported_file_types
            if allowed_types and source.content_type not in allowed_types:
                return False
            
            # Try to read content to ensure it's accessible
            content = source.get_content_as_text()
            if not content or len(content.strip()) == 0:
                return False
            
            return True
            
        except Exception:
            return False

    def _create_document_from_file(self, source: FileWrapper) -> Document:
        """Create a LlamaIndex Document from a FileWrapper."""
        # Get text content from the file
        text_content = source.content
        
        # Create metadata
        metadata = {
            "file_name": source.filename,
            "file_size": source.size,
            "content_type": source.content_type,
            **source.metadata,
        }
        
        # Generate a unique document ID
        doc_id = str(uuid4())
        
        return Document(
            text=text_content,
            metadata=metadata,
            id_=doc_id,
        )
    
    async def _parse_document(self, source: FileWrapper) -> List[Document]:
        """Parse the document using LlamaParse."""
        bytes = source.content
        result: JobResult = await self.document_parser.aparse(bytes, extra_info={"file_name": source.filename})
        return await result.aget_markdown_documents()