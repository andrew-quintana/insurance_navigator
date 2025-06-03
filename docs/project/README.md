# Insurance Navigator System

A comprehensive multi-agent system for navigating healthcare insurance options, focusing on Medicare.

## Overview

The Insurance Navigator system consists of multiple specialized agents that work together to help users understand their healthcare options, verify document requirements, and develop strategies for accessing healthcare services.

## Architecture

The system is built on a modular architecture with four main agents:

1. **Prompt Security Agent**: Validates user inputs for security issues
2. **Patient Navigator Agent**: Front-facing agent that understands user needs and questions
3. **Task Requirements Agent**: Determines required documentation for service requests
4. **Service Access Strategy Agent**: Develops strategies for accessing healthcare services

Each agent has standardized components:
- Core implementation files
- Pydantic models for type safety
- Standard error handling
- Unit tests
- Configuration through a centralized config manager

## Directory Structure

```
insurance_navigator/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── common/
│   │   └── exceptions.py
│   ├── prompt_security/
│   │   ├── core/
│   │   ├── models/
│   │   └── tests/
│   ├── patient_navigator/
│   │   ├── core/
│   │   ├── models/
│   │   └── tests/
│   ├── task_requirements/
│   │   ├── core/
│   │   ├── models/
│   │   └── tests/
│   └── service_access_strategy/
│       ├── core/
│       ├── models/
│       └── tests/
├── config/
│   └── agent_config.json
├── utils/
│   └── config_manager.py
└── examples/
    └── insurance_navigator_example.py
```

## Key Features

- **Standardized Error Handling**: Consistent hierarchy of exceptions
- **Type Safety**: Pydantic models for all agent inputs and outputs
- **Modular Components**: Clean boundaries between agents
- **Comprehensive Testing**: Unit tests for each agent
- **Configurability**: Centralized configuration
- **Resilience**: Graceful handling of component failures

## DRY (Don't Repeat Yourself) Principles

The refactored codebase follows DRY principles by:

1. **Common BaseAgent**: Implementing shared functionality in the BaseAgent class
   - Standardized prompt loading with fallbacks
   - Consistent error handling
   - Performance tracking
   - Logging configuration
   
2. **Shared Models**: Using Pydantic models consistently across the system
   - Each agent has dedicated model files
   - Models are exported through the main `__init__.py`
   - Cross-agent referencing when needed

3. **Unified Exceptions**: Implementing a hierarchy of exceptions for specific error cases
   - Base exceptions for general categories
   - Agent-specific exceptions for detailed error reporting
   - Consistent error handling patterns

## Getting Started

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the example:

```bash
python examples/insurance_navigator_example.py
```

## Development

To extend or modify the system:

1. Follow the modular architecture
2. Add new agent functionality in a dedicated module
3. Use Pydantic for all data models
4. Add appropriate exception types
5. Write comprehensive tests
6. Update the config file

## Troubleshooting

### Database Connection Issues

#### Problem: "role 'postgres' does not exist"

**Symptoms:**
```
ERROR: role "postgres" does not exist
asyncpg.exceptions.InvalidAuthorizationSpecificationError: role "postgres" does not exist
```

**Root Cause:** The application is trying to connect to a PostgreSQL database using the `postgres` user, but you're running a local PostgreSQL instance that uses your system user.

**Solution:**

The system supports both local development and Supabase environments with automatic database URL selection:

1. **For Local Development:** Set `DATABASE_URL_LOCAL` in your `.env` file:
   ```env
   DATABASE_URL_LOCAL="postgresql://your_username@localhost:5432/insurance_navigator"
   ```

2. **For Supabase/Production:** Keep `DATABASE_URL` for Supabase:
   ```env
   DATABASE_URL="postgresql://postgres:password@localhost:5432/insurance_navigator"
   ```

**Precedence:** The system will use `DATABASE_URL_LOCAL` if available, otherwise fall back to `DATABASE_URL`.

#### Problem: "Address already in use" (Port 8000)

**Symptoms:**
```
ERROR: [Errno 48] Address already in use
```

**Solutions:**

1. **Kill existing processes:**
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **Use a different port:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001
   ```

3. **Find what's using the port:**
   ```bash
   lsof -i:8000
   ```

### Environment Variable Issues

#### Problem: "supabase_url is required"

**Symptoms:**
```
ERROR: supabase_url is required
```

**Solution:** Ensure Supabase environment variables are set in `.env`:
```env
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
SUPABASE_STORAGE_BUCKET="documents"
```

#### Problem: "Examples file not found"

**Symptoms:**
```
WARNING - Failed to load examples: Examples file not found: agents/task_requirements/core/prompts/examples/prompt_examples_task_requirements_v0_1.json
```

**Solution:** Ensure all agent example files exist. If missing, check if there's a corresponding `.md` file and convert it, or create the missing JSON file with proper structure.

### Server Startup Issues

#### Problem: Server starts but doesn't respond

**Diagnostic Steps:**

1. **Check if server is running:**
   ```bash
   ps aux | grep "python main.py"
   ```

2. **Check logs for errors:**
   ```bash
   tail -f logs/*.log
   ```

3. **Test health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

4. **Check server binding:**
   ```bash
   netstat -an | grep 8000
   ```

### Quick Diagnostic Commands

```bash
# Check environment variables
env | grep -E "(DATABASE|SUPABASE|JWT)" | sort

# Kill all Python processes (use with caution)
pkill -f python

# Start server with verbose output
python main.py 2>&1 | tee server.log

# Test with minimal environment
export DATABASE_URL_LOCAL="postgresql://$(whoami)@localhost:5432/insurance_navigator"
export SUPABASE_URL="https://placeholder.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="placeholder_key"
python main.py
```

### Environment Setup Verification

Use this checklist to verify your environment:

- [ ] `.env` file exists and is loaded
- [ ] Database URL is set (local or production)
- [ ] Supabase credentials are configured
- [ ] All required agent example files exist
- [ ] No port conflicts on 8000
- [ ] PostgreSQL is running (for local development)
- [ ] All Python dependencies are installed

### Getting Help

If you encounter issues not covered here:

1. Check the logs in the `logs/` directory
2. Verify your `.env` configuration matches `.env.example`
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
4. Try starting the server on a different port to isolate port conflicts

## License

MIT 