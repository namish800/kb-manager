# KB Event Handler - Implementation Plan

## 📋 Project Overview

The KB Event Handler is a FastAPI service that provides REST endpoints for knowledge base ingestion operations. It follows a microservice architecture pattern where Next.js uploads files to Supabase Storage and triggers this Python API for background processing.

### Tech Stack Flow
```
Next.js → Upload to Supabase Storage → Trigger Python API → Return immediately
Python Worker → Process in background → Update Supabase DB
```

### Key Requirements
- **SOLID Design Principles** with dependency injection
- **FastAPI Best Practices** following Netflix Dispatch structure
- **Multi-tenant Architecture** with tenant-scoped operations
- **Background Processing** using FastAPI's built-in BackgroundTasks
- **Supabase Integration** for database and storage operations

## 🏗️ Architecture Overview

### Project Structure
Following FastAPI best practices with domain-driven design:

```
src/kb_event_handler/
├── main.py                    # FastAPI app initialization
├── config.py                  # Global configurations
├── dependencies.py            # Global dependencies (auth, db)
├── exceptions.py              # Global exception handlers
├── database.py                # Supabase client setup
│
├── ingestion/                 # Ingestion domain module
│   ├── router.py             # Ingestion endpoints
│   ├── schemas.py            # Pydantic models for requests/responses
│   ├── service.py            # Business logic layer
│   ├── dependencies.py       # Ingestion-specific dependencies
│   ├── exceptions.py         # Ingestion-specific exceptions
│   └── background_tasks.py   # Background task definitions
│
├── health/                   # Health check domain
│   ├── router.py
│   └── schemas.py
│
└── common/                   # Shared utilities
    ├── auth.py              # Authentication utilities
    ├── supabase_client.py   # Supabase integration
    ├── repositories.py      # Database repository classes
    └── utils.py             # Common utilities
```

### Database Schema Reference
Multi-tenant architecture with the following key tables:

#### Core Tables
- **`tenants`** - Organizations/workspaces
- **`tenant_users`** - User-tenant relationships with roles
- **`profiles`** - Extended user profile information

#### Knowledge Base Tables
- **`knowledge_bases`** - KB metadata with status tracking
- **`kb_files`** - File references with storage paths
- **`kb_jobs`** - Job tracking for processing operations

#### Job Status Flow
```
queued → processing → completed/failed
```

## 📅 Implementation Phases

### Phase 1: Foundation & Structure ⚡
**Goal:** Set up basic FastAPI architecture following best practices

#### Tasks:
1. **Project Structure Setup**
   - Create FastAPI directory structure per best practices
   - Set up `main.py` with app initialization
   - Create domain modules: `ingestion/`, `health/`
   - Configure package imports and exports

2. **Core Infrastructure**
   - Global configuration management (Pydantic BaseSettings)
   - Environment variable validation
   - Basic logging setup with structured format
   - CORS and middleware configuration

3. **Authentication & Middleware**
   - Simple API key authentication middleware
   - Tenant ID validation from headers
   - Request correlation ID generation
   - Security headers middleware

**Deliverable:** Working FastAPI app with authentication middleware

---

### Phase 2: Database Integration 📊
**Goal:** Set up Supabase integration with proper models

#### Tasks:
1. **Database Models**
   - Pydantic models for database entities
   - Request/response schemas
   - Configuration models with validation

2. **Repository Pattern**
   - `JobRepository` for `kb_jobs` CRUD operations
   - `KnowledgeBaseRepository` for KB operations
   - `FileRepository` for `kb_files` operations
   - Base repository with common patterns

3. **Supabase Client**
   - Async Supabase client setup
   - Connection pooling and error handling
   - RLS (Row Level Security) integration
   - Tenant-scoped database operations

**Deliverable:** Clean database abstraction layer with repositories

---

### Phase 3: File Handling & Validation 📁
**Goal:** Implement file download and validation logic

#### Tasks:
1. **File Validation**
   - File type validation (pdf, ppt, docx, doc, md)
   - File size validation (<25MB)
   - MIME type verification
   - File existence check in Supabase Storage

2. **Storage Integration**
   - Supabase Storage client configuration
   - Async file download from storage paths
   - Temporary file management and cleanup
   - Error handling for storage operations

3. **Validation Service**
   - Centralized file validation logic
   - Custom validation exceptions
   - Detailed error responses
   - File metadata extraction

**Deliverable:** Robust file validation and download system

---

### Phase 4: Ingestion Service Integration 🔄
**Goal:** Integrate with existing `kb_ingestion` package using dependency injection

#### Tasks:
1. **Service Layer Design**
   - `IngestionService` with dependency injection
   - Configuration factory for ingestion pipelines
   - Progress callback mechanism
   - Error handling and recovery

2. **Pipeline Integration**
   - Import `kb_ingestion` package components
   - Configure `LlamaIndexDocumentIngestionToPinecone`
   - Convert files to `FileWrapper` format
   - Handle `IngestionResult` and metadata

3. **Progress Tracking**
   - Progress calculation during ingestion
   - Real-time database updates
   - Success/failure result handling
   - Performance metrics collection

**Deliverable:** Working ingestion service following SOLID principles

---

### Phase 5: API Endpoints & Background Tasks 🚀
**Goal:** Implement actual API endpoints with background processing

#### Tasks:
1. **API Schemas**
   - Request/response Pydantic models
   - Error response standardization
   - OpenAPI documentation schemas
   - Example payloads and responses

2. **Ingestion Endpoint**
   - `POST /api/v1/ingestion/files` implementation
   - Request validation and sanitization
   - Authentication and authorization
   - Background task dispatch

3. **Background Task Implementation**
   - FastAPI BackgroundTasks integration
   - End-to-end file processing workflow
   - Database status updates
   - Error handling and logging

4. **Health Check Endpoint**
   - `GET /api/v1/health` implementation
   - System health indicators
   - Dependency health checks
   - Version information

**Deliverable:** Complete working API with all endpoints

---

### Phase 6: Testing & Polish ✨
**Goal:** Add comprehensive error handling, logging, and production readiness

#### Tasks:
1. **Enhanced Error Handling**
   - Custom exception hierarchy
   - Proper HTTP status codes
   - Detailed error messages
   - Error tracking and monitoring

2. **Logging & Monitoring**
   - Structured logging with correlation IDs
   - Request/response logging
   - Performance metrics
   - Health monitoring endpoints

3. **Production Readiness**
   - Configuration validation
   - Startup health checks
   - Graceful shutdown handling
   - Documentation and examples

**Deliverable:** Production-ready API service

## 🔧 Technical Specifications

### Authentication
- **Method:** Shared secret API key + Tenant ID
- **Headers:** 
  - `X-API-Key`: Shared secret between Next.js and Python API
  - `X-Tenant-ID`: Tenant identifier for multi-tenant operations

### File Validation Rules
```python
# Supported file types
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.ms-powerpoint", 
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown"
}

# File size limit
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
```

### Dependency Injection Architecture
```python
class IngestionService:
    def __init__(
        self,
        job_repo: JobRepository,
        kb_repo: KnowledgeBaseRepository, 
        file_repo: FileRepository,
        storage_client: StorageClient,
        pipeline_factory: IngestionPipelineFactory
    ):
        # Dependencies injected at construction
        # Follows Dependency Inversion Principle
```

### Background Task Signature
```python
async def process_file_ingestion(
    tenant_id: int,
    knowledge_base_id: int,
    file_path: str,
    job_id: int,
    original_name: str,
    correlation_id: str
) -> None:
    # Process file in background
    # Update database with progress
    # Handle errors gracefully
```

## 📡 API Specification

### File Ingestion Endpoint
```http
POST /api/v1/ingestion/files
Headers:
  X-API-Key: your_shared_secret
  X-Tenant-ID: 123
  Content-Type: application/json

Request Body:
{
    "knowledge_base_id": 456,
    "file_path": "tenant_123/files/document.pdf",
    "original_name": "My Document.pdf"
}

Response (202 Accepted):
{
    "job_id": 789,
    "status": "queued",
    "message": "File ingestion started",
    "correlation_id": "req_abc123"
}

Error Response (400 Bad Request):
{
    "error": "INVALID_FILE_TYPE",
    "message": "File type not supported: .txt",
    "correlation_id": "req_abc123"
}
```

### Health Check Endpoint
```http
GET /api/v1/health

Response (200 OK):
{
    "status": "healthy",
    "timestamp": "2025-01-27T10:00:00Z",
    "version": "1.0.0",
    "dependencies": {
        "supabase": "connected",
        "openai": "connected",
        "pinecone": "connected"
    }
}
```

## ⚙️ Configuration

### Environment Variables
```bash
# API Configuration
API_SECRET_KEY=your_shared_secret_here
API_VERSION=v1
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development

# Supabase Configuration  
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_key_here

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_INDEX_NAME=kb-management

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Configuration Validation
All environment variables are validated at startup using Pydantic BaseSettings with proper error messages for missing or invalid values.

## 🚀 Execution Strategy

### Development Approach
1. **Sequential Implementation:** Each phase builds on the previous
2. **Testing at Each Phase:** Validate functionality before moving forward  
3. **SOLID Principles:** Maintain clean architecture throughout
4. **FastAPI Best Practices:** Follow Netflix Dispatch structure consistently

### Error Handling Strategy
- **Graceful Degradation:** API returns meaningful errors for all failure modes
- **Database Consistency:** All job status updates are transactional
- **Logging:** Comprehensive logging with correlation IDs for debugging
- **Monitoring:** Health checks for all external dependencies

### Performance Considerations
- **Async Operations:** All I/O operations are asynchronous
- **Connection Pooling:** Proper connection management for Supabase
- **Resource Cleanup:** Temporary files are cleaned up automatically
- **Background Processing:** Non-blocking API responses with background processing

## 📚 Dependencies

### Core Dependencies
- **FastAPI:** Web framework with automatic OpenAPI documentation
- **Pydantic:** Data validation and serialization
- **Supabase:** Database and storage client
- **kb_ingestion:** Internal package for document processing

### Development Dependencies
- **pytest:** Testing framework
- **black:** Code formatting
- **flake8:** Code linting
- **mypy:** Type checking

This implementation plan ensures a robust, scalable, and maintainable FastAPI service that follows industry best practices while integrating seamlessly with the existing knowledge base management ecosystem. 