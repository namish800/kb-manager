# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

Knowledge base management system with UV workspace containing three specialized packages:
- **kb_ingestion**: Document and website ingestion pipeline using LlamaIndex and LlamaParse
- **kb_retriever**: Document retrieval and search functionality with Pinecone vector store
- **kb_event_handler**: FastAPI service providing REST API endpoints for ingestion operations

## Core Development Commands

### UV Workspace Commands (run from root only)
```bash
# Sync all dependencies
uv sync

# Run the main example/runner script
uv run python runner.py

# Run FastAPI service
uv run --package kb-event-handler python -m kb_event_handler.main

# Add dependencies to specific packages
uv add --package kb-ingestion "new-dependency>=1.0.0"
uv add --package kb-retriever "new-dependency>=1.0.0"
uv add --package kb-event-handler "new-dependency>=1.0.0"

# Run tests for specific package
uv run --package kb-ingestion python -m pytest
uv run --package kb-retriever python -m pytest
uv run --package kb-event-handler python -m pytest

# Run all tests
uv run python -m pytest packages/

# Build packages
uv build --package kb-ingestion
uv build --package kb-retriever
uv build --package kb-event-handler
```

**Critical**: Always run UV commands from the root directory to avoid dependency conflicts. Running `uv sync` from package directories can break the workspace.

### FastAPI Development
```bash
# Development server with auto-reload
uv run --package kb-event-handler python packages/kb_event_handler/run_dev.py

# Production server
uv run --package kb-event-handler python -m kb_event_handler.main
```

## Architecture Patterns

### Interface-Based Design
All packages follow SOLID principles with interfaces in `interfaces/` directories:
- Interface naming: `I[ComponentName]` (e.g., `IIngestionPipeline`, `IRetrievalPipeline`)
- Concrete implementations: Descriptive names indicating tech stack (e.g., `LlamaIndexDocumentIngestionToPinecone`)

### Data Models Structure
Models are organized in `models/` directories:
- **Requests**: Input structures (`QueryRequest`, `BatchRequest`, `FileWrapper`, `WebsiteWrapper`)
- **Results**: Output structures (`IngestionResult`, `RetrievalResult`)
- **Config**: Configuration classes with validation (`PipelineConfig`, `RetrievalConfig`)

### Dependency Injection Pattern
- Components receive dependencies at instantiation, not per operation
- Configuration passed to constructors
- External services (vector stores, embedding models) injected as dependencies

### Package Structure
```
packages/[package_name]/src/[package_name]/
├── interfaces/           # Abstract interfaces  
├── models/              # Data models (requests, results, config)
├── [implementation].py  # Concrete implementations
└── __init__.py         # Public API exports
```

## Technology Stack Integration

### LlamaIndex Dependencies
- Use umbrella package `llama-index>=0.12.40` for main functionality
- Add specific packages for specialized components (e.g., `llama-index-vector-stores-pinecone`)
- Use `arun()` for native async processing, avoid `asyncio.to_thread()` unless necessary

### Vector Store Integration
- Initialize Pinecone externally and inject as dependency
- Support namespacing for multi-tenant scenarios
- Abstract vector store specifics behind interfaces

### External Services
- **LlamaParse**: Document parsing service (PDFs, etc.)
- **Firecrawl**: Website scraping and content extraction
- **OpenAI**: Embedding generation
- **Pinecone**: Vector storage and similarity search

## Environment Variables Required

```bash
OPENAI_API_KEY=sk-...
LLAMA_CLOUD_API_KEY=llx-...
LLAMA_PARSE_API_KEY=llx-...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=...
PINECONE_NAMESPACE=  # Optional
FIRECRAWL_API_KEY=...
```

## FastAPI Service Details

Main application: `packages/kb_event_handler/src/kb_event_handler/main.py`
- Runs on configurable host/port via settings
- Includes CORS, request logging, and correlation ID middleware
- Health check endpoint: `/api/v1/health`
- Ingestion endpoints: `/api/v1/ingestion/`
- Auto-generated docs available in development mode at `/docs`

## Development Guidelines

### Async Patterns
- All ingestion and retrieval operations are async
- Use concurrent processing for batch operations
- Return structured result objects with success/failure indicators

### Error Handling
- Custom exception hierarchy in each package
- Include detailed error messages and metadata in results
- Use structured logging for debugging

### Testing
- Package-specific tests in each `packages/[name]/tests/` directory
- Examples available in `runner.py` and package `examples/` directories
- Integration tests require valid API keys in environment