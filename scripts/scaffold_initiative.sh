#!/bin/bash

# scaffold_initiative.sh - Generate initiative documentation from templates
# Usage: ./scaffold_initiative.sh <serial> <initiative_name>
# Example: ./scaffold_initiative.sh 001 "User Authentication System"

set -e

if [ $# -ne 2 ]; then
    echo "Usage: $0 <serial> <initiative_name>"
    echo "Example: $0 001 \"User Authentication System\""
    exit 1
fi

SERIAL="$1"
INITIATIVE_NAME="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_DIR="$REPO_ROOT/docs"
TEMPLATES_DIR="$DOCS_DIR/meta/templates"
INITIATIVES_DIR="$DOCS_DIR/initiatives"

# Validate inputs
if [[ ! "$SERIAL" =~ ^[0-9]{3}$ ]]; then
    echo "Error: Serial must be a 3-digit number (e.g., 001, 042, 123)"
    exit 1
fi

if [ -z "$INITIATIVE_NAME" ]; then
    echo "Error: Initiative name cannot be empty"
    exit 1
fi

# Check if templates exist
if [ ! -d "$TEMPLATES_DIR" ]; then
    echo "Error: Templates directory not found at $TEMPLATES_DIR"
    echo "Please run the documentation contract system setup first."
    exit 1
fi

# Create initiatives directory if it doesn't exist
mkdir -p "$INITIATIVES_DIR"

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# File names
CONTEXT_FILE="$INITIATIVES_DIR/CONTEXT${SERIAL}.md"
PRD_FILE="$INITIATIVES_DIR/PRD${SERIAL}.md"
RFC_FILE="$INITIATIVES_DIR/RFC${SERIAL}.md"
TODO_FILE="$INITIATIVES_DIR/TODO${SERIAL}.md"

# Check if any files already exist
if [ -f "$CONTEXT_FILE" ] || [ -f "$PRD_FILE" ] || [ -f "$RFC_FILE" ] || [ -f "$TODO_FILE" ]; then
    echo "Error: Initiative ${SERIAL} files already exist:"
    [ -f "$CONTEXT_FILE" ] && echo "  - $CONTEXT_FILE"
    [ -f "$PRD_FILE" ] && echo "  - $PRD_FILE"
    [ -f "$RFC_FILE" ] && echo "  - $RFC_FILE"
    [ -f "$TODO_FILE" ] && echo "  - $TODO_FILE"
    echo "Use a different serial number or remove existing files."
    exit 1
fi

echo "Scaffolding initiative ${SERIAL}: ${INITIATIVE_NAME}"

# Generate CONTEXT file
sed -e "s/XXX/${SERIAL}/g" \
    -e "s/{InitiativeName}/${INITIATIVE_NAME}/g" \
    "$TEMPLATES_DIR/CONTEXT.md" > "$CONTEXT_FILE"

# Generate PRD file
sed -e "s/XXX/${SERIAL}/g" \
    -e "s/{InitiativeName}/${INITIATIVE_NAME}/g" \
    -e "s/2025-08-21/${CURRENT_DATE}/g" \
    "$TEMPLATES_DIR/PRD.md" > "$PRD_FILE"

# Generate RFC file
sed -e "s/XXX/${SERIAL}/g" \
    -e "s/{InitiativeName}/${INITIATIVE_NAME}/g" \
    "$TEMPLATES_DIR/RFC.md" > "$RFC_FILE"

# Generate TODO file
sed -e "s/XXX/${SERIAL}/g" \
    -e "s/{InitiativeName}/${INITIATIVE_NAME}/g" \
    "$TEMPLATES_DIR/TODO.md" > "$TODO_FILE"

echo "Created files:"
echo "  ✓ $CONTEXT_FILE"
echo "  ✓ $PRD_FILE"
echo "  ✓ $RFC_FILE"
echo "  ✓ $TODO_FILE"

echo ""
echo "Next steps:"
echo "1. Edit $CONTEXT_FILE to define scope and adjacent components"
echo "2. Update docs/knowledge/ADJACENT_INDEX.md with component entries"
echo "3. Run tools/validate_docs.py to check readiness"
echo "4. Complete PRD and RFC before starting implementation"

echo ""
echo "Remember: Review docs/DOCS_READINESS_CHECKLIST.md before coding!"