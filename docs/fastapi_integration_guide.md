# FastAPI Integration Guide

## Overview

The Insurance Navigator FastAPI application provides a comprehensive REST API with persistent database integration, user authentication, conversation management, and document storage. This guide covers the complete API integration with Supabase PostgreSQL and Storage.

## Features

### ✅ Core API Features
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Async Database Integration**: Full Supabase PostgreSQL integration with connection pooling
- **User Authentication**: JWT-based authentication with role-based access control
- **Conversation Persistence**: Chat history with conversation threading
- **Document Storage**: Secure file upload/download with Supabase Storage
- **Agent Orchestration**: Integration with LangGraph agent system
- **Comprehensive Error Handling**: Structured error responses and logging

### ✅ Security Features
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: User/admin permission system
- **File Permissions**: Owner-based file access control
- **Input Validation**: Pydantic model validation
- **CORS Configuration**: Secure cross-origin request handling

## API Endpoints

### Authentication Endpoints

#### POST `/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### POST `/login`
Authenticate user and return access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### GET `/me`
Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer your_jwt_token_here
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-01T12:00:00Z",
  "is_active": true,
  "roles": ["user"]
}
```

### Chat and Conversation Endpoints

#### POST `/chat`
Send message and get AI response with conversation persistence.

**Headers:**
```
Authorization: Bearer your_jwt_token_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "I need help with Medicare eligibility requirements",
  "conversation_id": "optional-existing-conversation-id",
  "context": {
    "user_state": "new_inquiry",
    "priority": "high"
  }
}
```

**Response:**
```json
{
  "text": "I'd be happy to help you understand Medicare eligibility...",
  "conversation_id": "conv_123e4567-e89b-12d3-a456-426614174000",
  "sources": [
    {
      "title": "Medicare.gov Official Guidelines",
      "url": "https://medicare.gov/eligibility",
      "relevance": 0.95
    }
  ],
  "metadata": {
    "agent_used": "patient_navigator",
    "processing_time": 2.3,
    "confidence": 0.92
  },
  "workflow_type": "medicare_navigator",
  "agent_state": {
    "current_step": "eligibility_check",
    "next_actions": ["verify_age", "check_disability_status"]
  }
}
```

#### GET `/conversations`
Get user's conversation history.

**Headers:**
```
Authorization: Bearer your_jwt_token_here
```

**Query Parameters:**
- `limit` (optional): Number of conversations to return (default: 20)

**Response:**
```json
[
  {
    "id": "conv_123e4567-e89b-12d3-a456-426614174000",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T13:30:00Z",
    "message_count": 8,
    "metadata": {
      "workflow_type": "medicare_navigator",
      "last_topic": "eligibility_requirements"
    }
  }
]
```

#### GET `/conversations/{conversation_id}/messages`
Get messages from a specific conversation.

**Headers:**
```
Authorization: Bearer your_jwt_token_here
```

**Query Parameters:**
- `limit` (optional): Number of messages to return (default: 50)

**Response:**
```json
{
  "messages": [
    {
      "id": "msg_123",
      "role": "user",
      "content": "I need help with Medicare eligibility",
      "created_at": "2024-01-01T12:00:00Z",
      "metadata": {
        "user_context": "new_inquiry"
      }
    },
    {
      "id": "msg_124", 
      "role": "assistant",
      "content": "I'd be happy to help you understand Medicare eligibility...",
      "created_at": "2024-01-01T12:00:05Z",
      "metadata": {
        "sources": [...],
        "agent_metadata": {...}
      }
    }
  ]
}
```

### Document Storage Endpoints

#### POST `/upload-document`
Upload a policy document with secure storage.

**Headers:**
```
Authorization: Bearer your_jwt_token_here
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Document file (PDF, DOC, DOCX, etc.)
- `policy_id`: UUID of the associated policy
- `document_type`: Type of document (policy, claim, etc.)

**Response:**
```json
{
  "document_id": 123,
  "file_path": "policy/123e4567-e89b-12d3-a456-426614174000/abc123.pdf",
  "original_filename": "policy_document.pdf",
  "file_size": 2048576,
  "signed_url": "https://storage.supabase.co/...?token=..."
}
```

#### GET `/documents`
List user's documents with filtering.

**Headers:**
```
Authorization: Bearer your_jwt_token_here
```

**Query Parameters:**
- `policy_id` (required): UUID of the policy
- `document_type` (optional): Filter by document type

**Response:**
```json
[
  {
    "id": 123,
    "file_path": "policy/123e4567-e89b-12d3-a456-426614174000/abc123.pdf",
    "original_filename": "policy_document.pdf",
    "content_type": "application/pdf",
    "file_size": 2048576,
    "document_type": "policy",
    "uploaded_at": "2024-01-01T12:00:00Z",
    "metadata": {
      "uploaded_by_name": "John Doe",
      "content_length": 2048576
    }
  }
]
```

#### GET `/documents/{file_path}/download`
Download a document (redirects to signed URL).

**Headers:**
```
Authorization: Bearer your_jwt_token_here
```

**Response:**
- **307 Redirect**: Redirects to Supabase Storage signed URL
- **403 Forbidden**: If user doesn't have read access
- **404 Not Found**: If document doesn't exist

#### DELETE `/documents/{file_path}`
Delete a document (soft delete by default).

**Headers:**
```
Authorization: Bearer your_jwt_token_here
```

**Query Parameters:**
- `hard_delete` (optional): Boolean to permanently delete (default: false)

**Response:**
```json
{
  "message": "Document deleted",
  "success": true
}
```

### System Endpoints

#### GET `/`
API root endpoint with service information.

**Response:**
```json
{
  "service": "Insurance Navigator API",
  "version": "2.0.0",
  "status": "running",
  "features": [
    "Persistent user authentication",
    "Conversation history",
    "Document storage",
    "Agent orchestration",
    "Role-based access control"
  ],
  "endpoints": {
    "docs": "/docs",
    "health": "/health",
    "auth": ["/register", "/login", "/me"],
    "chat": ["/chat", "/conversations"],
    "storage": ["/upload-document", "/documents"]
  }
}
```

#### GET `/health`
Comprehensive health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "insurance_navigator",
  "version": "2.0.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "database": "healthy",
    "user_service": "healthy",
    "conversation_service": "healthy",
    "storage_service": "healthy",
    "agent_orchestrator": "available"
  }
}
```

## Authentication

The API uses JWT (JSON Web Token) based authentication:

1. **Register** or **Login** to get an access token
2. **Include the token** in the Authorization header for protected endpoints:
   ```
   Authorization: Bearer your_jwt_token_here
   ```
3. **Token expiration**: Tokens expire after a configured time period
4. **Token validation**: Each request validates the token and loads user context

### Example Authentication Flow

```python
import httpx

async def authenticate_and_chat():
    client = httpx.AsyncClient(base_url="http://localhost:8000")
    
    # 1. Login
    login_response = await client.post("/login", json={
        "email": "user@example.com",
        "password": "SecurePassword123!"
    })
    token = login_response.json()["access_token"]
    
    # 2. Use token for protected endpoints
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Send chat message
    chat_response = await client.post("/chat", json={
        "message": "Help me understand Medicare Part A coverage"
    }, headers=headers)
    
    return chat_response.json()
```

## Error Handling

The API provides structured error responses:

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Common HTTP Status Codes
- **200**: Success
- **201**: Created successfully
- **400**: Bad Request (validation error)
- **401**: Unauthorized (invalid/missing token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **422**: Unprocessable Entity (validation error)
- **500**: Internal Server Error

### Authentication Errors
```json
{
  "detail": "Missing or invalid authentication token",
  "headers": {"WWW-Authenticate": "Bearer"}
}
```

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Database Integration

### Connection Management
- **Async Connection Pool**: Efficient database connection pooling with AsyncPG
- **Transaction Support**: Automatic transaction management for data consistency
- **Connection Health Monitoring**: Automatic reconnection and health checks

### Data Persistence
- **User Data**: Secure user authentication and profile management
- **Conversation History**: Complete message history with metadata
- **Document Metadata**: File information and access control
- **Agent State**: Persistent agent workflow state

### Performance Optimization
- **Connection Pooling**: Reused database connections for performance
- **Async Operations**: Non-blocking database operations
- **Indexed Queries**: Optimized database queries with proper indexing
- **JSONB Support**: Efficient metadata storage and querying

## Testing

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run comprehensive API integration tests
python scripts/test_api_integration.py

# Run specific endpoint tests
python tests/integration/test_fastapi_endpoints.py
```

### Test Coverage

The test suite covers:
- ✅ **Authentication Flow**: Registration, login, token validation
- ✅ **Chat Endpoints**: Message sending, conversation management
- ✅ **Document Storage**: Upload, download, permissions
- ✅ **Error Handling**: Authentication failures, validation errors
- ✅ **Database Integration**: Data persistence and retrieval
- ✅ **Security**: Authorization and access control

### Example Test Output
```
🎉 All FastAPI endpoint tests PASSED!
📊 Test Results: 12 passed, 0 failed

✅ FastAPI application is fully integrated with database services
✅ Authentication, chat, and storage endpoints are working
✅ Database persistence is functioning correctly
```

## Development Setup

### Prerequisites
- Python 3.11+
- Supabase account with PostgreSQL database
- Environment variables configured

### Environment Configuration

Copy `.env.template` to `.env` and configure:

```bash
# Database
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_URL=postgresql://postgres:password@db.supabase.co:5432/postgres

# Storage
SUPABASE_STORAGE_BUCKET=documents
SIGNED_URL_EXPIRY_SECONDS=3600

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Running the API

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
python db/scripts/run_migrations.py

# Start the API server
python main.py

# Or with uvicorn for development
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Production Deployment

### Environment Considerations
- Use secure JWT secret keys
- Configure proper CORS origins
- Set up SSL/TLS certificates
- Monitor database connection pools
- Implement proper logging

### Scaling
- Database connection pool sizing
- Horizontal scaling with load balancers
- Supabase Storage CDN for file delivery
- Caching for frequently accessed data

### Monitoring
- Health check endpoint monitoring
- Database performance metrics
- API response time tracking
- Error rate monitoring

## Integration with Frontend

The API is designed to work seamlessly with frontend applications:

### React/Next.js Integration
```javascript
// API client setup
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Send chat message
const sendMessage = async (message, conversationId) => {
  const response = await apiClient.post('/chat', {
    message,
    conversation_id: conversationId
  });
  return response.data;
};
```

### File Upload Integration
```javascript
// Document upload
const uploadDocument = async (file, policyId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('policy_id', policyId);
  formData.append('document_type', 'policy');
  
  const response = await apiClient.post('/upload-document', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};
```

## Conclusion

The FastAPI integration provides a production-ready API with:
- ✅ **Complete Database Integration** with Supabase PostgreSQL
- ✅ **Secure Authentication** with JWT and role-based access
- ✅ **Persistent Conversations** with full message history
- ✅ **Document Storage** with Supabase Storage integration
- ✅ **Agent Orchestration** with LangGraph workflow integration
- ✅ **Comprehensive Testing** with automated test suites
- ✅ **Production Readiness** with proper error handling and monitoring

The API is ready for frontend integration and production deployment, providing a solid foundation for the Insurance Navigator application. 