# KB Management System

A knowledge base management system with document ingestion and retrieval capabilities.

## Project Structure

This is a UV workspace with multiple packages:

```
kb-management/                 # Root workspace
├── packages/
│   ├── kb_ingestion/         # Document ingestion package (PDF/text processing)
│   ├── kb_retriever/         # Document retrieval package (search/query)
│   └── kb_event_handler/     # FastAPI service package (API endpoints)
├── pyproject.toml            # Root workspace configuration
└── uv.lock                   # Unified lock file
```

## Development Setup

### ⚠️ Important: UV Workspace Commands

**Always run UV commands from the root directory** to avoid dependency conflicts:

```bash
# ✅ Correct - from root directory
cd kb-management/
uv sync                                    # Sync all packages
uv add --package kb-ingestion llama-parse  # Add dependency to specific package
uv run python runner.py                   # Run scripts

# ❌ Incorrect - from package directory
cd packages/kb_ingestion/
uv sync                                    # Can break dependencies!
```

### Initial Setup

```bash
# Clone and setup
git clone <repo-url>
cd kb-management

# Install all dependencies
uv sync

# Set environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Adding Dependencies

```bash
# Add to specific package
uv add --package kb-ingestion "llama-parse>=0.4.0"
uv add --package kb-retriever "some-package>=1.0.0"

# Add to root workspace (for shared dependencies)
uv add "shared-package>=1.0.0"
```

### Running Tests

```bash
# From root - run tests for specific package
uv run --package kb-ingestion python -m pytest
uv run --package kb-retriever python -m pytest

# Run all tests
uv run python -m pytest packages/
```

## Environment Variables

Required environment variables in `.env`:

```bash
OPENAI_API_KEY=sk-...
LLAMA_CLOUD_API_KEY=llx-...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=...
PINECONE_NAMESPACE=  # Optional
```

## Usage Examples

### API Usage
```python
from kb_ingestion import LlamaIndexDocumentIngestionToPinecone
from kb_retriever import LlamaIndexDocumentRetrievalFromPinecone

# Your usage code here
```

### CLI Usage
```bash
uv run python runner.py
```

## Package Development

When working on individual packages:

### KB Ingestion Package
```bash
# Add dependencies
uv add --package kb-ingestion "new-dependency"

# Run package-specific commands from root
uv run --package kb-ingestion python -c "import kb_ingestion; print('OK')"
```

### KB Retriever Package  
```bash
# Add dependencies
uv add --package kb-retriever "new-dependency"

# Run package-specific commands from root
uv run --package kb-retriever python -c "import kb_retriever; print('OK')"
```

### KB Event Handler Package (FastAPI Service)
```bash
# Add dependencies
uv add --package kb-event-handler "new-dependency"

# Run the FastAPI service
uv run --package kb-event-handler python -m kb_event_handler.main
```

## Troubleshooting

### Dependency Issues
If you accidentally run `uv sync` from a package directory and break dependencies:

```bash
# Go back to root and fix
cd ../../  # Navigate to root
uv sync     # Restore all dependencies
```

### Clean Reinstall
```bash
# Remove lock file and reinstall everything
rm uv.lock
uv sync
```

## Building and Publishing

```bash
# Build specific package
uv build --package kb-ingestion
uv build --package kb-retriever

# Build all packages
uv build
```

## Creating New Packages

To structure reusable packages in this monorepo:

```bash
# Initialize workspace
uv init --bare

# Add a new package
uv init packages/kb_ingestion --name kb-ingestion --lib
```

## Package Internal Structure

### High-Level Organization

```
packages/kb_ingestion/src/kb_ingestion/
├── interfaces/           # All abstract interfaces
├── implementations/      # Concrete implementations
│   ├── pipelines/       # Document & Website pipelines
│   ├── processing/      # Text splitters, extractors
│   ├── services/        # Embedding services
│   └── storage/         # Vector stores, caches
├── models/              # Data classes and DTOs
├── exceptions/          # Custom exception hierarchy
└── factory/             # Dependency injection factory
```

### Detailed Structure Example

```
packages/kb_ingestion/src/kb_ingestion/
├── __init__.py                    # Main package init
├── interfaces/
│   ├── __init__.py               # Export all interfaces
│   ├── ingestion.py              # IIngestionPipeline
│   ├── processing.py             # ITextSplitter, IContentExtractor
│   ├── storage.py                # IVectorStore, IIngestionCache
│   └── services.py               # IEmbeddingService
├── implementations/
│   ├── __init__.py               # Export implementations
│   ├── pipelines/
│   │   ├── __init__.py           # Export pipeline implementations
│   │   ├── document.py           # DocumentIngestionPipeline
│   │   └── website.py            # WebsiteIngestionPipeline
│   ├── processing/
│   │   ├── __init__.py           # Export processing implementations
│   │   ├── text_splitters.py
│   │   └── extractors.py
│   ├── services/
│   │   ├── __init__.py           # Export service implementations
│   │   └── embeddings.py
│   └── storage/
│       ├── __init__.py           # Export storage implementations
│       ├── vector_stores.py
│       └── caches.py
├── models/
│   ├── __init__.py               # Export all models
│   ├── requests.py               # FileWrapper, BatchRequest
│   ├── results.py                # IngestionResult, BatchIngestionResult
│   └── config.py                 # PipelineConfig, various configs
├── exceptions/
│   ├── __init__.py               # Export all exceptions
│   └── ingestion.py              # Custom exception hierarchy
└── factory/
    ├── __init__.py               # Export factory
    └── pipeline_factory.py       # PipelineFactory
```