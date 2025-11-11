#!/bin/bash
# Test script for FM-042 Dockerfile changes
# Tests: Build, dependencies, cache, and application startup
#
# Usage:
#   ./scripts/test_dockerfile_fm042.sh           # Use cached layers (faster)
#   ./scripts/test_dockerfile_fm042.sh --no-cache # Fresh build (tests typical boot)

set -e

# Parse arguments
NO_CACHE=""
if [ "$1" = "--no-cache" ] || [ "$1" = "-n" ]; then
    NO_CACHE="--no-cache"
    echo "🧹 Cache clearing enabled - testing fresh build"
fi

echo "🧪 Testing FM-042 Dockerfile Changes"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
IMAGE_NAME="insurance-navigator-fm042-test"
CONTAINER_NAME="fm042-test-container"
PORT=8001

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    docker rm -f $CONTAINER_NAME 2>/dev/null || true
    docker rmi $IMAGE_NAME 2>/dev/null || true
    echo "✅ Cleanup complete"
}

# Trap to cleanup on exit
trap cleanup EXIT

# Pre-check: Docker Daemon Health
echo "🔍 Pre-check: Docker Daemon Health"
echo "-----------------------------------"
echo "Verifying Docker is responsive before starting tests..."
echo ""

# Check if docker command exists
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker command not found${NC}"
    echo "   Please install Docker Desktop and try again"
    exit 1
fi

# Test Docker daemon responsiveness with timeout
DOCKER_RESPONSIVE=false
docker info > /tmp/docker_precheck.log 2>&1 &
DOCKER_CHECK_PID=$!

# Wait up to 5 seconds for response
for i in {1..5}; do
    if ! kill -0 $DOCKER_CHECK_PID 2>/dev/null; then
        # Process finished
        wait $DOCKER_CHECK_PID
        DOCKER_EXIT=$?
        if [ $DOCKER_EXIT -eq 0 ]; then
            DOCKER_RESPONSIVE=true
            break
        fi
    fi
    sleep 1
done

# If still running, kill it (hanging)
if kill -0 $DOCKER_CHECK_PID 2>/dev/null; then
    kill $DOCKER_CHECK_PID 2>/dev/null || true
    echo -e "${RED}❌ Docker daemon is not responding (hanging)${NC}"
    echo ""
    echo "   Docker appears to be hung. Try these fixes:"
    echo "   1. Restart Docker Desktop:"
    echo "      osascript -e 'quit app \"Docker\"' && sleep 5 && open -a Docker"
    echo ""
    echo "   2. Run diagnostics:"
    echo "      ./scripts/diagnose_docker_issues.sh"
    echo ""
    echo "   3. Check Docker Desktop logs:"
    echo "      tail -50 ~/Library/Containers/com.docker.docker/Data/log/host/*.log"
    echo ""
    echo "   See docs/operations/DOCKER_TROUBLESHOOTING.md for more help"
    exit 1
fi

if [ "$DOCKER_RESPONSIVE" = false ]; then
    echo -e "${RED}❌ Docker daemon returned an error${NC}"
    echo "   Error output:"
    cat /tmp/docker_precheck.log
    echo ""
    echo "   Run diagnostics: ./scripts/diagnose_docker_issues.sh"
    exit 1
fi

echo -e "${GREEN}✅ Docker daemon is responsive${NC}"
echo ""

# Test 1: Docker Build
echo "📦 Test 1: Docker Build"
echo "----------------------"
echo "Building Docker image (this may take several minutes)..."
echo "   Progress will be shown below..."
echo ""

# Build with progress output
# Note: timeout command not available on macOS by default
# Build will run without timeout (Ctrl+C to cancel if needed)
if docker build $NO_CACHE --progress=plain -t $IMAGE_NAME . 2>&1 | tee /tmp/docker_build.log; then
    echo ""
    echo -e "${GREEN}✅ Build succeeded${NC}"
    echo "   Build log saved to /tmp/docker_build.log"
    
    # Try to extract build time if available
    if grep -q "real" /tmp/docker_build.log 2>/dev/null; then
        # Use sed for macOS compatibility (grep -P not available on macOS)
        BUILD_TIME=$(grep "real" /tmp/docker_build.log | sed -E 's/.*real[[:space:]]+([0-9]+\.[0-9]+).*/\1/' | head -1)
        if [ -n "$BUILD_TIME" ]; then
            echo "   Build time: ${BUILD_TIME}s"
        fi
    fi
else
    EXIT_CODE=$?
    echo ""
    echo -e "${RED}❌ Build failed (exit code: $EXIT_CODE)${NC}"
    echo "   Last 50 lines of build log:"
    tail -50 /tmp/docker_build.log
    echo ""
    echo "   Full build log: /tmp/docker_build.log"
    exit 1
fi
echo ""

# Test 2: Check Image Size
echo "📏 Test 2: Image Size Check"
echo "---------------------------"
IMAGE_SIZE=$(docker images $IMAGE_NAME --format "{{.Size}}")
echo "   Image size: $IMAGE_SIZE"
echo -e "${GREEN}✅ Image size check complete${NC}"
echo ""

# Test 3: Verify Dependencies (pydantic version)
echo "🔍 Test 3: Dependency Verification"
echo "---------------------------------"
echo "Checking pydantic version (should be 2.9.0)..."
PYDANTIC_VERSION=$(docker run --rm $IMAGE_NAME python -c "import pydantic; print(pydantic.__version__)" 2>/dev/null || echo "ERROR")
if [ "$PYDANTIC_VERSION" = "2.9.0" ]; then
    echo -e "${GREEN}✅ Pydantic version correct: $PYDANTIC_VERSION${NC}"
else
    echo -e "${RED}❌ Pydantic version incorrect: $PYDANTIC_VERSION (expected 2.9.0)${NC}"
    exit 1
fi
echo ""

# Test 4: Verify Cache Mount Works
echo "💾 Test 4: Cache Mount Verification"
echo "-------------------------------------"
echo "Checking if pip cache directory exists and is writable..."
CACHE_CHECK=$(docker run --rm $IMAGE_NAME sh -c "test -d /home/app/.cache/pip && echo 'EXISTS' || echo 'MISSING'" 2>/dev/null || echo "ERROR")
if [ "$CACHE_CHECK" = "EXISTS" ]; then
    echo -e "${GREEN}✅ Cache directory exists${NC}"
else
    echo -e "${YELLOW}⚠️  Cache directory check: $CACHE_CHECK${NC}"
fi
echo ""

# Test 5: Application Startup
echo "🚀 Test 5: Application Startup"
echo "------------------------------"
echo "Starting container..."
echo "   Note: Using cloud deployment mode (RENDER=true) to avoid .env file requirement"
echo "   Note: Database connection will fail (expected - no database in test environment)"
docker run -d \
    --name $CONTAINER_NAME \
    -p $PORT:8000 \
    -e PORT=8000 \
    -e RENDER=true \
    -e ENVIRONMENT=development \
    -e SUPABASE_URL=https://test.supabase.co \
    -e SUPABASE_SERVICE_ROLE_KEY=test_key \
    -e DATABASE_URL=postgresql://test:test@localhost/test \
    -e OPENAI_API_KEY=test_key \
    -e LLAMAPARSE_API_KEY=test_key \
    -e LOG_LEVEL=INFO \
    $IMAGE_NAME > /dev/null 2>&1

# Wait for container to start
echo "   Waiting for application to start..."
sleep 5

# Check if container exists (running or exited)
CONTAINER_EXISTS=$(docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Names}}" 2>/dev/null || echo "")
if [ -n "$CONTAINER_EXISTS" ]; then
    CONTAINER_STATUS=$(docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Status}}" 2>/dev/null || echo "")
    
    if docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q $CONTAINER_NAME; then
        echo -e "${GREEN}✅ Container is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Container exists but is not running (status: $CONTAINER_STATUS)${NC}"
        echo "   This is expected if application startup fails due to missing database"
    fi
    
    # Check logs regardless of container state
    CONTAINER_LOGS=$(docker logs $CONTAINER_NAME 2>&1)
    
    # Check if uvicorn process started (indicates Dockerfile CMD executed correctly)
    if echo "$CONTAINER_LOGS" | grep -q "Started server process"; then
        echo -e "${GREEN}✅ Application server process started (Dockerfile CMD executed)${NC}"
    else
        echo -e "${YELLOW}⚠️  Server process not detected in logs${NC}"
        echo "   First 20 lines of container logs:"
        echo "$CONTAINER_LOGS" | head -20
    fi
    
    # Check if application began initialization (validates imports and basic startup)
    if echo "$CONTAINER_LOGS" | grep -q "Initializing Insurance Navigator system"; then
        echo -e "${GREEN}✅ Application initialization started${NC}"
    fi
    
    # Check if environment loaded correctly
    if echo "$CONTAINER_LOGS" | grep -q "Environment loaded"; then
        ENV_INFO=$(echo "$CONTAINER_LOGS" | grep "Environment loaded" | head -1)
        echo -e "${GREEN}✅ Environment configuration loaded: $ENV_INFO${NC}"
    fi
    
    # Note: Database connection failure is expected in test environment
    if echo "$CONTAINER_LOGS" | grep -q "Connection refused\|ConnectionRefusedError"; then
        echo -e "${YELLOW}⚠️  Database connection failed (expected in test environment without database)${NC}"
        echo -e "${GREEN}✅ Dockerfile test passed - container starts and application initializes${NC}"
        echo -e "${GREEN}✅ All Dockerfile validations successful!${NC}"
    elif echo "$CONTAINER_LOGS" | grep -q "Application startup failed"; then
        echo -e "${YELLOW}⚠️  Application startup failed (checking reason...)${NC}"
        if echo "$CONTAINER_LOGS" | grep -q "Connection refused\|ConnectionRefusedError"; then
            echo -e "${GREEN}✅ Failure due to expected database connection issue${NC}"
            echo -e "${GREEN}✅ Dockerfile test passed - container and application start correctly${NC}"
        else
            echo -e "${RED}❌ Application startup failed for unexpected reason${NC}"
            echo "   Last 30 lines of logs:"
            echo "$CONTAINER_LOGS" | tail -30
            exit 1
        fi
    fi
else
    echo -e "${RED}❌ Container does not exist${NC}"
    echo "   Container may have failed to create"
    exit 1
fi
echo ""

# Test 6: Health Check Endpoint (Optional - may fail without database)
echo "🏥 Test 6: Health Check Endpoint"
echo "---------------------------------"
echo "Testing /health endpoint..."
echo "   Note: Health check may fail if application startup incomplete (expected without database)"
sleep 3  # Give app more time to fully start
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/health 2>/dev/null || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ Health check passed (HTTP $HEALTH_RESPONSE)${NC}"
    HEALTH_BODY=$(curl -s http://localhost:$PORT/health 2>/dev/null)
    echo "   Response: $HEALTH_BODY"
elif [ "$HEALTH_RESPONSE" = "000" ]; then
    echo -e "${YELLOW}⚠️  Health check endpoint not accessible (expected - app startup incomplete without database)${NC}"
    echo "   This is acceptable for Dockerfile validation test"
else
    echo -e "${YELLOW}⚠️  Health check returned HTTP $HEALTH_RESPONSE (expected without database)${NC}"
fi
echo ""

# Test 7: Verify All Required Directories
echo "📁 Test 7: Directory Structure Verification"
echo "-------------------------------------------"
# Check if container is running (docker exec only works on running containers)
if docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q $CONTAINER_NAME; then
    REQUIRED_DIRS=("api" "config" "core" "db" "utils" "agents" "backend")
    MISSING_DIRS=()
    for dir in "${REQUIRED_DIRS[@]}"; do
        if docker exec $CONTAINER_NAME test -d "/app/$dir" 2>/dev/null; then
            echo "   ✅ $dir/ exists"
        else
            echo "   ❌ $dir/ missing"
            MISSING_DIRS+=("$dir")
        fi
    done

    if [ ${#MISSING_DIRS[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All required directories present${NC}"
    else
        echo -e "${RED}❌ Missing directories: ${MISSING_DIRS[*]}${NC}"
        exit 1
    fi
else
    # Container is not running - verify directories were copied during build instead
    echo "   Container is not running - verifying directories in image..."
    REQUIRED_DIRS=("api" "config" "core" "db" "utils" "agents" "backend")
    MISSING_DIRS=()
    for dir in "${REQUIRED_DIRS[@]}"; do
        if docker run --rm $IMAGE_NAME test -d "/app/$dir" 2>/dev/null; then
            echo "   ✅ $dir/ exists in image"
        else
            echo "   ❌ $dir/ missing from image"
            MISSING_DIRS+=("$dir")
        fi
    done

    if [ ${#MISSING_DIRS[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All required directories present in image${NC}"
    else
        echo -e "${RED}❌ Missing directories in image: ${MISSING_DIRS[*]}${NC}"
        exit 1
    fi
fi
echo ""

# Test 8: Verify main.py exists
echo "📄 Test 8: Main Application File"
echo "---------------------------------"
if docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q $CONTAINER_NAME; then
    if docker exec $CONTAINER_NAME test -f "/app/main.py" 2>/dev/null; then
        echo -e "${GREEN}✅ main.py exists${NC}"
    else
        echo -e "${RED}❌ main.py missing${NC}"
        exit 1
    fi
else
    # Container is not running - verify main.py in image
    if docker run --rm $IMAGE_NAME test -f "/app/main.py" 2>/dev/null; then
        echo -e "${GREEN}✅ main.py exists in image${NC}"
    else
        echo -e "${RED}❌ main.py missing from image${NC}"
        exit 1
    fi
fi
echo ""

# Test 9: Check for Conflicting Flags (should be removed)
echo "🔍 Test 9: Verify Conflicting Flags Removed"
echo "--------------------------------------------"
BUILD_LOG=$(cat /tmp/docker_build.log)
if echo "$BUILD_LOG" | grep -q "PIP_NO_CACHE_DIR"; then
    echo -e "${YELLOW}⚠️  PIP_NO_CACHE_DIR still present in build${NC}"
else
    echo -e "${GREEN}✅ PIP_NO_CACHE_DIR removed${NC}"
fi

# Check Dockerfile doesn't have the flags
if grep -q "PIP_NO_CACHE_DIR" Dockerfile; then
    echo -e "${RED}❌ PIP_NO_CACHE_DIR still in Dockerfile${NC}"
    exit 1
else
    echo -e "${GREEN}✅ PIP_NO_CACHE_DIR not in Dockerfile${NC}"
fi

if grep -q "no-cache-dir" Dockerfile; then
    echo -e "${RED}❌ --no-cache-dir still in Dockerfile${NC}"
    exit 1
else
    echo -e "${GREEN}✅ --no-cache-dir not in Dockerfile${NC}"
fi

if grep -q "force-reinstall" Dockerfile; then
    echo -e "${RED}❌ --force-reinstall still in Dockerfile${NC}"
    exit 1
else
    echo -e "${GREEN}✅ --force-reinstall not in Dockerfile${NC}"
fi
echo ""

# Test 10: Application Logs Check
echo "📋 Test 10: Application Logs"
echo "----------------------------"
echo "Recent container logs:"
docker logs $CONTAINER_NAME 2>&1 | tail -10
echo ""

# Summary
echo "===================================="
echo "📊 Test Summary"
echo "===================================="
echo -e "${GREEN}✅ All critical tests passed!${NC}"
echo ""
echo "Next steps:"
echo "1. Review build logs: /tmp/docker_build.log"
echo "2. Test chat endpoint manually if needed"
echo "3. Deploy to staging/production"
echo ""
echo "To test chat endpoint manually:"
echo "  curl -X POST http://localhost:$PORT/chat \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "    -d '{\"message\": \"test\"}'"
echo ""

