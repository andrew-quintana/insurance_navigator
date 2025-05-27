# Supabase Database Integration Guide

## Executive Summary

The Insurance Navigator system has been successfully integrated with **Supabase PostgreSQL** as the production database, replacing in-memory storage with persistent data management. This integration provides:

- **Persistent conversation history** across user sessions
- **Agent workflow state management** for complex multi-step interactions  
- **User authentication and authorization** with JWT tokens
- **Document storage integration** with Supabase Storage
- **Regulatory document caching** for improved performance

## Architecture Overview

### Database Integration Points

```mermaid
graph TB
    A[FastAPI Backend] --> B[Agent Orchestrator]
    B --> C[Chat Communicator Agent]
    B --> D[Patient Navigator Agent]
    B --> E[Service Access Strategy Agent]
    
    C --> F[Conversation Service]
    D --> F
    E --> F
    
    F --> G[Supabase PostgreSQL]
    
    A --> H[User Service]
    H --> G
    
    G --> I[Persistent Storage]
    I --> J[Conversations]
    I --> K[Agent States]
    I --> L[Workflow States]
    I --> M[Users & Auth]
```

### Key Components

1. **Database Connection Pool** (`db/services/db_pool.py`)
   - Manages PostgreSQL connections with connection pooling
   - Supports both raw asyncpg and SQLAlchemy async operations
   - Handles connection lifecycle and error recovery

2. **Conversation Service** (`db/services/conversation_service.py`)
   - Manages persistent conversation history
   - Stores agent workflow states
   - Handles conversation metadata and context

3. **User Service** (`db/services/user_service.py`)
   - User registration and authentication
   - JWT token management
   - Role-based access control

4. **Migration System** (`db/scripts/run_migrations.py`)
   - Automated database schema management
   - Version tracking and rollback support
   - Safe migration execution

## Setup Instructions

### 1. Environment Configuration

Update your `.env` file with Supabase credentials:

```bash
# === Supabase Configuration ===
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# Database Configuration  
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
POSTGRES_PASSWORD=your_postgres_password

# Authentication & Security
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters-long-for-security
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage Configuration
SUPABASE_STORAGE_BUCKET=policies
SIGNED_URL_EXPIRY_SECONDS=3600
```

### 2. Run the Integration Setup

Execute the comprehensive setup script:

```bash
python db/scripts/setup_supabase_integration.py
```

This script will:
- ✅ Validate environment configuration
- ✅ Test database connectivity
- ✅ Execute all pending migrations
- ✅ Test user service functionality
- ✅ Validate conversation service
- ✅ Test agent orchestrator integration

### 3. Manual Migration (Alternative)

If you prefer manual setup:

```bash
# Run migrations
python db/scripts/run_migrations.py

# Test database connection
python -c "
import asyncio
from db.services.db_pool import get_db_pool

async def test():
    pool = await get_db_pool()
    result = await pool.test_connection()
    print('✅ Database connected' if result else '❌ Connection failed')

asyncio.run(test())
"
```

## Conversation Service Integration

### Best Practices Implementation

The conversation service follows enterprise best practices:

1. **Async/Await Pattern**
   - All database operations are asynchronous
   - Proper connection management and cleanup
   - Non-blocking I/O for high performance

2. **Error Handling and Resilience**
   - Graceful degradation when database is unavailable
   - Comprehensive error logging and monitoring
   - Automatic retry logic for transient failures

3. **Data Consistency**
   - ACID transaction support
   - Proper foreign key constraints
   - Atomic conversation operations

### Chat Communicator Integration

The `ChatCommunicatorAgent` now seamlessly integrates with persistent storage:

```python
# Before: In-memory conversation management
agent.update_conversation_context(user_id, session_id, message, response)

# After: Database-backed persistence
await agent.process_navigator_output(
    navigator_output=data,
    user_id=user_id,
    session_id=session_id
)
# Conversation automatically persisted to Supabase
```

### Key Integration Features

1. **Automatic Conversation Creation**
   ```python
   # Conversations are created automatically
   conversation_id = await conversation_service.create_conversation(
       user_id=user_id,
       conversation_id=session_id,
       metadata={"source": "navigator_output"}
   )
   ```

2. **Message Persistence**
   ```python
   # User and agent messages are stored
   await conversation_service.add_message(
       conversation_id=session_id,
       role="user",
       content=user_message,
       agent_name="patient_navigator"
   )
   ```

3. **Agent State Management**
   ```python
   # Agent workflow states are persisted
   await conversation_service.save_agent_state(
       conversation_id=conversation_id,
       agent_name="chat_communicator",
       state_data=workflow_state,
       workflow_step="response_generation"
   )
   ```

## Agent Orchestrator Integration

### Workflow State Persistence

The LangGraph orchestrator now persists workflow state at each step:

```python
# Workflow state is saved automatically
await conversation_service.save_workflow_state(
    conversation_id=conversation_id,
    workflow_type="strategy_request",
    current_step="security_check",
    state_data=state.to_dict(),
    user_id=user_id
)
```

### Resumable Workflows

Workflows can now resume from interruption:

```python
# Load existing workflow state
existing_state = await conversation_service.get_workflow_state(conversation_id)
if existing_state:
    state = AgentState.from_dict(existing_state["state_data"])
    logger.info(f"Resumed workflow from step: {existing_state['current_step']}")
```

## Database Schema

### Core Tables

1. **conversations**
   - `id` (TEXT): Conversation identifier
   - `user_id` (UUID): User who owns the conversation
   - `metadata` (JSONB): Conversation metadata
   - `created_at`, `updated_at` (TIMESTAMPTZ)

2. **conversation_messages**
   - `id` (TEXT): Message identifier
   - `conversation_id` (TEXT): FK to conversations
   - `role` (TEXT): user|assistant
   - `content` (TEXT): Message content
   - `agent_name` (TEXT): Source agent name
   - `metadata` (JSONB): Message metadata

3. **agent_states**
   - `conversation_id` (TEXT): FK to conversations
   - `agent_name` (TEXT): Agent identifier
   - `state_data` (JSONB): Serialized agent state
   - `workflow_step` (TEXT): Current workflow step

4. **workflow_states**
   - `conversation_id` (TEXT): FK to conversations (Primary Key)
   - `user_id` (UUID): User identifier
   - `workflow_type` (TEXT): Type of workflow
   - `current_step` (TEXT): Current step in workflow
   - `state_data` (JSONB): Workflow state data

### Migration Files

The system includes comprehensive migrations:

- `000_users_schema.sql` - User authentication tables
- `001_initial_schema.sql` - Core policy and document tables
- `002_initial_seed.sql` - Default roles and admin user
- `003_regulatory_documents.sql` - Regulatory document storage
- `004_add_regulatory_agent_role.sql` - Agent permissions

## API Integration

### Updated Endpoints

The FastAPI backend now uses async database operations:

```python
@app.post("/chat/navigator")
async def process_navigator(request: dict):
    """Process navigator input with persistent conversation."""
    agent = ChatCommunicatorAgent()
    return await agent.process_navigator_output(
        navigator_output=request["data"],
        user_id=request.get("user_id"),
        session_id=request.get("session_id")
    )

@app.get("/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    """Get conversation history from database."""
    conversation_service = await get_conversation_service()
    return await conversation_service.get_conversation_history(
        conversation_id=conversation_id,
        limit=50,
        include_metadata=True
    )
```

### Authentication Flow

```python
# User registration
user_service = await get_user_service()
user = await user_service.create_user(
    email=email,
    password=password,
    full_name=full_name
)

# Authentication
auth_user = await user_service.authenticate_user(email, password)
if auth_user:
    token = user_service.create_access_token(auth_user)
    # Use token for subsequent requests
```

## Performance Considerations

### Connection Pooling

```python
# Configured for optimal performance
pool = await asyncpg.create_pool(
    db_url,
    min_size=5,       # Minimum connections
    max_size=20,      # Maximum connections  
    command_timeout=60 # Query timeout
)
```

### Query Optimization

1. **Indexes**: Strategic indexes on conversation_id, user_id, and timestamps
2. **JSONB Queries**: Efficient metadata searches using GIN indexes
3. **Connection Reuse**: Persistent connection pooling reduces overhead

### Monitoring

- Database connection metrics
- Query performance tracking
- Conversation persistence success rates
- Agent state consistency checks

## Security Best Practices

### Data Protection

1. **Encryption at Rest**: Supabase provides automatic encryption
2. **Transport Security**: All connections use SSL/TLS
3. **Access Control**: Row-level security policies
4. **Audit Logging**: Comprehensive operation logging

### Authentication Security

```python
# JWT tokens with secure configuration
JWT_SECRET_KEY=minimum_32_characters_secure_random_string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Input Validation

- All user inputs validated through Pydantic models
- SQL injection prevention through parameterized queries
- XSS protection in conversation content

## Troubleshooting

### Common Issues

1. **Connection Failures**
   ```bash
   # Check DATABASE_URL format
   postgresql://postgres:password@db.project-ref.supabase.co:5432/postgres
   ```

2. **Migration Errors**
   ```bash
   # Check migration status
   python db/scripts/run_migrations.py
   ```

3. **Authentication Issues**
   ```bash
   # Verify JWT secret length (minimum 32 characters)
   echo $JWT_SECRET_KEY | wc -c
   ```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

```python
# Database health check
from db.services.db_pool import get_db_pool

async def health_check():
    pool = await get_db_pool()
    return await pool.test_connection()
```

## Migration from In-Memory Storage

### Data Migration Strategy

1. **Conversation History**: Historical conversations can be bulk-imported
2. **User Data**: Existing user sessions will require re-authentication
3. **Agent States**: Workflows will start fresh with new persistence

### Backwards Compatibility

The system maintains backwards compatibility:
- Graceful fallback to in-memory storage if database unavailable
- Existing API endpoints continue to function
- No breaking changes to agent interfaces

## Future Enhancements

### Planned Features

1. **Conversation Analytics**: Query patterns and user behavior analysis
2. **Advanced Caching**: Redis integration for frequently accessed conversations
3. **Data Archival**: Automatic archival of old conversations
4. **Multi-tenant Support**: Isolated data for different organizations

### Scalability Roadmap

1. **Read Replicas**: Database read scaling
2. **Connection Pooling**: Enhanced pool management
3. **Sharding Strategy**: Horizontal scaling for large datasets
4. **CDC Integration**: Change data capture for real-time analytics

## Best Practices Summary

### Development

1. **Always use async/await** for database operations
2. **Handle database errors gracefully** with try/catch blocks
3. **Use connection pooling** rather than direct connections
4. **Validate inputs** before database operations
5. **Test with realistic data volumes** for performance validation

### Production

1. **Monitor connection pool utilization**
2. **Set up database performance alerts**
3. **Regular backup verification**
4. **Capacity planning based on conversation volume**
5. **Security audit of access patterns**

## Support and Resources

- **Setup Script**: `python db/scripts/setup_supabase_integration.py`
- **Migration Tool**: `python db/scripts/run_migrations.py`
- **Health Check**: Database connection validation in setup script
- **Documentation**: This guide and inline code documentation
- **Error Logging**: Comprehensive logs in `logs/` directory

---

**Status**: ✅ Production Ready
**Last Updated**: January 2025
**Version**: 1.0.0 