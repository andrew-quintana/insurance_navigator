#!/bin/bash
# Environment Configuration Enforcement Script
# This script enforces the three-environment configuration system rules

set -e

echo "🔍 Checking environment configuration compliance..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track violations
VIOLATIONS=0

# Function to report violations
report_violation() {
    echo -e "${RED}❌ VIOLATION: $1${NC}"
    ((VIOLATIONS++))
}

# Function to report success
report_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to report warning
report_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "📋 Checking for direct environment variable access..."

# Check for direct os.getenv usage outside configuration_manager.py
ENV_VIOLATIONS=$(grep -r "os\.getenv" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude="*.example" --exclude="config/configuration_manager.py" --exclude="test_*.py" . | wc -l)

if [ "$ENV_VIOLATIONS" -gt 0 ]; then
    report_violation "Found $ENV_VIOLATIONS instances of direct os.getenv usage outside configuration_manager.py"
    echo "Files with violations:"
    grep -r "os\.getenv" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude="*.example" --exclude="config/configuration_manager.py" --exclude="test_*.py" . | head -10
else
    report_success "No direct os.getenv usage found outside configuration_manager.py"
fi

echo ""
echo "📋 Checking for hardcoded environment-specific values..."

# Check for hardcoded environment-specific values
HARDCODED_VIOLATIONS=$(grep -r "NODE_ENV\|DEBUG.*true\|DEBUG.*false\|LOG_LEVEL.*DEBUG\|LOG_LEVEL.*WARNING\|LOG_LEVEL.*ERROR" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude="*.example" --exclude="config/configuration_manager.py" --exclude="test_*.py" . | wc -l)

if [ "$HARDCODED_VIOLATIONS" -gt 0 ]; then
    report_violation "Found $HARDCODED_VIOLATIONS instances of hardcoded environment-specific values"
    echo "Files with violations:"
    grep -r "NODE_ENV\|DEBUG.*true\|DEBUG.*false\|LOG_LEVEL.*DEBUG\|LOG_LEVEL.*WARNING\|LOG_LEVEL.*ERROR" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude="*.example" --exclude="config/configuration_manager.py" --exclude="test_*.py" . | head -10
else
    report_success "No hardcoded environment-specific values found"
fi

echo ""
echo "📋 Checking for configuration manager usage..."

# Check for configuration manager imports
CONFIG_IMPORTS=$(grep -r "from config.configuration_manager import\|import.*configuration_manager" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ . | wc -l)

if [ "$CONFIG_IMPORTS" -gt 0 ]; then
    report_success "Found $CONFIG_IMPORTS instances of configuration manager usage"
else
    report_warning "No configuration manager usage found - this might be expected for some files"
fi

echo ""
echo "📋 Checking for environment-specific testing..."

# Check for environment-specific test files
DEV_TESTS=$(find . -name "test_development_*.py" -o -name "test_dev_*.py" | wc -l)
TESTING_TESTS=$(find . -name "test_testing_*.py" -o -name "test_bridge_*.py" | wc -l)
PROD_TESTS=$(find . -name "test_production_*.py" -o -name "test_prod_*.py" | wc -l)
INTEGRATION_TESTS=$(find . -name "test_all_environments_*.py" -o -name "test_cross_environment_*.py" | wc -l)

echo "Test file counts:"
echo "  Development tests: $DEV_TESTS"
echo "  Testing tests: $TESTING_TESTS"
echo "  Production tests: $PROD_TESTS"
echo "  Integration tests: $INTEGRATION_TESTS"

if [ "$DEV_TESTS" -eq 0 ] || [ "$TESTING_TESTS" -eq 0 ] || [ "$PROD_TESTS" -eq 0 ]; then
    report_warning "Missing environment-specific test files"
    echo "  Consider adding tests for all environments"
fi

echo ""
echo "📋 Checking for environment validation in tests..."

# Check for environment validation in test files
ENV_VALIDATION=$(grep -r "config\.is_development\|config\.is_testing\|config\.is_production" --include="test_*.py" . | wc -l)

if [ "$ENV_VALIDATION" -gt 0 ]; then
    report_success "Found $ENV_VALIDATION instances of environment validation in tests"
else
    report_warning "No environment validation found in tests"
fi

echo ""
echo "📋 Checking for configuration manager usage in tests..."

# Check for configuration manager usage in test files
TEST_CONFIG_USAGE=$(grep -r "initialize_config\|ConfigurationManager" --include="test_*.py" . | wc -l)

if [ "$TEST_CONFIG_USAGE" -gt 0 ]; then
    report_success "Found $TEST_CONFIG_USAGE instances of configuration manager usage in tests"
else
    report_warning "No configuration manager usage found in tests"
fi

echo ""
echo "📋 Checking for environment-specific documentation..."

# Check for environment-specific documentation
ENV_DOCS=$(grep -r "Environment Behavior\|environment-specific\|Development:\|Testing:\|Production:" --include="*.py" . | wc -l)

if [ "$ENV_DOCS" -gt 0 ]; then
    report_success "Found $ENV_DOCS instances of environment-specific documentation"
else
    report_warning "No environment-specific documentation found"
fi

echo ""
echo "📋 Checking for staging environment references..."

# Check for staging environment references (should not exist)
STAGING_REFERENCES=$(grep -r "staging\|STAGING" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude="*.example" --exclude="*.md" . | wc -l)

if [ "$STAGING_REFERENCES" -gt 0 ]; then
    report_violation "Found $STAGING_REFERENCES references to staging environment (should be removed)"
    echo "Files with staging references:"
    grep -r "staging\|STAGING" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude="*.example" --exclude="*.md" . | head -5
else
    report_success "No staging environment references found"
fi

echo ""
echo "📋 Summary..."

if [ "$VIOLATIONS" -eq 0 ]; then
    echo -e "${GREEN}🎉 All environment configuration rules are being followed!${NC}"
    echo -e "${GREEN}✅ No violations found${NC}"
    exit 0
else
    echo -e "${RED}❌ Found $VIOLATIONS violations of environment configuration rules${NC}"
    echo -e "${RED}❌ Please fix these violations before committing${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Replace direct os.getenv() usage with config.get_config()"
    echo "2. Replace hardcoded values with configuration manager access"
    echo "3. Add environment-specific tests for all environments"
    echo "4. Remove any staging environment references"
    echo "5. Add environment-specific documentation"
    exit 1
fi
