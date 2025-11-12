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

# Check if Docker daemon is running (with timeout to prevent hang)
echo -e "${YELLOW}Checking Docker daemon...${NC}"
if command -v timeout &> /dev/null; then
    if ! timeout 5 docker info > /dev/null 2>&1; then
        echo -e "${RED}✗ Docker daemon is not running or not accessible.${NC}"
        echo "  Please start Docker Desktop or Docker daemon and try again."
        echo "  Error: Docker daemon check timed out or failed"
        exit 1
    fi
else
    # Fallback for macOS without timeout - use a background process
    docker info > /dev/null 2>&1 &
    DOCKER_CHECK_PID=$!
    sleep 2
    if ! kill -0 $DOCKER_CHECK_PID 2>/dev/null; then
        wait $DOCKER_CHECK_PID
        DOCKER_EXIT=$?
        if [ $DOCKER_EXIT -ne 0 ]; then
            echo -e "${RED}✗ Docker daemon is not running or not accessible.${NC}"
            echo "  Please start Docker Desktop or Docker daemon and try again."
            exit 1
        fi
    else
        # Still running after 2 seconds - likely hanging
        kill $DOCKER_CHECK_PID 2>/dev/null
        echo -e "${RED}✗ Docker daemon check is hanging - Docker may not be running.${NC}"
        echo "  Please start Docker Desktop and try again."
        exit 1
    fi
fi
echo -e "${GREEN}✓ Docker daemon is running${NC}"
echo ""

# Build the Docker image with progress output
echo -e "${YELLOW}Building Docker image...${NC}"
echo "This may take 5-10 minutes on first build (compiling cryptography, numpy, etc.)"
echo "Progress will be shown below..."
echo ""

# Set build timeout (20 minutes should be enough even for slow systems)
BUILD_TIMEOUT=1200

# Check if timeout command is available (not on macOS by default)
if command -v timeout &> /dev/null; then
    TIMEOUT_CMD="timeout $BUILD_TIMEOUT"
    TIMEOUT_AVAILABLE=true
else
    TIMEOUT_CMD=""
    TIMEOUT_AVAILABLE=false
    echo -e "${YELLOW}⚠ timeout command not available - build will not have automatic timeout${NC}"
    echo "  If build hangs, press Ctrl+C to cancel"
    echo ""
fi

# Build with progress output and log to file simultaneously
# Use timeout to prevent infinite hangs (if available)
if $TIMEOUT_CMD docker build --progress=plain -t insurance-navigator-test:latest -f Dockerfile . 2>&1 | tee /tmp/docker-build.log; then
    echo ""
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    EXIT_CODE=$?
    echo ""
    if [ "$TIMEOUT_AVAILABLE" = true ] && [ $EXIT_CODE -eq 124 ]; then
        echo -e "${RED}✗ Docker build timed out after $((BUILD_TIMEOUT / 60)) minutes${NC}"
        echo "  This usually indicates a network issue or a package that's taking too long to compile."
        echo "  Check the build log for which package was being installed when it hung."
    else
        echo -e "${RED}✗ Docker build failed${NC}"
    fi
    echo ""
    echo "Last 50 lines of build log:"
    tail -50 /tmp/docker-build.log
    echo ""
    echo "Full log available at: /tmp/docker-build.log"
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

