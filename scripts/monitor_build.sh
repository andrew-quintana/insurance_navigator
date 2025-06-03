#!/bin/bash
# Monitor Docker Build Progress
# Shows real-time build progress with timestamps

echo "🔍 Docker Build Monitor"
echo "======================="
echo "⏱️  Expected time: 8-20 minutes (first build)"
echo "🔄 Heavy ML dependencies downloading..."
echo "📊 Monitoring build progress..."
echo

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

START_TIME=$(date +%s)

# Function to show elapsed time
show_elapsed() {
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    MINUTES=$((ELAPSED / 60))
    SECONDS=$((ELAPSED % 60))
    echo -e "${BLUE}⏱️  Elapsed: ${MINUTES}m ${SECONDS}s${NC}"
}

# Check if build is still running
while ps aux | grep -q "docker.*build.*insurance-navigator" | grep -v grep; do
    show_elapsed
    echo -e "${YELLOW}🔄 Docker build still running...${NC}"
    echo "   ├─ Installing ML packages (torch, transformers)"
    echo "   ├─ This is the longest step (~5-15 minutes)"
    echo "   └─ Grab a coffee! ☕"
    echo
    sleep 30
done

show_elapsed
echo -e "${GREEN}✅ Build process completed!${NC}"

# Check if image was created successfully
if docker images | grep -q "insurance-navigator"; then
    echo -e "${GREEN}🎉 Docker image created successfully!${NC}"
    docker images | grep insurance-navigator
else
    echo -e "${YELLOW}⚠️  Build may have failed - checking logs...${NC}"
fi 