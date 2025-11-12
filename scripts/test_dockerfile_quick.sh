#!/bin/bash
# Quick test script for FM-042 Dockerfile changes
# Tests syntax and basic structure without full build

set -e

echo "🔍 Quick Dockerfile Validation"
echo "==============================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Check for conflicting flags
echo "1️⃣ Checking for removed conflicting flags..."
echo "-------------------------------------------"

if grep -q "PIP_NO_CACHE_DIR" Dockerfile; then
    echo -e "${RED}❌ PIP_NO_CACHE_DIR still present${NC}"
    exit 1
else
    echo -e "${GREEN}✅ PIP_NO_CACHE_DIR removed${NC}"
fi

if grep -q "\-\-no-cache-dir" Dockerfile; then
    echo -e "${RED}❌ --no-cache-dir still present${NC}"
    exit 1
else
    echo -e "${GREEN}✅ --no-cache-dir removed${NC}"
fi

if grep -q "\-\-force-reinstall" Dockerfile; then
    echo -e "${RED}❌ --force-reinstall still present${NC}"
    exit 1
else
    echo -e "${GREEN}✅ --force-reinstall removed${NC}"
fi
echo ""

# Test 2: Verify cache mount is present
echo "2️⃣ Checking cache mount configuration..."
echo "----------------------------------------"
if grep -q "type=cache,target=/home/app/.cache/pip" Dockerfile; then
    echo -e "${GREEN}✅ Cache mount configured${NC}"
else
    echo -e "${RED}❌ Cache mount missing${NC}"
    exit 1
fi
echo ""

# Test 3: Verify constraints file is used
echo "3️⃣ Checking constraints file usage..."
echo "------------------------------------"
if grep -q "constraints.txt" Dockerfile; then
    echo -e "${GREEN}✅ Constraints file referenced${NC}"
    grep "constraints.txt" Dockerfile | head -1
else
    echo -e "${RED}❌ Constraints file not referenced${NC}"
    exit 1
fi
echo ""

# Test 4: Verify selective COPY commands
echo "4️⃣ Checking selective COPY commands..."
echo "--------------------------------------"
REQUIRED_COPIES=("main.py" "api/" "config/" "core/" "db/" "utils/" "agents/" "backend/")
MISSING=0

for item in "${REQUIRED_COPIES[@]}"; do
    if grep -q "COPY.*$item" Dockerfile; then
        echo -e "${GREEN}✅ $item copied${NC}"
    else
        echo -e "${RED}❌ $item not found in COPY commands${NC}"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    exit 1
fi
echo ""

# Test 5: Verify no wildcard COPY
echo "5️⃣ Checking for wildcard COPY (should be removed)..."
echo "---------------------------------------------------"
if grep -q "COPY.*\\. \\.$" Dockerfile || grep -q "COPY.*\\. \\./" Dockerfile; then
    echo -e "${YELLOW}⚠️  Wildcard COPY found - this copies everything${NC}"
    echo "   Consider using selective COPY instead"
else
    echo -e "${GREEN}✅ No wildcard COPY found${NC}"
fi
echo ""

# Test 6: Verify main.py entry point
echo "6️⃣ Checking entry point..."
echo "--------------------------"
if grep -q "uvicorn main:app" Dockerfile; then
    echo -e "${GREEN}✅ Entry point correct (main:app)${NC}"
else
    echo -e "${RED}❌ Entry point incorrect${NC}"
    exit 1
fi
echo ""

# Test 7: Check required files exist
echo "7️⃣ Checking required files exist..."
echo "----------------------------------"
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py not found${NC}"
    exit 1
else
    echo -e "${GREEN}✅ main.py exists${NC}"
fi

if [ ! -f "constraints.txt" ]; then
    echo -e "${RED}❌ constraints.txt not found${NC}"
    exit 1
else
    echo -e "${GREEN}✅ constraints.txt exists${NC}"
fi

if [ ! -f "requirements-api.txt" ]; then
    echo -e "${RED}❌ requirements-api.txt not found${NC}"
    exit 1
else
    echo -e "${GREEN}✅ requirements-api.txt exists${NC}"
fi
echo ""

# Test 8: Verify constraints.txt has pydantic 2.9.0
echo "8️⃣ Checking constraints.txt content..."
echo "--------------------------------------"
if grep -q "pydantic==2.9.0" constraints.txt; then
    echo -e "${GREEN}✅ pydantic==2.9.0 in constraints.txt${NC}"
else
    echo -e "${RED}❌ pydantic==2.9.0 not found in constraints.txt${NC}"
    exit 1
fi
echo ""

echo "===================================="
echo -e "${GREEN}✅ All quick validation tests passed!${NC}"
echo ""
echo "Next: Run full build test:"
echo "  ./scripts/test_dockerfile_fm042.sh"
echo ""
echo "Or test build manually:"
echo "  docker build -t test-image ."
echo ""

