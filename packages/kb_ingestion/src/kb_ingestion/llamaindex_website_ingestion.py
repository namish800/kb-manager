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
from firecrawl import FirecrawlApp

from kb_ingestion.models.config import PipelineConfig
from kb_ingestion.models.requests import WebsiteWrapper
from kb_ingestion.models.results import IngestionResult
from kb_ingestion.interfaces.ingestion import IIngestionPipeline

class LlamaIndexWebsiteIngestionToPinecone(IIngestionPipeline):
    def __init__(self, config: PipelineConfig, vector_store: PineconeVectorStore, firecrawl_reader: FirecrawlApp):
        self.config = config
        self.vector_store = vector_store
        self.firecrawl_reader = firecrawl_reader
        
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


    async def ingest(self, source: WebsiteWrapper) -> IngestionResult:
        """Ingest a website using LlamaIndex pipeline."""
        start_time = time.time()
        
        try:
            # Create a Document from the WebsiteWrapper
            documents = self._create_document_from_website(source)
            
            # Run the ingestion pipeline
            nodes = await self.pipeline.arun(documents=documents)
            
            # Extract node IDs
            node_ids = [node.node_id for node in nodes if hasattr(node, 'node_id')]
            
            processing_time = time.time() - start_time
            
            return IngestionResult(
                success=True,
                source_id=str(uuid4()),
                chunk_ids=node_ids,
                metadata={
                    "urls": source.urls,
                    "nodes_created": len(nodes),
                    **source.metadata,
                },
                processing_time_seconds=processing_time,
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return IngestionResult(
                success=False,
                source_id=str(uuid4()),
                chunk_ids=[],
                metadata={
                    "urls": source.urls,
                    **source.metadata,
                },
                processing_time_seconds=processing_time,
                error=e
            )

    async def validate_source(self, source: WebsiteWrapper) -> bool:
        """Validate if the source website can be processed."""
        try:
            # urls should be a list of valid urls
            for url in source.urls:
                if not url.startswith("http"):
                    return False
            return True
        except Exception:
            return False

    def _create_document_from_website(self, source: WebsiteWrapper) -> List[Document]:
        """Create a LlamaIndex Document from a WebsiteWrapper."""

        # Load documents by providing a list of URLs to extract data from
        documents = []
        for url in source.urls:
            scrape_result = self.firecrawl_reader.scrape_url(url, formats=['markdown', 'html'])
            documents.append(Document(text=scrape_result.markdown, metadata=scrape_result.metadata))
        return documents