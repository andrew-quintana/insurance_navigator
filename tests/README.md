# Test Organization

This directory contains all test files organized by category and purpose.

## Directory Structure

### Core Tests (`tests/`)
- **Unit tests**: Individual component testing
- **Integration tests**: Cross-component testing
- **Feature tests**: End-to-end feature testing

### Debug Tests (`tests/debug/`)
- **Incident-specific tests**: Tests for specific incidents (e.g., `fm_027/`)
- **Debugging utilities**: Tools for investigating issues
- **Troubleshooting scripts**: One-off diagnostic tests

### Feature-Specific Tests
- **`tests/agents/`**: Agent-related tests
- **`tests/initiatives/`**: Initiative-specific tests
- **`tests/unit/`**: Unit tests by component

## Test Categories

### By Incident
- **`tests/fm_027/`**: FM-027 Worker Storage Access tests
- **`tests/debug/fm_027/`**: FM-027 debugging tests

### By Component
- **`tests/unit/core/`**: Core service tests
- **`tests/unit/backend/`**: Backend component tests

### By Initiative
- **`tests/initiatives/system/upload_refactor/`**: Upload pipeline refactor tests

## Security Guidelines

### ✅ Allowed
- Environment variable references: `os.getenv("API_KEY")`
- Test placeholders: `"test-key"`, `"sk-test-key"`
- Mock values: `"mock_value"`

### ❌ Prohibited
- Hardcoded production keys
- Real API keys in source code
- Production database credentials
- JWT secrets in test files

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### By Category
```bash
# Unit tests
pytest tests/unit/ -v

# Debug tests
pytest tests/debug/ -v

# Specific incident
pytest tests/fm_027/ -v
```

### By Pattern
```bash
# All FM-027 tests
pytest tests/ -k "fm_027" -v

# Storage-related tests
pytest tests/ -k "storage" -v
```

## Test Naming Convention

- **Test files**: `test_<feature>_<purpose>.py`
- **Test functions**: `test_<scenario>_<expected_result>`
- **Debug tests**: `test_<incident>_<debug_purpose>.py`

## Environment Setup

Tests use environment variables from:
- `.env.development` (local development)
- `.env.staging` (staging environment)
- `.env.production` (production environment)

Load with:
```python
from dotenv import load_dotenv
load_dotenv('.env.staging')
```