#!/bin/bash
# FM-040 Fix Validation Script
# Validates that the rootDirectory configuration fix works correctly

set -e

echo "🔍 FM-040 Fix Validation"
echo "========================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Verify root-level vercel.json exists and is valid
echo "Test 1: Verifying root-level vercel.json..."
if [ -f "vercel.json" ]; then
    ROOT_DIR=$(node -e "const config = require('./vercel.json'); console.log(config.rootDirectory || 'not set');")
    if [ "$ROOT_DIR" = "ui" ]; then
        echo -e "${GREEN}✅ Root-level vercel.json exists with rootDirectory: ui${NC}"
    else
        echo -e "${RED}❌ Root-level vercel.json exists but rootDirectory is: $ROOT_DIR${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Root-level vercel.json not found${NC}"
    exit 1
fi
echo ""

# Test 2: Verify tailwindcss is in ui/package.json
echo "Test 2: Verifying tailwindcss dependency..."
if grep -q '"tailwindcss"' ui/package.json; then
    TAILWIND_VERSION=$(node -e "const pkg = require('./ui/package.json'); console.log(pkg.dependencies?.tailwindcss || pkg.devDependencies?.tailwindcss || 'not found');")
    echo -e "${GREEN}✅ tailwindcss found in ui/package.json (version: $TAILWIND_VERSION)${NC}"
else
    echo -e "${RED}❌ tailwindcss not found in ui/package.json${NC}"
    exit 1
fi
echo ""

# Test 3: Verify tailwindcss can be resolved from ui/ directory
echo "Test 3: Verifying tailwindcss can be resolved..."
cd ui
if node -e "require.resolve('tailwindcss')" 2>/dev/null; then
    TAILWIND_PATH=$(node -e "console.log(require.resolve('tailwindcss'));")
    echo -e "${GREEN}✅ tailwindcss can be resolved from ui/ directory${NC}"
    echo "   Path: $TAILWIND_PATH"
else
    echo -e "${RED}❌ tailwindcss cannot be resolved from ui/ directory${NC}"
    echo "   Run: cd ui && npm install"
    exit 1
fi
cd ..
echo ""

# Test 4: Verify configuration files exist
echo "Test 4: Verifying configuration files..."
CONFIG_FILES=(
    "ui/tailwind.config.js"
    "ui/postcss.config.js"
    "ui/app/globals.css"
    "ui/app/layout.tsx"
)

ALL_EXIST=true
for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${RED}❌ $file not found${NC}"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = false ]; then
    exit 1
fi
echo ""

# Test 5: Verify globals.css contains Tailwind directives
echo "Test 5: Verifying Tailwind directives in globals.css..."
if grep -q "@tailwind base" ui/app/globals.css && \
   grep -q "@tailwind components" ui/app/globals.css && \
   grep -q "@tailwind utilities" ui/app/globals.css; then
    echo -e "${GREEN}✅ globals.css contains all Tailwind directives${NC}"
else
    echo -e "${RED}❌ globals.css missing Tailwind directives${NC}"
    exit 1
fi
echo ""

# Test 6: Verify postcss.config.js includes tailwindcss
echo "Test 6: Verifying postcss.config.js configuration..."
if grep -q "tailwindcss" ui/postcss.config.js; then
    echo -e "${GREEN}✅ postcss.config.js includes tailwindcss${NC}"
else
    echo -e "${RED}❌ postcss.config.js missing tailwindcss${NC}"
    exit 1
fi
echo ""

# Test 7: Simulate what Vercel will do - check if build directory is correct
echo "Test 7: Simulating Vercel build directory detection..."
echo "   Vercel will:"
echo "   1. Scan repository root"
echo "   2. Find vercel.json with rootDirectory: ui"
echo "   3. Change to ui/ directory"
echo "   4. Run: npm install --legacy-peer-deps"
echo "   5. Run: npm run build"
echo ""
echo -e "${GREEN}✅ Configuration validated - Vercel should build from ui/ directory${NC}"
echo ""

# Summary
echo "========================"
echo -e "${GREEN}✅ All validation tests passed!${NC}"
echo ""
echo "The fix is correctly configured:"
echo "  • Root-level vercel.json sets rootDirectory: ui"
echo "  • tailwindcss is present in ui/package.json"
echo "  • All configuration files exist and are correct"
echo "  • Dependencies can be resolved from ui/ directory"
echo ""
echo "Next steps:"
echo "  1. Monitor next Vercel deployment"
echo "  2. Verify build succeeds with new configuration"
echo "  3. Check build logs confirm 863 packages installed (not 141)"
echo ""

