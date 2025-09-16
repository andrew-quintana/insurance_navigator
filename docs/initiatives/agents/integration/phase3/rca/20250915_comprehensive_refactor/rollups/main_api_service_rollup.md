# Main API Service Rollup

**Last Updated:** 2025-09-15  
**Maintainer:** Core Development Team  
**Status:** active

## Purpose
The Main API Service serves as the central entry point for the Insurance Navigator system, handling user authentication, document uploads, chat interactions, and coordinating with various backend services including the RAG system, database operations, and external APIs. It provides RESTful endpoints for frontend integration and manages the complete user workflow from document upload to AI-powered chat responses.

## Key Interfaces
```
POST /api/v2/upload - Document upload endpoint
POST /chat - Chat interaction endpoint  
GET /health - Service health check
POST /auth/login - User authentication
POST /auth/signup - User registration
```

## Dependencies
- Input: HTTP requests from frontend, user authentication tokens, document uploads
- Output: JSON responses, file uploads to storage, database operations
- External: Supabase database, OpenAI API, Anthropic API, RAG system

## Current Status
- Performance: Degraded due to RAG tool integration failures
- Reliability: 57.1% test success rate, critical functionality failing
- Technical Debt: High - missing service initialization, configuration management issues

## Integration Points
- Frontend Next.js application for user interface
- RAG system for document retrieval and chat responses
- Supabase database for data persistence and user management
- External AI APIs for embedding generation and response processing
- Upload pipeline workers for document processing

## Recent Changes
- Added RAG tool integration (September 15, 2025)
- Implemented configuration management system (September 15, 2025)
- Fixed database schema references (September 15, 2025)
- Added comprehensive error handling (September 15, 2025)

## Known Issues
- RAG tool not properly initialized in service startup
- Configuration management not loading environment-specific settings
- Database schema references incorrect table names
- Missing service dependency injection
- Error handling insufficient for production use

## Quick Start
```python
# Start the main API service
from main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```
