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
│
├── health/                    # Health check domain
│   ├── router.py             # Health endpoints
│   └── schemas.py            # Health response models
│
├── ingestion/                 # Ingestion domain (placeholder)
│   └── __init__.py           # Future ingestion endpoints
│
└── common/                    # Shared utilities (placeholder)
    └── __init__.py           # Future utility modules
```

## 🔒 Authentication

The API uses a simple shared secret authentication model:

- **Header:** `X-API-Key: your_shared_secret`
- **Tenant ID:** `X-Tenant-ID: 123`

All protected endpoints require both headers.

## 📊 Current Features (Phase 1 Complete)

### ✅ Foundation & Structure
- FastAPI application with proper configuration
- Environment variable validation using Pydantic
- Structured logging with JSON format support
- CORS middleware configuration
- Custom exception handling
- Request correlation ID tracking
- Authentication middleware for API key validation
- Tenant ID validation from headers

### ✅ Health Check Endpoint
- `GET /api/v1/health` - Returns system health status
- Includes environment, version, and dependency status
- JSON response with structured data

### 🔄 Coming Next (Future Phases)
- Database integration with Supabase (Phase 2)
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
    "supabase": "unknown",
    "openai": "unknown",
    "pinecone": "unknown"
  }
}
```

### Authentication Test
```bash
# This will fail with 401 (expected in Phase 1)
curl -H "X-API-Key: wrong-key" -H "X-Tenant-ID: 123" http://localhost:8000/api/v1/health
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
- **Open/Closed:** Extensible through interfaces (will be evident in later phases)
- **Liskov Substitution:** Proper inheritance hierarchies
- **Interface Segregation:** Clean, focused interfaces
- **Dependency Inversion:** Dependency injection patterns

### Next Steps
Ready to proceed with Phase 2 - Database Integration, which will add:
- Supabase client setup
- Repository pattern implementation
- Database models and operations
- Connection health checks

## 📖 Implementation Plan

This project follows a 6-phase implementation plan. See `IMPLEMENTATION_PLAN.md` for detailed phase breakdown and technical specifications.

**Current Status:** ✅ Phase 1 Complete - Foundation & Structure
