# Docker Diagnostic Tools - Summary

## Problem

Docker issues on macOS that require computer restarts are often caused by:
1. **Docker daemon hanging** - Most common issue, `docker info` hangs indefinitely
2. **Resource exhaustion** - Disk space, memory, or file descriptors
3. **Build cache corruption** - Corrupted build cache causing hangs
4. **Network issues** - Docker network stack problems
5. **Container/volume corruption** - Stuck containers or corrupted volumes

## Solution

Three tools have been created to help diagnose and fix Docker issues **without restarting**:

### 1. Diagnostic Script (`scripts/diagnose_docker_issues.sh`)

Comprehensive diagnostic tool that checks:
- ✅ Docker daemon responsiveness
- ✅ Disk space and resources
- ✅ Container status
- ✅ Image and volume health
- ✅ Network connectivity
- ✅ Build cache status
- ✅ System limits

**Usage:**
```bash
./scripts/diagnose_docker_issues.sh
```

**What it does:**
- Runs 8 different health checks
- Attempts automatic fixes (cleanup, etc.)
- Provides specific recommendations
- Tries to restart Docker Desktop programmatically if daemon is hanging

### 2. Troubleshooting Guide (`docs/operations/DOCKER_TROUBLESHOOTING.md`)

Complete reference guide with:
- Common issues and quick fixes
- Step-by-step recovery procedures
- Prevention tips
- Quick reference table

**Usage:**
```bash
# Read the guide
cat docs/operations/DOCKER_TROUBLESHOOTING.md

# Or open in editor
code docs/operations/DOCKER_TROUBLESHOOTING.md
```

### 3. Enhanced Test Script (`scripts/test_dockerfile_fm042.sh`)

Updated test script with pre-check that:
- Verifies Docker is responsive before starting tests
- Provides helpful error messages if Docker is hung
- Suggests fixes automatically
- Saves time by failing fast

**Usage:**
```bash
./scripts/test_dockerfile_fm042.sh
```

The script will now detect Docker issues **before** attempting the build.

## Quick Start

### When Docker is Hanging

```bash
# Step 1: Run diagnostics
./scripts/diagnose_docker_issues.sh

# Step 2: If daemon is hanging, try restarting Docker Desktop
osascript -e 'quit app "Docker"'
sleep 5
open -a Docker
sleep 10

# Step 3: Verify it's working
docker info

# Step 4: If still not working, check logs
tail -50 ~/Library/Containers/com.docker.docker/Data/log/host/*.log
```

### Before Running Tests

```bash
# Quick check (built into test script now)
./scripts/test_dockerfile_fm042.sh

# Or manual check
docker info > /dev/null 2>&1 && echo "✅ OK" || ./scripts/diagnose_docker_issues.sh
```

### Regular Maintenance

Run weekly to prevent issues:

```bash
# Clean up unused resources
docker system prune -f

# Check health
./scripts/diagnose_docker_issues.sh
```

## Most Common Fixes

### Fix 1: Restart Docker Desktop (No Restart Required)
```bash
osascript -e 'quit app "Docker"'
sleep 5
open -a Docker
sleep 10
docker info  # Verify
```

### Fix 2: Clean Up Resources
```bash
# Safe cleanup (keeps running containers)
docker system prune -f

# Aggressive cleanup (removes everything unused)
docker system prune -a -f
```

### Fix 3: Clean Build Cache
```bash
docker builder prune -f
```

### Fix 4: Check and Free Disk Space
```bash
# Check space
df -h .

# Clean Docker
docker system prune -a -f
```

## When Restart is Actually Needed

Only restart your computer if:
1. ✅ All command-line fixes failed
2. ✅ Docker Desktop won't start at all
3. ✅ System is completely unresponsive
4. ✅ You've tried all troubleshooting steps

**Before restarting, try:**
1. Full Docker Desktop restart (quit and reopen)
2. Clean all Docker resources
3. Reset Docker Desktop: Troubleshoot → Reset to factory defaults

## Integration

The diagnostic tools are integrated into the test workflow:

1. **Test script** now checks Docker health before running
2. **Diagnostic script** can be run standalone or as part of CI/CD
3. **Troubleshooting guide** provides reference documentation

## Files Created

- `scripts/diagnose_docker_issues.sh` - Main diagnostic tool
- `docs/operations/DOCKER_TROUBLESHOOTING.md` - Complete troubleshooting guide
- `docs/operations/DOCKER_DIAGNOSTIC_SUMMARY.md` - This file

## Files Modified

- `scripts/test_dockerfile_fm042.sh` - Added Docker health pre-check

## Next Steps

1. **Run diagnostics now** to check current Docker health:
   ```bash
   ./scripts/diagnose_docker_issues.sh
   ```

2. **Read the troubleshooting guide** for detailed solutions:
   ```bash
   cat docs/operations/DOCKER_TROUBLESHOOTING.md
   ```

3. **Test the enhanced test script**:
   ```bash
   ./scripts/test_dockerfile_fm042.sh
   ```

## Benefits

- ✅ **No more unnecessary restarts** - Most issues can be fixed via command line
- ✅ **Faster diagnosis** - Know exactly what's wrong in seconds
- ✅ **Automatic fixes** - Many issues are fixed automatically
- ✅ **Better error messages** - Tests fail fast with helpful guidance
- ✅ **Prevention** - Regular maintenance prevents issues

