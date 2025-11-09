#!/bin/bash
# Test Docker Build and Import Compatibility
# This mimics the Render deployment environment to catch import errors

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Docker Import Compatibility Test"
echo "=========================================="
echo "This test builds the Docker image and checks for import errors"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$PROJECT_ROOT"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not available. Skipping Docker-based test.${NC}"
    echo "  Install Docker to run this test, or use: python3 scripts/test_dependency_compatibility.py"
    exit 1
fi

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
if docker build -t insurance-navigator-test:latest -f Dockerfile . > /tmp/docker-build.log 2>&1; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    echo "Build logs:"
    tail -50 /tmp/docker-build.log
    exit 1
fi
echo ""

# Test imports in the Docker container
echo -e "${YELLOW}Testing imports in Docker container...${NC}"
if docker run --rm insurance-navigator-test:latest python3 -c "
import sys
print('Python version:', sys.version)
print()

# Test pydantic version and with_config
try:
    import pydantic
    version = pydantic.__version__
    print(f'✓ Pydantic version: {version}')
    
    if hasattr(pydantic, 'with_config'):
        print('✓ with_config is available')
    else:
        print('✗ with_config is NOT available')
        sys.exit(1)
except Exception as e:
    print(f'✗ Pydantic import failed: {e}')
    sys.exit(1)

# Test supabase imports
try:
    import supabase
    from supabase_auth import errors
    print('✓ Supabase imports successful')
except Exception as e:
    print(f'✗ Supabase import failed: {e}')
    sys.exit(1)

# Test critical application imports
try:
    from config.environment_loader import load_environment
    from config.configuration_manager import get_config_manager
    from config.database import get_supabase_client
    from db.services.auth_adapter import auth_adapter
    print('✓ Critical application imports successful')
except ImportError as e:
    print(f'✗ Application import failed: {e}')
    sys.exit(1)
except Exception as e:
    # Other exceptions (like missing env vars) are OK for import test
    print(f'⚠ Import succeeded but got exception: {type(e).__name__}')
    print('  (This is OK - likely missing environment variables)')

print()
print('✓ All import tests passed!')
"; then
    echo -e "${GREEN}✓ All imports work correctly in Docker environment${NC}"
    echo ""
    echo -e "${GREEN}✓ Deployment readiness test PASSED${NC}"
    
    # Cleanup
    docker rmi insurance-navigator-test:latest > /dev/null 2>&1 || true
    
    exit 0
else
    echo -e "${RED}✗ Import test failed in Docker environment${NC}"
    echo ""
    echo -e "${RED}✗ Deployment readiness test FAILED${NC}"
    echo ""
    echo "This indicates the same error that would occur in Render deployment."
    echo "Please fix the import errors before deploying."
    
    # Cleanup
    docker rmi insurance-navigator-test:latest > /dev/null 2>&1 || true
    
    exit 1
fi

