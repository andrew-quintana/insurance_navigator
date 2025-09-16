# Main API Service Rollup

**Last Updated:** 2025-09-15  
**Maintainer:** Core Development Team  
**Status:** active

## Purpose
The Main API Service serves as the central entry point for the Insurance Navigator system, handling user authentication, document uploads, chat interactions, and coordinating with various backend services including the **embedded RAG system**, database operations, and external APIs. It provides RESTful endpoints for frontend integration and manages the complete user workflow from document upload to AI-powered chat responses. The RAG system is embedded as a library component within this service, not a separate microservice.

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
- **Embedded RAG system** for document retrieval and chat responses
- Supabase database for data persistence and user management
- External AI APIs for embedding generation and response processing
- Upload pipeline workers for document processing

## Recent Changes
- Added RAG tool integration (September 15, 2025)
- Implemented configuration management system (September 15, 2025)
- Fixed database schema references (September 15, 2025)
- Added comprehensive error handling (September 15, 2025)

## Known Issues
- **RAG Tool Initialization**: RAG tool not properly initialized in main.py startup sequence
- **Configuration Management**: Not loading environment-specific settings (similarity threshold 0.7 vs 0.3)
- **Database Schema**: References incorrect table names (chunks vs document_chunks)
- **Service Dependencies**: Missing service dependency injection
- **Error Handling**: Insufficient error handling for production use

## Quick Start
```python
# Start the main API service
from main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
```
