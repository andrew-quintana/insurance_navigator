# Docker Troubleshooting Guide for macOS

## Quick Diagnostic

Run the diagnostic script to identify issues:

```bash
./scripts/diagnose_docker_issues.sh
```

## Common Issues and Solutions

### 1. Docker Daemon Not Responding (Hanging)

**Symptoms:**
- `docker info` hangs indefinitely
- `docker ps` doesn't return
- Builds hang at "Connecting to Docker daemon"

**Quick Fixes (in order):**

#### Fix 1: Restart Docker Desktop via Command Line
```bash
# Quit Docker Desktop
osascript -e 'quit app "Docker"'

# Wait a few seconds
sleep 5

# Restart Docker Desktop
open -a Docker

# Wait for it to start (10-15 seconds)
sleep 10

# Verify it's working
docker info
```

#### Fix 2: Restart Docker Desktop Manually
1. Click Docker icon in menu bar
2. Select "Troubleshoot" → "Restart"
3. Wait for Docker to restart

#### Fix 3: Force Quit and Restart
```bash
# Force quit Docker
killall Docker 2>/dev/null || true
killall "Docker Desktop" 2>/dev/null || true

# Wait
sleep 5

# Restart
open -a Docker
```

#### Fix 4: Check Docker Desktop Logs
```bash
# View recent logs
tail -50 ~/Library/Containers/com.docker.docker/Data/log/host/*.log

# Or open log directory
open ~/Library/Containers/com.docker.docker/Data/log/host/
```

### 2. Docker Build Hangs or Fails

**Symptoms:**
- Build hangs at specific step
- "Cannot connect to Docker daemon" errors
- Build fails with timeout

**Quick Fixes:**

#### Fix 1: Clean Build Cache
```bash
# Clean build cache (keeps images)
docker builder prune -f

# Or clean everything (more aggressive)
docker system prune -f
```

#### Fix 2: Rebuild Without Cache
```bash
docker build --no-cache -t your-image-name .
```

#### Fix 3: Check Disk Space
```bash
# Check available space
df -h .

# Clean up if needed
docker system prune -a -f  # Removes unused images too
```

### 3. Container Won't Start

**Symptoms:**
- Container exits immediately
- "Cannot start container" errors
- Port already in use

**Quick Fixes:**

#### Fix 1: Check Port Conflicts
```bash
# Check if port is in use
lsof -i :8000
lsof -i :8001

# Kill process using port (if safe)
kill -9 $(lsof -t -i :8000)
```

#### Fix 2: Check Container Logs
```bash
# View logs of stopped container
docker logs container-name

# View last 50 lines
docker logs --tail 50 container-name
```

#### Fix 3: Remove Stuck Containers
```bash
# List all containers
docker ps -a

# Remove specific container
docker rm -f container-name

# Remove all stopped containers
docker container prune -f
```

### 4. Out of Disk Space

**Symptoms:**
- "No space left on device" errors
- Docker operations fail
- System running slow

**Quick Fixes:**

#### Fix 1: Check Docker Disk Usage
```bash
# See what's using space
docker system df

# Clean up
docker system prune -a -f
```

#### Fix 2: Clean Specific Resources
```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Remove build cache
docker builder prune -a -f
```

#### Fix 3: Check System Disk Space
```bash
# Check available space
df -h

# Find large files
du -sh ~/Library/Containers/com.docker.docker/Data/*
```

### 5. Memory Issues

**Symptoms:**
- Docker Desktop crashes
- Containers killed unexpectedly
- System becomes unresponsive

**Quick Fixes:**

#### Fix 1: Adjust Docker Desktop Memory
1. Open Docker Desktop
2. Go to Settings → Resources
3. Increase Memory allocation (recommended: 4GB+)
4. Click "Apply & Restart"

#### Fix 2: Check System Memory
```bash
# Check available memory
vm_stat

# Check Docker memory usage
docker stats --no-stream
```

### 6. Network Issues

**Symptoms:**
- Containers can't reach each other
- Can't access containerized services
- DNS resolution fails

**Quick Fixes:**

#### Fix 1: Restart Docker Network
```bash
# List networks
docker network ls

# Remove and recreate default network
docker network prune -f
```

#### Fix 2: Check Network Configuration
```bash
# Inspect network
docker network inspect bridge

# Test connectivity
docker run --rm alpine ping -c 3 8.8.8.8
```

### 7. Permission Issues

**Symptoms:**
- "Permission denied" errors
- Can't access Docker socket
- Build fails with permission errors

**Quick Fixes:**

#### Fix 1: Check Docker Socket Permissions
```bash
# Check socket permissions
ls -la /var/run/docker.sock

# If missing, restart Docker Desktop
```

#### Fix 2: Check User Groups
```bash
# Verify user is in docker group (Linux)
groups | grep docker

# On macOS, Docker Desktop handles this automatically
```

## Prevention Tips

### Regular Maintenance

Run these weekly to prevent issues:

```bash
# Clean up unused resources
docker system prune -f

# Check for updates
docker --version
# Update Docker Desktop from menu bar
```

### Before Running Tests

Always check Docker health before running build tests:

```bash
# Quick health check
docker info > /dev/null 2>&1 && echo "✅ Docker OK" || echo "❌ Docker not responding"

# Or run full diagnostic
./scripts/diagnose_docker_issues.sh
```

### Monitor Resources

```bash
# Watch Docker resource usage
docker stats

# Check disk usage regularly
docker system df
```

## When to Restart Your Computer

Only restart if:
1. ✅ All command-line fixes failed
2. ✅ Docker Desktop won't start at all
3. ✅ System is completely unresponsive
4. ✅ You've tried all troubleshooting steps

**Before restarting, try:**
1. Full Docker Desktop restart (quit and reopen)
2. Clean all Docker resources: `docker system prune -a -f`
3. Reset Docker Desktop: Troubleshoot → Reset to factory defaults

## Getting Help

### Check Logs
```bash
# Docker Desktop logs
tail -f ~/Library/Containers/com.docker.docker/Data/log/host/*.log

# Container logs
docker logs container-name

# Build logs
cat /tmp/docker_build.log
```

### Useful Commands
```bash
# Full system status
docker system df
docker ps -a
docker images
docker volume ls
docker network ls

# Resource usage
docker stats --no-stream

# Version info
docker --version
docker-compose --version
```

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Daemon hanging | `osascript -e 'quit app "Docker"' && sleep 5 && open -a Docker` |
| Out of space | `docker system prune -a -f` |
| Port conflict | `lsof -i :PORT` then `kill -9 PID` |
| Build hangs | `docker builder prune -f` then rebuild |
| Container won't start | `docker logs container-name` |
| Memory issues | Increase Docker Desktop memory in Settings |

## Integration with Test Scripts

The test script `test_dockerfile_fm042.sh` now includes a pre-check. To manually run diagnostics before testing:

```bash
# Run diagnostics
./scripts/diagnose_docker_issues.sh

# If OK, run tests
./scripts/test_dockerfile_fm042.sh
```

Or add to your test workflow:

```bash
# Quick pre-test check
docker info > /dev/null 2>&1 || (echo "Docker not responding - run diagnostics" && ./scripts/diagnose_docker_issues.sh && exit 1)
```

