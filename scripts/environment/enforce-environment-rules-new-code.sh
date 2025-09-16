#!/bin/bash
# Environment Configuration Enforcement Script for New Code
# This script enforces the three-environment configuration system rules for new/modified files

set -e

echo "🔍 Checking environment configuration compliance for new/modified code..."

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

# Get list of modified files (staged for commit)
MODIFIED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$' || true)

if [ -z "$MODIFIED_FILES" ]; then
    echo "No Python files modified in this commit. Skipping environment configuration checks."
    exit 0
fi

echo "📋 Checking modified files for environment configuration compliance..."
echo "Modified files: $MODIFIED_FILES"

echo ""
echo "📋 Checking for direct environment variable access in modified files..."

# Check for direct os.getenv usage in modified files (excluding configuration_manager.py and test files)
ENV_VIOLATIONS=$(echo "$MODIFIED_FILES" | xargs grep -l "os\.getenv" 2>/dev/null | grep -v "config/configuration_manager.py" | grep -v "test_" | wc -l)

if [ "$ENV_VIOLATIONS" -gt 0 ]; then
    report_violation "Found modified files with direct os.getenv usage outside configuration_manager.py"
    echo "Files with violations:"
    echo "$MODIFIED_FILES" | xargs grep -l "os\.getenv" 2>/dev/null | grep -v "config/configuration_manager.py" | grep -v "test_" | head -5
    echo ""
    echo "Please replace direct os.getenv usage with configuration manager:"
    echo "  WRONG: os.getenv('DATABASE_URL')"
    echo "  CORRECT: config.get_database_url()"
else
    report_success "No direct os.getenv usage found in modified files"
fi

echo ""
echo "📋 Checking for hardcoded environment-specific values in modified files..."

# Check for hardcoded environment-specific values in modified files
HARDCODED_VIOLATIONS=$(echo "$MODIFIED_FILES" | xargs grep -l "NODE_ENV\|DEBUG.*true\|DEBUG.*false\|LOG_LEVEL.*DEBUG\|LOG_LEVEL.*WARNING\|LOG_LEVEL.*ERROR" 2>/dev/null | grep -v "config/configuration_manager.py" | grep -v "test_" | wc -l)

if [ "$HARDCODED_VIOLATIONS" -gt 0 ]; then
    report_violation "Found modified files with hardcoded environment-specific values"
    echo "Files with violations:"
    echo "$MODIFIED_FILES" | xargs grep -l "NODE_ENV\|DEBUG.*true\|DEBUG.*false\|LOG_LEVEL.*DEBUG\|LOG_LEVEL.*WARNING\|LOG_LEVEL.*ERROR" 2>/dev/null | grep -v "config/configuration_manager.py" | grep -v "test_" | head -5
    echo ""
    echo "Please replace hardcoded values with configuration manager:"
    echo "  WRONG: if os.getenv('NODE_ENV') == 'development':"
    echo "  CORRECT: if config.is_development():"
else
    report_success "No hardcoded environment-specific values found in modified files"
fi

echo ""
echo "📋 Checking for configuration manager usage in modified files..."

# Check for configuration manager imports in modified files
CONFIG_IMPORTS=$(echo "$MODIFIED_FILES" | xargs grep -l "from config.configuration_manager import\|import.*configuration_manager" 2>/dev/null | wc -l)

if [ "$CONFIG_IMPORTS" -gt 0 ]; then
    report_success "Found $CONFIG_IMPORTS modified files using configuration manager"
else
    report_warning "No configuration manager usage found in modified files"
fi

echo ""
echo "📋 Checking for environment-specific testing in modified files..."

# Check if any modified files are test files
TEST_FILES=$(echo "$MODIFIED_FILES" | grep -E "test_.*\.py$" | wc -l)

if [ "$TEST_FILES" -gt 0 ]; then
    echo "Found $TEST_FILES modified test files"
    
    # Check for environment-specific test patterns
    ENV_TEST_PATTERNS=$(echo "$MODIFIED_FILES" | xargs grep -l "config\.is_development\|config\.is_testing\|config\.is_production\|initialize_config" 2>/dev/null | wc -l)
    
    if [ "$ENV_TEST_PATTERNS" -gt 0 ]; then
        report_success "Found environment-specific test patterns in modified test files"
    else
        report_warning "No environment-specific test patterns found in modified test files"
    fi
else
    report_warning "No test files modified - consider adding tests for new features"
fi

echo ""
echo "📋 Checking for staging environment references in modified files..."

# Check for staging environment references in modified files (should not exist)
STAGING_REFERENCES=$(echo "$MODIFIED_FILES" | xargs grep -l "staging\|STAGING" 2>/dev/null | wc -l)

if [ "$STAGING_REFERENCES" -gt 0 ]; then
    report_violation "Found modified files with staging environment references (should be removed)"
    echo "Files with staging references:"
    echo "$MODIFIED_FILES" | xargs grep -l "staging\|STAGING" 2>/dev/null | head -5
    echo ""
    echo "Please remove staging environment references and use testing environment instead"
else
    report_success "No staging environment references found in modified files"
fi

echo ""
echo "📋 Checking for environment-specific documentation in modified files..."

# Check for environment-specific documentation in modified files
ENV_DOCS=$(echo "$MODIFIED_FILES" | xargs grep -l "Environment Behavior\|environment-specific\|Development:\|Testing:\|Production:" 2>/dev/null | wc -l)

if [ "$ENV_DOCS" -gt 0 ]; then
    report_success "Found environment-specific documentation in modified files"
else
    report_warning "No environment-specific documentation found in modified files"
fi

echo ""
echo "📋 Summary..."

if [ "$VIOLATIONS" -eq 0 ]; then
    echo -e "${GREEN}🎉 All environment configuration rules are being followed in modified files!${NC}"
    echo -e "${GREEN}✅ No violations found in modified files${NC}"
    exit 0
else
    echo -e "${RED}❌ Found $VIOLATIONS violations of environment configuration rules in modified files${NC}"
    echo -e "${RED}❌ Please fix these violations before committing${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Replace direct os.getenv() usage with config.get_config()"
    echo "2. Replace hardcoded values with configuration manager access"
    echo "3. Add environment-specific tests for new features"
    echo "4. Remove any staging environment references"
    echo "5. Add environment-specific documentation"
    echo ""
    echo "Example fixes:"
    echo "  WRONG: os.getenv('DATABASE_URL')"
    echo "  CORRECT: config.get_database_url()"
    echo ""
    echo "  WRONG: if os.getenv('NODE_ENV') == 'development':"
    echo "  CORRECT: if config.is_development():"
    echo ""
    echo "  WRONG: similarity_threshold = 0.3"
    echo "  CORRECT: similarity_threshold = config.get_rag_similarity_threshold()"
    exit 1
fi
