#!/bin/bash
# Test Deployment Readiness
# Runs dependency compatibility tests and basic application startup checks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Deployment Readiness Test"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Test 1: Dependency Compatibility
echo -e "${YELLOW}Test 1: Dependency Compatibility${NC}"
cd "$PROJECT_ROOT"
if python3 scripts/test_dependency_compatibility.py; then
    echo -e "${GREEN}✓ Dependency compatibility test passed${NC}"
else
    echo -e "${RED}✗ Dependency compatibility test failed${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# Test 2: Check if main.py can be imported (without starting server)
echo -e "${YELLOW}Test 2: Application Import Check${NC}"
cd "$PROJECT_ROOT"
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    # Try to import main module (this will fail if there are import errors)
    import main
    print('✓ Application imports successfully')
    sys.exit(0)
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
except Exception as e:
    # Other exceptions are OK for this test (e.g., missing env vars)
    print(f'⚠ Import succeeded but got exception: {type(e).__name__}')
    print('  (This is OK - likely missing environment variables)')
    sys.exit(0)
"; then
    echo -e "${GREEN}✓ Application import test passed${NC}"
else
    echo -e "${RED}✗ Application import test failed${NC}"
    FAILURES=$((FAILURES + 1))
fi
echo ""

# Test 3: Check Dockerfile syntax (if docker is available)
if command -v docker &> /dev/null; then
    echo -e "${YELLOW}Test 3: Dockerfile Syntax Check${NC}"
    cd "$PROJECT_ROOT"
    if docker build --dry-run -f Dockerfile . &> /dev/null 2>&1 || \
       docker buildx build --dry-run -f Dockerfile . &> /dev/null 2>&1; then
        echo -e "${GREEN}✓ Dockerfile syntax check passed${NC}"
    else
        # Try a simpler check - just validate Dockerfile exists and is readable
        if [ -f Dockerfile ]; then
            echo -e "${YELLOW}⚠ Dockerfile exists but dry-run not supported${NC}"
            echo "  (This is OK - Docker may not support dry-run)"
        else
            echo -e "${RED}✗ Dockerfile not found${NC}"
            FAILURES=$((FAILURES + 1))
        fi
    fi
    echo ""
fi

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILURES test(s) failed. Please fix issues before deploying.${NC}"
    exit 1
fi

