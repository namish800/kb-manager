# KB Retriever

A production-ready knowledge base retrieval component built with LlamaIndex and Pinecone, designed following SOLID principles for semantic document search.

## Features

- 🔍 **Semantic Search**: Advanced vector-based document retrieval using OpenAI embeddings
- 📄 **Citation Support**: Built-in citation tracking and source reference generation
- ⚡ **Async Ready**: Full async/await support for optimal performance
- 🔧 **Configurable**: Flexible configuration with similarity thresholds and filtering
- 🏗️ **SOLID Architecture**: Interface-based design with dependency injection ready
- 🔗 **Framework Independent**: Custom abstractions that don't leak LlamaIndex specifics
- 🚀 **Extensible**: Designed for future query engine capabilities

## Architecture

The component follows a clean architecture with:

- **Interface**: `IRetrievalPipeline` for dependency inversion
- **Data Models**: `QueryRequest`, `RetrievalResult`, `RetrievedNode` with citation support
- **Configuration**: Separate config classes for embedding and vector store settings
- **Implementation**: `LlamaIndexDocumentRetrievalFromPinecone` using LlamaIndex + Pinecone

## Installation

```bash
# Install the package (assumes UV workspace setup)
uv add kb-retriever

# Or install dependencies manually
pip install llama-index-core llama-index-embeddings-openai llama-index-vector-stores-pinecone pinecone-client openai pydantic
```

## Quick Start

```python
import asyncio
from kb_retriever import (
    EmbeddingConfig,
    LlamaIndexDocumentRetrievalFromPinecone,
    QueryRequest,
    RetrievalConfig,
    VectorStoreConfig,
)

async def search_documents():
    # Configure retrieval pipeline
    config = RetrievalConfig(
        embedding_config=EmbeddingConfig(
            api_key="your-openai-api-key",
            model_name="text-embedding-3-small",
        ),
        vector_store_config=VectorStoreConfig(
            api_key="your-pinecone-api-key",
            index_name="your-index-name",
            namespace="default",
        ),
    )
    
    # Initialize retrieval pipeline
    retrieval = LlamaIndexDocumentRetrievalFromPinecone(config)
    
    # Create query
    query = QueryRequest(
        query="What is machine learning?",
        similarity_top_k=5,
        similarity_threshold=0.7,
    )
    
    # Retrieve results
    result = await retrieval.retrieve(query)
    
    if result.success:
        print(f"Found {len(result.nodes)} relevant chunks")
        for node in result.nodes:
            print(f"Source: {node.get_source_reference()}")
            print(f"Content: {node.content[:200]}...")
            print(f"Score: {node.similarity_score:.3f}\n")
    else:
        print(f"Search failed: {result.error}")

# Run the search
asyncio.run(search_documents())
```

## Citation Support

The component provides comprehensive citation support for RAG applications:

```python
# Get citation information for each node
for node in result.nodes:
    citation = node.get_citation_info()
    print(f"Source: {citation['source_file']}")
    print(f"Node ID: {citation['node_id']}")
    print(f"Similarity: {citation['similarity_score']:.3f}")

# Get formatted source references
source_ref = node.get_source_reference()  # "document.pdf (Page 5)"

# Get content with metadata context
content_with_source = node.get_content_with_metadata()
# "[Source: document.pdf (Page 5)]\nActual content here..."

# Get overall citation summary
summary = result.get_citation_summary()
print(f"Total sources: {len(summary['sources'])}")
print(f"Average similarity: {summary['avg_similarity']:.3f}")
```

## Configuration Options

### RetrievalConfig

```python
config = RetrievalConfig(
    embedding_config=EmbeddingConfig(...),
    vector_store_config=VectorStoreConfig(...),
    
    # Retrieval defaults
    default_similarity_top_k=10,
    default_similarity_threshold=0.7,
    default_query_mode="default",  # "default", "sparse", "hybrid"
    
    # Performance settings
    request_timeout_seconds=30.0,
    max_retries=3,
    
    # Postprocessing options
    enable_similarity_filter=True,
    similarity_cutoff=0.7,
)
```

### QueryRequest

```python
query = QueryRequest(
    query="Your search query",
    similarity_top_k=10,
    similarity_threshold=0.7,
    metadata_filters={"category": "technical"},
    namespace="documents",
    query_mode="default",
)
```

## Advanced Usage

### Filtering Results

```python
# Filter by similarity threshold
high_quality_nodes = result.filter_by_similarity(0.8)

# Get top N results
top_nodes = result.get_top_nodes(3)

# Get unique sources
sources = result.get_sources()
```

### Query Validation

```python
# Validate query before retrieval
is_valid = await retrieval.validate_query(query)
if not is_valid:
    print("Invalid query parameters")
```

### Error Handling

```python
result = await retrieval.retrieve(query)

if not result.success:
    print(f"Retrieval failed: {result.error}")
    print(f"Processing time: {result.processing_time_seconds:.2f}s")
```

## Integration with KB Ingestion

This retrieval component is designed to work seamlessly with the `kb-ingestion` package:

```python
# Ingest documents first
from kb_ingestion import LlamaIndexDocumentIngestionToPinecone, PipelineConfig

# Then retrieve from the same index
from kb_retriever import LlamaIndexDocumentRetrievalFromPinecone, RetrievalConfig
```

## Future Extensibility

The architecture is designed for future query engine capabilities:

```python
# Future: Query engine with LLM response synthesis
# from kb_retriever import IQueryEngine, QueryEngineRequest

# query_engine = LlamaIndexQueryEngine(config)
# response = await query_engine.query(request)  # Returns synthesized answer
```

## Examples

See the `examples/` directory for more comprehensive usage examples:

- `basic_usage.py` - Simple retrieval example
- `advanced_filtering.py` - Advanced filtering and postprocessing
- `citation_demo.py` - Citation and source reference examples

## Requirements

- Python 3.12+
- OpenAI API key (for embeddings)
- Pinecone API key (for vector storage)
- Pre-populated Pinecone index with documents

## Architecture Philosophy

This component follows SOLID principles:

- **S**ingle Responsibility: Each class has one clear purpose
- **O**pen/Closed: Extensible without modifying existing code
- **L**iskov Substitution: Interface implementations are interchangeable
- **I**nterface Segregation: Clean, focused interfaces
- **D**ependency Inversion: Depends on abstractions, not concretions
