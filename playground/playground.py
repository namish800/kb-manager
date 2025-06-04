import nest_asyncio

nest_asyncio.apply()

import os

os.environ["OPENAI_API_KEY"] = ""

from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader("./data/paul_graham/").load_data()

from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import TokenTextSplitter
from llama_index.core.extractors import TitleExtractor
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.vector_stores.pinecone import PineconeVectorStore

from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="")

index_name = "llama-integration-example"

# pc.create_index(
#     index_name,
#     dimension=1536,
#     spec=ServerlessSpec(cloud="aws", region="us-east-1"),
# )

pinecone_index = pc.Index(index_name)

vector_store = PineconeVectorStore(pinecone_index=pinecone_index)

nodes_embedding_cache = IngestionCache.from_persist_path(
    "./nodes_embedding.json"
)

pipeline = IngestionPipeline(
    transformations=[
        TokenTextSplitter(chunk_size=1024, chunk_overlap=100),
        TitleExtractor(),
        OpenAIEmbedding(),
    ],
    vector_store=vector_store,
    cache=nodes_embedding_cache, 
)

# Will load it from the cache as the transformations are same.
pipeline.run(documents=documents)

print(pinecone_index.describe_index_stats())

from llama_index.core import VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever

# Instantiate VectorStoreIndex object from your vector_store object
vector_index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

# Grab 5 search results
retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=5)