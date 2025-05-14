#!/bin/bash
# setup_test_env.sh - Script to set up an isolated test environment

# Ensure we're in the project root
PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd $PROJECT_ROOT

echo "Setting up isolated test environment for insurance_navigator..."

# Create a dedicated test virtual environment if it doesn't exist
if [ ! -d ".venv-test" ]; then
    echo "Creating test virtual environment..."
    python3 -m venv .venv-test
else
    echo "Test virtual environment already exists."
fi

# Activate the test environment
source .venv-test/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install development dependencies
echo "Installing development dependencies from requirements-dev.txt..."
pip install -r requirements-dev.txt

# Install the project in development mode
echo "Installing project in development mode..."
pip install -e .

# Create necessary directories
mkdir -p logs/agents
mkdir -p logs/langsmith

# Set environment variables for testing
export PYTHONPATH=$PROJECT_ROOT
export LANGCHAIN_API_KEY="${LANGCHAIN_API_KEY:-your_langsmith_api_key}"
export LANGCHAIN_PROJECT="insurance_navigator_test"
export LANGCHAIN_TRACING_V2="true"

echo "Test environment setup complete. Activated at .venv-test"
echo "Use 'source .venv-test/bin/activate' to activate the test environment."
echo ""
echo "Current environment:"
echo "-------------------"
echo "Python: $(which python)"
echo "NumPy version: $(python -c 'import numpy; print(numpy.__version__)')"
echo "LangSmith project: $LANGCHAIN_PROJECT"
echo ""
echo "Run tests with: python -m pytest agents/patient_navigator/tests/unit/test_patient_navigator.py -v" 