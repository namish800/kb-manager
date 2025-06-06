import asyncio
import os

from kb_ingestion import LlamaIndexDocumentIngestionToPinecone
from kb_ingestion.llamaindex_website_ingestion import LlamaIndexWebsiteIngestionToPinecone
from kb_ingestion.models.config import EmbeddingConfig, PipelineConfig, VectorStoreConfig as IngestionVectorStoreConfig
from kb_ingestion.models.requests import FileWrapper, WebsiteWrapper

from kb_retriever.llamaindex_document_retrieval import LlamaIndexDocumentRetrievalFromPinecone
from kb_retriever.models.retrieval import (
    EmbeddingConfig as RetrievalEmbeddingConfig,
    QueryRequest,
    RetrievalConfig,
    VectorStoreConfig,
)
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from firecrawl import FirecrawlApp




def get_pinecone_vs():
    # Initialize Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    pinecone_index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
    vector_store = PineconeVectorStore(
        pinecone_index=pinecone_index,
        namespace=os.getenv("PINECONE_NAMESPACE") or None
    )
    return vector_store

def get_firecrawl_reader():
    return FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

async def document_ingestion_example(vector_store: PineconeVectorStore):
    """Example of document ingestion to Pinecone."""
    print("Running ingestion example...")
    
    # Configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    embedding_config = EmbeddingConfig(
        api_key=openai_api_key, 
        model_name="text-embedding-ada-002"
    )
    
    config = PipelineConfig(
        embedding_config=embedding_config,
        chunk_size=1024,
        chunk_overlap=100
    )
    
    # Initialize pipeline
    pipeline = LlamaIndexDocumentIngestionToPinecone(
        config, 
        vector_store=vector_store
    )
    
    # Sample file
    file = FileWrapper(
        filename="hello.txt",
        content_type="text/plain",
        size=1024,
        content="Hello, world! This is a sample document for testing knowledge base ingestion."
    )
    
    # Ingest file
    result = await pipeline.ingest(file)
    print(f"Ingestion result: {result}")


async def website_ingestion_example(vector_store: PineconeVectorStore, firecrawl_reader: FirecrawlApp):
    """Example of website ingestion to Pinecone."""
    print("Running website ingestion example...")
    
    # Configuration 
    openai_api_key = os.getenv("OPENAI_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    
    embedding_config = EmbeddingConfig(
        api_key=openai_api_key, 
        model_name="text-embedding-ada-002")
    
    config = PipelineConfig(
        embedding_config=embedding_config,
        chunk_size=1024,
        chunk_overlap=100
    )
    
    # Initialize pipeline
    pipeline = LlamaIndexWebsiteIngestionToPinecone(
        config=config, 
        vector_store=vector_store,
        firecrawl_reader=firecrawl_reader
    )
    
    # Sample file
    file = WebsiteWrapper(
        urls=["https://www.sarvam.ai/blogs/sarvam-m",
               "https://www.sarvam.ai/blogs/building-a-sovereign-ai-ecosystem-for-india",
               "https://www.sarvam.ai/blogs/indias-sovereign-llm"]
    )
    
    # Ingest file
    result = await pipeline.ingest(file)
    print(f"Ingestion result: {result}")
    


async def retrieval_example(vector_store: PineconeVectorStore):
    """Example of document retrieval from Pinecone."""
    print("Running retrieval example...")
    
    # Configuration
    config = RetrievalConfig(
        embedding_config=RetrievalEmbeddingConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-ada-002",
        )
    )
    
    # Initialize retrieval pipeline
    retrieval_pipeline = LlamaIndexDocumentRetrievalFromPinecone(config, vector_store)
    
    # Create query request
    query_request = QueryRequest(
        query="What is Sarvam-m?",
        similarity_top_k=2,
        similarity_threshold=0.7,
    )
    
    # Retrieve documents
    result = await retrieval_pipeline.retrieve(query_request)
    print(f"Retrieval result: {result}")


async def main():
    """Main function to run examples."""
    print("KB Management System Examples")
    print("=" * 40)

    vector_store = get_pinecone_vs()
    firecrawl_reader = get_firecrawl_reader()
    
    # Run document ingestion example
    # await document_ingestion_example(vector_store)
    # print()
    
    # Run website ingestion example
    # await website_ingestion_example(vector_store, firecrawl_reader)
    # print()
    
    # # Run retrieval example
    await retrieval_example(vector_store)


if __name__ == "__main__":
    asyncio.run(main())


