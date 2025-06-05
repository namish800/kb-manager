Monorepo with uv to structure resubale packages
uv init --bare

to add a package
uv init packages/kb_ingestion --name kb-ingestion --lib  


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