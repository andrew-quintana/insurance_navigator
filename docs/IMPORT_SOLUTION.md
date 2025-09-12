# Import Solution for Insurance Navigator

## Problem

The Insurance Navigator project has been experiencing persistent "No module named 'agents'" errors throughout the system. This occurs because:

1. **Python Path Issues**: Scripts run from different directories can't find the `agents` module
2. **Inconsistent Import Patterns**: Different parts of the codebase use different import strategies
3. **Missing Error Handling**: Import failures cause crashes instead of graceful degradation
4. **Deployment Environment Differences**: Local vs production environments have different Python path setups

## Solution

We've implemented a comprehensive import solution with the following components:

### 1. Python Path Manager (`utils/python_path_manager.py`)

Centralized Python path management that:
- Automatically detects the project root directory
- Sets up Python paths consistently across all scripts
- Provides validation and error handling for imports
- Tracks module availability and provides recommendations

### 2. Import Utilities (`utils/import_utilities.py`)

Safe import functions that:
- Handle import errors gracefully
- Provide fallback values for missing modules
- Validate module availability before use
- Offer specific import functions for common modules

### 3. Deployment Checks (`scripts/deployment_checks.py`)

Comprehensive deployment validation that:
- Verifies all critical modules can be imported
- Checks environment variables and file structure
- Validates functionality of key components
- Provides detailed error reporting

## Usage

### Basic Usage

```python
# Old way (causes import errors)
from agents.tooling.rag.core import RAGTool

# New way (safe imports)
from utils.import_utilities import safe_import_rag_tool
RAGTool = safe_import_rag_tool()
if RAGTool:
    # Use RAGTool
    pass
```

### Advanced Usage

```python
# Setup Python paths
from utils.python_path_manager import setup_python_path
path_manager = setup_python_path()

# Validate imports
from utils.import_utilities import validate_agents_imports
results = validate_agents_imports()

# Get detailed report
from utils.import_utilities import get_import_status_report
report = get_import_status_report()
```

### Context Manager Usage

```python
from utils.import_utilities import SafeImportContext

with SafeImportContext(['agents', 'agents.tooling.rag.core']) as modules:
    agents = modules['agents']
    rag_core = modules['agents.tooling.rag.core']
    # Use modules safely
```

## Available Import Functions

### Core Agents
- `safe_import_agents()` - Import agents module
- `safe_import_base_agent()` - Import BaseAgent class
- `safe_import_rag_tool()` - Import RAGTool class
- `safe_import_retrieval_config()` - Import RetrievalConfig class

### Patient Navigator
- `safe_import_information_retrieval_agent()` - Import InformationRetrievalAgent
- `safe_import_information_retrieval_input()` - Import InformationRetrievalInput
- `safe_import_information_retrieval_output()` - Import InformationRetrievalOutput
- `safe_import_patient_navigator_chat_interface()` - Import PatientNavigatorChatInterface
- `safe_import_chat_message()` - Import ChatMessage class
- `safe_import_supervisor_workflow()` - Import SupervisorWorkflow
- `safe_import_workflow_prescription_agent()` - Import WorkflowPrescriptionAgent

### Shared Services
- `safe_import_database_manager()` - Import DatabaseManager
- `safe_import_storage_manager()` - Import StorageManager
- `safe_import_service_router()` - Import ServiceRouter
- `safe_import_worker_config()` - Import WorkerConfig
- `safe_import_enhanced_service_client()` - Import EnhancedServiceClient
- `safe_import_error_handler()` - Import WorkerErrorHandler

## Migration Guide

### Step 1: Update Imports

Replace direct imports with safe imports:

```python
# Before
from agents.tooling.rag.core import RAGTool, RetrievalConfig
from agents.patient_navigator.information_retrieval import InformationRetrievalAgent

# After
from utils.import_utilities import (
    safe_import_rag_tool,
    safe_import_retrieval_config,
    safe_import_information_retrieval_agent
)

RAGTool = safe_import_rag_tool()
RetrievalConfig = safe_import_retrieval_config()
InformationRetrievalAgent = safe_import_information_retrieval_agent()
```

### Step 2: Add Error Handling

Add proper error handling for missing modules:

```python
# Before
from agents.tooling.rag.core import RAGTool
rag_tool = RAGTool(user_id)

# After
from utils.import_utilities import safe_import_rag_tool

RAGTool = safe_import_rag_tool()
if not RAGTool:
    raise HTTPException(
        status_code=500,
        detail="RAG service temporarily unavailable"
    )

rag_tool = RAGTool(user_id)
```

### Step 3: Update Test Scripts

Update test scripts to use safe imports:

```python
# Add at the beginning of test scripts
from utils.import_utilities import setup_python_path
setup_python_path()

# Then use safe imports
from utils.import_utilities import safe_import_rag_tool
RAGTool = safe_import_rag_tool()
```

## Deployment

### Pre-deployment Checks

Run the deployment checks before deploying:

```bash
python scripts/deployment_checks.py
```

This will validate:
- Python path setup
- File structure
- Environment variables
- Database connectivity
- Module imports
- Functionality tests

### Environment Setup

Ensure the following environment variables are set:

```bash
export DATABASE_URL="your_database_url"
export SUPABASE_URL="your_supabase_url"
export SUPABASE_ANON_KEY="your_supabase_anon_key"
export SUPABASE_SERVICE_ROLE_KEY="your_supabase_service_role_key"
```

### Docker Deployment

For Docker deployments, ensure the working directory is set correctly:

```dockerfile
WORKDIR /app
COPY . .
# Python path will be set up automatically
```

## Best Practices

### 1. Always Use Safe Imports

Never use direct imports for project modules:

```python
# ❌ Don't do this
from agents.tooling.rag.core import RAGTool

# ✅ Do this instead
from utils.import_utilities import safe_import_rag_tool
RAGTool = safe_import_rag_tool()
```

### 2. Handle Missing Modules Gracefully

Always check if modules are available before using them:

```python
RAGTool = safe_import_rag_tool()
if not RAGTool:
    # Handle missing module gracefully
    return {"error": "RAG service unavailable"}
```

### 3. Use Context Managers for Multiple Imports

When importing multiple modules, use the context manager:

```python
from utils.import_utilities import SafeImportContext

with SafeImportContext(['agents', 'agents.tooling.rag.core']) as modules:
    agents = modules['agents']
    rag_core = modules['agents.tooling.rag.core']
```

### 4. Validate Imports in Tests

Always validate imports in test scripts:

```python
from utils.import_utilities import validate_agents_imports

def test_imports():
    results = validate_agents_imports()
    assert results['agents'], "Agents module not available"
    assert results['rag_tool'], "RAGTool not available"
```

## Troubleshooting

### Common Issues

1. **"No module named 'agents'"**
   - Solution: Use `safe_import_agents()` instead of direct import
   - Check that `utils/import_utilities.py` is in the Python path

2. **"Module not found" errors**
   - Solution: Run `python scripts/deployment_checks.py` to diagnose
   - Check that all required files exist in the project structure

3. **Import errors in production**
   - Solution: Ensure working directory is set correctly
   - Check that all dependencies are installed

### Debugging

Use the import status report to debug issues:

```python
from utils.import_utilities import get_import_status_report

report = get_import_status_report()
print(f"Success rate: {report['success_rate']:.2%}")
for module, success in report['validation_results'].items():
    print(f"{'✅' if success else '❌'} {module}")
```

## Testing

Run the import solution test:

```bash
python test_import_solution.py
```

This will test both the old way (that causes errors) and the new way (that works).

## Benefits

1. **Eliminates Import Errors**: No more "No module named 'agents'" errors
2. **Graceful Degradation**: System continues to work even if some modules are missing
3. **Better Error Handling**: Clear error messages and fallback behavior
4. **Consistent Behavior**: Same import behavior across all environments
5. **Easy Debugging**: Comprehensive validation and reporting tools
6. **Future-Proof**: Easy to add new modules and import functions

## Conclusion

This import solution provides a robust, scalable approach to handling module imports in the Insurance Navigator project. By using safe imports and proper error handling, we can eliminate the persistent import errors and ensure the system works reliably across all environments.
