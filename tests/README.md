# Testing Environment for Insurance Navigator

This directory contains tests and test utilities for the Insurance Navigator project.

## Setup

We've implemented an isolated test environment to ensure consistent test results across different machines and to prevent conflicts with development dependencies.

### Quick Start

1. Run the setup script:
   ```bash
   bash scripts/setup_test_env.sh
   ```

2. Activate the test environment:
   ```bash
   source .venv-test/bin/activate
   ```

3. Run the tests:
   ```bash
   python -m pytest agents/patient_navigator/tests/unit/test_patient_navigator.py -v
   ```

### Manual Setup

If you prefer to set up the environment manually:

1. Create a virtual environment:
   ```bash
   python -m venv .venv-test
   source .venv-test/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

3. Set environment variables:
   ```bash
   export PYTHONPATH=$(pwd)
   export LANGCHAIN_API_KEY="your_langsmith_api_key"
   export LANGCHAIN_PROJECT="insurance_navigator_test"
   export LANGCHAIN_TRACING_V2="true"
   ```

## LangSmith Integration

The testing environment integrates with LangSmith for tracing and evaluation:

1. Tests with mocked LLMs will not generate traces in LangSmith
2. Real agent executions will be traced and can be viewed in the LangSmith UI
3. Test runs are tagged with metadata for easy filtering

To view traces:
1. Go to [https://smith.langchain.com/](https://smith.langchain.com/)
2. Log in with your credentials
3. Select the "insurance_navigator_test" project
4. Filter by metadata like agent_name, run_type, etc.

## Environment Compatibility

The test environment uses pinned dependency versions to ensure compatibility:

- NumPy 1.24.4 (compatible with sentence-transformers and other dependencies)
- Other dependencies as specified in requirements-dev.txt

If you encounter dependency conflicts, please update the requirements-dev.txt file and report the issue. 