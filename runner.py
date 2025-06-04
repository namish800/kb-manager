import asyncio
import os
from kb_ingestion import LlamaIndexDocumentIngestionToPinecone
from kb_ingestion.models.config import EmbeddingConfig, PipelineConfig
from kb_ingestion.models.requests import FileWrapper


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


asyncio.run(ingest_file())


