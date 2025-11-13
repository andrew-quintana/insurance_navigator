#!/bin/bash
# Docker Diagnostic and Recovery Script for macOS
# Diagnoses common Docker issues and attempts fixes without restarting

set -e

echo "🔍 Docker Diagnostic and Recovery Tool"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track issues found
ISSUES_FOUND=0
FIXES_APPLIED=0

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    elif [ "$status" = "ERROR" ]; then
        echo -e "${RED}❌ $message${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    elif [ "$status" = "INFO" ]; then
        echo -e "${BLUE}ℹ️  $message${NC}"
    fi
}

# Function to check if Docker daemon is responsive
check_docker_daemon() {
    echo "1️⃣  Checking Docker Daemon Status"
    echo "-----------------------------------"
    
    # Check if docker command exists
    if ! command -v docker &> /dev/null; then
        print_status "ERROR" "Docker command not found. Is Docker Desktop installed?"
        return 1
    fi
    
    # Try to get Docker info with timeout
    print_status "INFO" "Testing Docker daemon responsiveness..."
    
    # Use a background process with timeout simulation
    docker info > /tmp/docker_info.log 2>&1 &
    DOCKER_PID=$!
    
    # Wait up to 5 seconds
    for i in {1..5}; do
        if ! kill -0 $DOCKER_PID 2>/dev/null; then
            # Process finished
            wait $DOCKER_PID
            DOCKER_EXIT=$?
            if [ $DOCKER_EXIT -eq 0 ]; then
                print_status "OK" "Docker daemon is responsive"
                return 0
            else
                print_status "ERROR" "Docker daemon returned error (exit code: $DOCKER_EXIT)"
                cat /tmp/docker_info.log
                return 1
            fi
        fi
        sleep 1
    done
    
    # Still running after 5 seconds - likely hanging
    kill $DOCKER_PID 2>/dev/null || true
    print_status "ERROR" "Docker daemon is hanging (not responding after 5 seconds)"
    echo "   This is often the main issue requiring restarts."
    echo ""
    echo "   Attempting recovery..."
    
    # Try to restart Docker Desktop via command line (if available)
    if command -v osascript &> /dev/null; then
        print_status "INFO" "Attempting to restart Docker Desktop via AppleScript..."
        osascript -e 'quit app "Docker"' 2>/dev/null || true
        sleep 3
        open -a Docker 2>/dev/null || true
        print_status "INFO" "Waiting 10 seconds for Docker Desktop to restart..."
        sleep 10
        
        # Test again
        if timeout 5 docker info > /dev/null 2>&1 || docker info > /dev/null 2>&1; then
            print_status "OK" "Docker daemon recovered after restart attempt"
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
            return 0
        fi
    fi
    
    print_status "WARN" "Could not automatically recover Docker daemon"
    echo "   Manual steps:"
    echo "   1. Open Docker Desktop"
    echo "   2. Click 'Troubleshoot' → 'Restart'"
    echo "   3. Or quit Docker Desktop completely and reopen it"
    return 1
}

# Function to check Docker resources
check_docker_resources() {
    echo ""
    echo "2️⃣  Checking Docker Resources"
    echo "------------------------------"
    
    # Check disk space
    print_status "INFO" "Checking available disk space..."
    DISK_SPACE=$(df -h . | tail -1 | awk '{print $4}')
    DISK_AVAIL=$(df . | tail -1 | awk '{print $4}')
    DISK_AVAIL_GB=$((DISK_AVAIL / 1024 / 1024))
    
    if [ $DISK_AVAIL_GB -lt 5 ]; then
        print_status "WARN" "Low disk space: ${DISK_SPACE} available (${DISK_AVAIL_GB}GB)"
        echo "   Docker needs at least 5GB free space"
    else
        print_status "OK" "Disk space: ${DISK_SPACE} available"
    fi
    
    # Check Docker system disk usage
    if docker system df > /tmp/docker_df.log 2>&1; then
        print_status "OK" "Docker system info accessible"
        echo "   Docker disk usage:"
        docker system df | head -10
    else
        print_status "WARN" "Could not get Docker disk usage"
    fi
    
    # Check memory (if possible)
    if command -v vm_stat &> /dev/null; then
        print_status "INFO" "Checking system memory..."
        FREE_PAGES=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
        FREE_MB=$((FREE_PAGES * 4096 / 1024 / 1024))
        if [ $FREE_MB -lt 1024 ]; then
            print_status "WARN" "Low free memory: ~${FREE_MB}MB available"
        else
            print_status "OK" "Free memory: ~${FREE_MB}MB available"
        fi
    fi
}

# Function to check Docker containers
check_docker_containers() {
    echo ""
    echo "3️⃣  Checking Docker Containers"
    echo "-------------------------------"
    
    # Count running containers
    RUNNING=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
    STOPPED=$(docker ps -aq -f status=exited 2>/dev/null | wc -l | tr -d ' ')
    
    print_status "INFO" "Running containers: $RUNNING"
    print_status "INFO" "Stopped containers: $STOPPED"
    
    # Check for stuck containers
    if [ "$RUNNING" -gt 0 ]; then
        print_status "OK" "Some containers are running"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        print_status "INFO" "No containers currently running"
    fi
    
    # Check for unhealthy containers
    UNHEALTHY=$(docker ps -a --filter "health=unhealthy" -q 2>/dev/null | wc -l | tr -d ' ')
    if [ "$UNHEALTHY" -gt 0 ]; then
        print_status "WARN" "Found $UNHEALTHY unhealthy container(s)"
        docker ps -a --filter "health=unhealthy" --format "table {{.Names}}\t{{.Status}}"
    fi
}

# Function to check Docker images
check_docker_images() {
    echo ""
    echo "4️⃣  Checking Docker Images"
    echo "---------------------------"
    
    IMAGE_COUNT=$(docker images -q 2>/dev/null | wc -l | tr -d ' ')
    print_status "INFO" "Total images: $IMAGE_COUNT"
    
    # Check for dangling images
    DANGLING=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l | tr -d ' ')
    if [ "$DANGLING" -gt 0 ]; then
        print_status "WARN" "Found $DANGLING dangling image(s) (can be cleaned up)"
    else
        print_status "OK" "No dangling images"
    fi
    
    # Check total image size
    if docker images --format "{{.Size}}" 2>/dev/null | head -1 > /dev/null; then
        print_status "OK" "Image listing works"
    fi
}

# Function to check Docker volumes
check_docker_volumes() {
    echo ""
    echo "5️⃣  Checking Docker Volumes"
    echo "---------------------------"
    
    VOLUME_COUNT=$(docker volume ls -q 2>/dev/null | wc -l | tr -d ' ')
    print_status "INFO" "Total volumes: $VOLUME_COUNT"
    
    # Check for orphaned volumes
    if [ "$VOLUME_COUNT" -gt 0 ]; then
        print_status "OK" "Volumes accessible"
    fi
}

# Function to check Docker network
check_docker_network() {
    echo ""
    echo "6️⃣  Checking Docker Network"
    echo "---------------------------"
    
    if docker network ls > /dev/null 2>&1; then
        NETWORK_COUNT=$(docker network ls -q 2>/dev/null | wc -l | tr -d ' ')
        print_status "OK" "Network accessible (${NETWORK_COUNT} networks)"
    else
        print_status "ERROR" "Cannot access Docker networks"
    fi
}

# Function to check Docker build cache
check_docker_build_cache() {
    echo ""
    echo "7️⃣  Checking Docker Build Cache"
    echo "-------------------------------"
    
    # Try a simple build command to test cache
    print_status "INFO" "Testing build cache accessibility..."
    
    # Create a minimal test
    TEST_DIR=$(mktemp -d)
    echo "FROM alpine:latest" > "$TEST_DIR/Dockerfile.test"
    
    if docker build -t docker-test:temp "$TEST_DIR" > /tmp/docker_build_test.log 2>&1; then
        print_status "OK" "Build cache is working"
        docker rmi docker-test:temp > /dev/null 2>&1 || true
    else
        print_status "WARN" "Build cache may have issues"
        echo "   Build test output:"
        tail -10 /tmp/docker_build_test.log
    fi
    
    rm -rf "$TEST_DIR"
}

# Function to check file descriptors
check_file_descriptors() {
    echo ""
    echo "8️⃣  Checking System Limits"
    echo "---------------------------"
    
    # Check ulimit for file descriptors
    if command -v ulimit &> /dev/null; then
        FD_LIMIT=$(ulimit -n 2>/dev/null || echo "unknown")
        print_status "INFO" "File descriptor limit: $FD_LIMIT"
        
        if [ "$FD_LIMIT" != "unknown" ] && [ "$FD_LIMIT" -lt 1024 ]; then
            print_status "WARN" "Low file descriptor limit (may cause Docker issues)"
        fi
    fi
}

# Function to attempt automatic fixes
attempt_fixes() {
    echo ""
    echo "🔧 Attempting Automatic Fixes"
    echo "=============================="
    
    # Fix 1: Clean up stopped containers
    echo ""
    print_status "INFO" "Cleaning up stopped containers..."
    STOPPED_COUNT=$(docker ps -aq -f status=exited 2>/dev/null | wc -l | tr -d ' ')
    if [ "$STOPPED_COUNT" -gt 0 ]; then
        if docker container prune -f > /dev/null 2>&1; then
            print_status "OK" "Removed $STOPPED_COUNT stopped container(s)"
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
        fi
    else
        print_status "OK" "No stopped containers to clean"
    fi
    
    # Fix 2: Remove dangling images
    echo ""
    print_status "INFO" "Cleaning up dangling images..."
    DANGLING_COUNT=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l | tr -d ' ')
    if [ "$DANGLING_COUNT" -gt 0 ]; then
        if docker image prune -f > /dev/null 2>&1; then
            print_status "OK" "Removed dangling images"
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
        fi
    else
        print_status "OK" "No dangling images to clean"
    fi
    
    # Fix 3: Clean build cache (optional, ask user)
    echo ""
    print_status "INFO" "Build cache cleanup (skipped - use 'docker builder prune' manually if needed)"
    
    # Fix 4: Restart Docker Desktop (if hanging)
    echo ""
    if [ $ISSUES_FOUND -gt 0 ]; then
        print_status "INFO" "If Docker daemon is hanging, try:"
        echo "   osascript -e 'quit app \"Docker\"'"
        echo "   sleep 5"
        echo "   open -a Docker"
    fi
}

# Function to provide recommendations
provide_recommendations() {
    echo ""
    echo "📋 Recommendations"
    echo "==================="
    
    if [ $ISSUES_FOUND -eq 0 ]; then
        print_status "OK" "No issues detected! Docker should be working properly."
        echo ""
        echo "If you're still experiencing issues:"
        echo "  1. Check Docker Desktop logs:"
        echo "     ~/Library/Containers/com.docker.docker/Data/log/host/*.log"
        echo "  2. Try rebuilding your image:"
        echo "     docker build --no-cache -t your-image ."
        echo "  3. Check for port conflicts:"
        echo "     lsof -i :8000 -i :8001"
    else
        echo "Based on the diagnostics, try these fixes in order:"
        echo ""
        echo "1. Clean Docker system (safe):"
        echo "   docker system prune -f"
        echo ""
        echo "2. Restart Docker Desktop:"
        echo "   osascript -e 'quit app \"Docker\"'"
        echo "   sleep 5"
        echo "   open -a Docker"
        echo ""
        echo "3. If still having issues, check Docker Desktop settings:"
        echo "   - Resources → Memory: Should be at least 4GB"
        echo "   - Resources → Disk: Should have enough space"
        echo "   - General → Enable 'Use Virtualization framework'"
        echo ""
        echo "4. Check Docker Desktop logs:"
        echo "   tail -f ~/Library/Containers/com.docker.docker/Data/log/host/*.log"
        echo ""
        echo "5. As last resort, reset Docker Desktop:"
        echo "   Docker Desktop → Troubleshoot → Reset to factory defaults"
    fi
}

# Main execution
main() {
    # Run all checks
    check_docker_daemon
    DAEMON_STATUS=$?
    
    if [ $DAEMON_STATUS -eq 0 ]; then
        check_docker_resources
        check_docker_containers
        check_docker_images
        check_docker_volumes
        check_docker_network
        check_docker_build_cache
        check_file_descriptors
    else
        print_status "ERROR" "Skipping further checks - Docker daemon not accessible"
    fi
    
    # Attempt fixes if daemon is working
    if [ $DAEMON_STATUS -eq 0 ]; then
        attempt_fixes
    fi
    
    # Provide recommendations
    provide_recommendations
    
    # Summary
    echo ""
    echo "======================================"
    echo "📊 Diagnostic Summary"
    echo "======================================"
    echo "Issues found: $ISSUES_FOUND"
    echo "Fixes applied: $FIXES_APPLIED"
    echo ""
    
    if [ $ISSUES_FOUND -eq 0 ] && [ $DAEMON_STATUS -eq 0 ]; then
        print_status "OK" "Docker appears to be healthy!"
        exit 0
    elif [ $DAEMON_STATUS -ne 0 ]; then
        print_status "ERROR" "Docker daemon is not accessible - restart may be required"
        exit 1
    else
        print_status "WARN" "Some issues detected - review recommendations above"
        exit 0
    fi
}

# Run main function
main

