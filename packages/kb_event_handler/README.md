# KB Event Handler API

FastAPI service for knowledge base ingestion operations following SOLID principles and FastAPI best practices.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- uv package manager

### Installation

1. **Install dependencies:**
   ```bash
   cd packages/kb_event_handler
   uv sync
   ```

2. **Set up environment variables:**
   Create a `.env` file in the package root with the following variables:
   ```bash
   # API Configuration
   API_SECRET_KEY=your_shared_secret_between_nextjs_and_python
   API_VERSION=v1
   API_HOST=0.0.0.0
   API_PORT=8000
   ENVIRONMENT=development

   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your_service_role_key_here

   # OpenAI Configuration
   OPENAI_API_KEY=sk-your_openai_api_key_here

   # Pinecone Configuration
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_INDEX_NAME=kb-management

   # Logging Configuration
   LOG_LEVEL=INFO
   LOG_FORMAT=json
   ```

3. **Run the development server:**
   ```bash
   python run_dev.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn src.kb_event_handler.main:app --reload --host 0.0.0.0 --port 8000
   ```

## 📚 API Documentation

Once the server is running, you can access:

- **Interactive API Docs (Swagger):** http://localhost:8000/api/v1/docs
- **Alternative API Docs (ReDoc):** http://localhost:8000/api/v1/redoc
- **Health Check:** http://localhost:8000/api/v1/health

## 🏗️ Architecture

This service follows FastAPI best practices with a domain-driven structure:

```
src/kb_event_handler/
├── main.py                    # FastAPI app initialization
├── config.py                  # Global configurations
├── dependencies.py            # Global dependencies (auth, db)
├── exceptions.py              # Global exception handlers
├── middleware.py              # Custom middleware
├── database.py                # Database setup and initialization
│
├── health/                    # Health check domain
│   ├── router.py             # Health endpoints
│   └── schemas.py            # Health response models
│
├── ingestion/                 # Ingestion domain (placeholder)
│   └── __init__.py           # Future ingestion endpoints
│
└── common/                    # Shared utilities
    ├── models.py             # Database Pydantic models
    ├── repositories.py       # Repository pattern implementation
    ├── supabase_client.py    # Supabase client wrapper
    └── __init__.py           # Common module exports
```

## 🔒 Authentication

The API uses a simple shared secret authentication model:

- **Header:** `X-API-Key: your_shared_secret`
- **Tenant ID:** `X-Tenant-ID: 123`

All protected endpoints require both headers.

## 📊 Current Features

### ✅ Phase 1 Complete - Foundation & Structure
- FastAPI application with proper configuration
- Environment variable validation using Pydantic
- Structured logging with JSON format support
- CORS middleware configuration
- Custom exception handling
- Request correlation ID tracking
- Authentication middleware for API key validation
- Tenant ID validation from headers

### ✅ Phase 2 Complete - Database Integration 
- **Database Models** - Complete Pydantic models for all Supabase entities:
  - `Tenant`, `Profile`, `TenantUser` (core tables)
  - `KnowledgeBase`, `KBFile`, `KBJob` (knowledge base tables)
  - Create/Update models for API operations
- **Repository Pattern** - Clean database abstraction layer:
  - `BaseRepository` with common CRUD operations
  - `TenantRepository`, `JobRepository`, `KnowledgeBaseRepository`, `FileRepository`
  - Tenant-scoped operations with RLS support
- **Supabase Client** - Async client with connection management:
  - Connection pooling and error handling
  - Health check integration
  - Automatic reconnection logic
- **Dependency Injection** - Repository instances available as FastAPI dependencies
- **Database Lifecycle** - Automatic connection/disconnection during app startup/shutdown

### ✅ Health Check Endpoint
- `GET /api/v1/health` - Returns system health status
- **Real Supabase connectivity** - Tests actual database connection
- Includes environment, version, and dependency status
- JSON response with structured data

### 🔄 Coming Next (Future Phases)
- File validation and storage handling (Phase 3)
- Ingestion service integration (Phase 4)
- File ingestion endpoints (Phase 5)
- Enhanced error handling and monitoring (Phase 6)

## 🧪 Testing the API

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:00:00.000Z",
  "version": "0.1.0",
  "environment": "development",
  "dependencies": {
    "supabase": "connected",
    "openai": "unknown",
    "pinecone": "unknown"
  }
}
```

### Authentication Test
```bash
# This will fail with 401 (expected)
curl -H "X-API-Key: wrong-key" -H "X-Tenant-ID: 123" http://localhost:8000/api/v1/health
```

### Database Integration Test
```bash
# Run Phase 2 tests
python test_phase2.py
```

## 🔧 Configuration

The application uses Pydantic BaseSettings for configuration management. All settings can be configured via environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_SECRET_KEY` | ✅ | - | Shared secret for API authentication |
| `API_VERSION` | ❌ | `v1` | API version prefix |
| `API_HOST` | ❌ | `0.0.0.0` | Host to bind the server |
| `API_PORT` | ❌ | `8000` | Port to bind the server |
| `ENVIRONMENT` | ❌ | `development` | Environment name |
| `SUPABASE_URL` | ✅ | - | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | ✅ | - | Supabase service role key |
| `OPENAI_API_KEY` | ✅ | - | OpenAI API key |
| `PINECONE_API_KEY` | ✅ | - | Pinecone API key |
| `PINECONE_INDEX_NAME` | ✅ | - | Pinecone index name |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
| `LOG_FORMAT` | ❌ | `json` | Log format (json/text) |

## 🎯 Database Schema

The service integrates with a multi-tenant Supabase database:

### Core Tables
- **`tenants`** - Organizations/workspaces
- **`tenant_users`** - User-tenant relationships with roles
- **`profiles`** - Extended user profile information

### Knowledge Base Tables  
- **`knowledge_bases`** - KB metadata with status tracking
- **`kb_files`** - File references with storage paths
- **`kb_jobs`** - Job tracking for processing operations

### Repository Features
- **Tenant Scoping** - All operations are tenant-aware
- **Type Safety** - Full Pydantic model integration
- **CRUD Operations** - Complete create, read, update, delete support
- **Custom Queries** - Specialized methods for business logic
- **Error Handling** - Comprehensive exception management

## 🚀 Deployment

### Production Considerations
- Set `ENVIRONMENT=production` to hide API documentation
- Use strong `API_SECRET_KEY` values
- Configure proper CORS origins
- Set appropriate log levels
- Use environment-specific configuration

### Docker (Coming Soon)
Docker configuration will be added in future phases.

## 📝 Development

### Code Quality
- Type hints throughout the codebase
- Pydantic models for data validation
- Structured logging with correlation IDs
- Comprehensive error handling

### SOLID Principles
- **Single Responsibility:** Each module has a focused purpose
- **Open/Closed:** Extensible through interfaces (evident in repository pattern)
- **Liskov Substitution:** Proper inheritance hierarchies in repositories
- **Interface Segregation:** Clean, focused interfaces
- **Dependency Inversion:** Dependency injection patterns throughout

### Testing
```bash
# Test Phase 2 database integration
python test_phase2.py

# Expected output: All tests passing ✅
```

### Next Steps
Ready to proceed with **Phase 3 - File Handling & Validation**, which will add:
- File type validation (pdf, ppt, docx, doc, md)
- File size validation (<25MB)
- Supabase Storage integration
- File download and temporary management
- Validation service with custom exceptions

## 📖 Implementation Plan

This project follows a 6-phase implementation plan. See `IMPLEMENTATION_PLAN.md` for detailed phase breakdown and technical specifications.

**Current Status:** ✅ Phase 2 Complete - Database Integration

**Next:** Phase 3 - File Handling & Validation
