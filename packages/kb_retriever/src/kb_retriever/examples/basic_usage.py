"""Basic usage example for kb_retriever package."""

import asyncio
import os

from kb_retriever.models.retrieval import (
    EmbeddingConfig,
    QueryRequest,
    RetrievalConfig,
    VectorStoreConfig,
)
from kb_retriever.llamaindex_document_retrieval import LlamaIndexDocumentRetrievalFromPinecone


async def main():
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
    
    # Validate query
    is_valid = await retrieval_pipeline.validate_query(query_request)
    print(f"Query validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    if not is_valid:
        return
    
    # Perform retrieval
    print(f"\nSearching for: '{query_request.query}'")
    print("-" * 50)
    
    result = await retrieval_pipeline.retrieve(query_request)
    
    if result.success:
        print(f"✓ Found {len(result.nodes)} relevant chunks in {result.processing_time_seconds:.2f}s")
        print(f"Sources: {', '.join(result.get_sources())}")
        
        # Display retrieved nodes
        for i, node in enumerate(result.nodes, 1):
            print(f"\n--- Result {i} (Score: {node.similarity_score:.3f}) ---")
            print(f"Source: {node.get_source_reference()}")
            print(f"Content: {node.content[:200]}...")
            
            # Show citation info
            citation = node.get_citation_info()
            print(f"Citation: {citation['source_file']} (Node: {citation['node_id'][:8]}...)")
        
        # Show citation summary
        print("\n" + "="*50)
        citation_summary = result.get_citation_summary()
        print("Citation Summary:")
        print(f"- Total chunks: {citation_summary['total_nodes']}")
        print(f"- Average similarity: {citation_summary['avg_similarity']:.3f}")
        print(f"- Sources: {len(citation_summary['sources'])}")
        print(f"- Processing time: {citation_summary['processing_time']:.2f}s")
        
    else:
        print(f"✗ Retrieval failed: {result.error}")


if __name__ == "__main__":
    asyncio.run(main()) 