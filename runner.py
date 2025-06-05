import asyncio
import os
from kb_ingestion import LlamaIndexDocumentIngestionToPinecone
from kb_ingestion.models.config import EmbeddingConfig, PipelineConfig
from kb_ingestion.models.requests import FileWrapper
from kb_retriever.llamaindex_document_retrieval import LlamaIndexDocumentRetrievalFromPinecone


openai_api_key = os.getenv("OPENAI_API_KEY")
embedding_config = EmbeddingConfig(api_key=openai_api_key, model_name="text-embedding-ada-002")

config = PipelineConfig(
    embedding_config=embedding_config,
    chunk_size=1024,
    chunk_overlap=100)
pc_api_key = os.getenv("PINECONE_API_KEY")
pipeline = LlamaIndexDocumentIngestionToPinecone(config, api_key=pc_api_key, index_name="llama-integration-example")

file = FileWrapper(
    filename="hello.txt",
    content_type="text/plain",
    size=1024,
    content="Hello, world!"
)

async def ingest_file():
    result = await pipeline.ingest(file)
    print(result)

import asyncio
import os

from kb_retriever.models.retrieval import (
    EmbeddingConfig,
    QueryRequest,
    RetrievalConfig,
    VectorStoreConfig,
)
from kb_retriever.llamaindex_document_retrieval import LlamaIndexDocumentRetrievalFromPinecone


async def retrieve_chunk():
    """Demonstrate basic retrieval functionality."""
    
    # Configuration
    config = RetrievalConfig(
        embedding_config=EmbeddingConfig(
            api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key"),
            model_name="text-embedding-ada-002",
        ),
        vector_store_config=VectorStoreConfig(
            api_key=os.getenv("PINECONE_API_KEY", "your-pinecone-api-key"),
            index_name="llama-integration-example"
        ),
    )
    
    # Initialize retrieval pipeline
    retrieval_pipeline = LlamaIndexDocumentRetrievalFromPinecone(config)
    
    # Create a query request
    query_request = QueryRequest(
        query="What is the main topic of Paul Graham's essay?",
        similarity_top_k=5,
        similarity_threshold=0.7,
    )

    result = await retrieval_pipeline.retrieve(query_request)
    print(result)


asyncio.run(retrieve_chunk())


