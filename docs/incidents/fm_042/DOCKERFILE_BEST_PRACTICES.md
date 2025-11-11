# Dockerfile Best Practices

**Date**: 2025-01-10  
**Context**: Lessons learned from FM-041 and FM-042 investigations

## Overview

This document outlines Dockerfile best practices based on lessons learned from production deployment issues and optimization conflicts. These practices help avoid common pitfalls and ensure reliable, performant Docker builds.

## Cache Management

### ✅ DO: Use Cache Mounts

**Recommended**:
```dockerfile
RUN --mount=type=cache,target=/home/app/.cache/pip,sharing=locked \
    pip install --user -r /tmp/requirements.txt
```

**Benefits**:
- Persistent cache across builds
- Faster subsequent builds
- Reduced network usage

### ❌ DON'T: Mix Cache Mechanisms

**Avoid**:
```dockerfile
ENV PIP_NO_CACHE_DIR=1  # ❌ Conflicts with cache mount
RUN --mount=type=cache,target=/home/app/.cache/pip,sharing=locked \
    pip install --no-cache-dir ...  # ❌ Also conflicts
```

**Problem**: Multiple mechanisms trying to control caching creates conflicts and wastes resources.

**Rule**: Choose ONE caching strategy:
- **Option A**: Cache mount (recommended for BuildKit)
- **Option B**: `PIP_NO_CACHE_DIR=1` (if you don't want caching)

**Don't use both!**

## Dependency Version Management

### ✅ DO: Use Constraints Files for Critical Dependencies

**Recommended**:
```dockerfile
COPY constraints.txt /tmp/constraints.txt
RUN pip install -r /tmp/requirements.txt -c /tmp/constraints.txt
```

**Benefits**:
- Ensures exact versions for critical dependencies
- Prevents version conflicts
- Reproducible builds

### ❌ DON'T: Use --force-reinstall with Constraints Files

**Avoid**:
```dockerfile
RUN pip install --force-reinstall -r /tmp/requirements.txt -c /tmp/constraints.txt
```

**Problem**: Constraints file already ensures correct versions. `--force-reinstall` is redundant and forces unnecessary reinstalls.

**Rule**: Constraints file is sufficient. Only use `--force-reinstall` if you have a specific reason (e.g., corrupted installation).

## Multi-Stage Builds

### ✅ DO: Use Multi-Stage Builds

**Recommended**:
```dockerfile
FROM python:3.11-slim as builder
# Install dependencies
RUN pip install --user -r /tmp/requirements.txt

FROM python:3.11-slim
# Copy only what's needed
COPY --from=builder /home/app/.local /home/app/.local
```

**Benefits**:
- Smaller final image
- Faster deployments
- Better security (fewer packages in final image)

## Layer Optimization

### ✅ DO: Order Layers by Change Frequency

**Recommended**:
```dockerfile
# 1. System dependencies (rarely change)
RUN apt-get update && apt-get install -y ...

# 2. Requirements files (change occasionally)
COPY requirements.txt /tmp/requirements.txt
COPY constraints.txt /tmp/constraints.txt

# 3. Install dependencies (change when requirements change)
RUN pip install -r /tmp/requirements.txt

# 4. Application code (changes frequently)
COPY . .
```

**Benefits**:
- Better layer caching
- Faster rebuilds when only code changes

## Environment Variables

### ✅ DO: Set Environment Variables Explicitly

**Recommended**:
```dockerfile
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/home/app/.local/bin:$PATH
```

**Benefits**:
- Clear configuration
- Reproducible behavior
- Easy to understand

### ❌ DON'T: Set Conflicting Environment Variables

**Avoid**:
```dockerfile
ENV PIP_NO_CACHE_DIR=1  # Disables cache
RUN --mount=type=cache,target=/home/app/.cache/pip ...  # Provides cache
```

**Problem**: Conflicting directives confuse pip and waste resources.

## Security Best Practices

### ✅ DO: Use Non-Root User

**Recommended**:
```dockerfile
RUN useradd --create-home --shell /bin/bash app
USER app
```

**Benefits**:
- Better security
- Follows principle of least privilege

### ✅ DO: Clean Up Package Lists

**Recommended**:
```dockerfile
RUN apt-get update && apt-get install -y ... \
    && rm -rf /var/lib/apt/lists/*
```

**Benefits**:
- Smaller image size
- Faster deployments

## Common Pitfalls

### Pitfall 1: Cache Mount Conflicts

**Symptom**: Builds are slow, cache mount seems unused

**Cause**: Multiple cache control mechanisms

**Fix**: Remove conflicting flags, use only cache mount

### Pitfall 2: Redundant Flags

**Symptom**: Builds reinstalling everything every time

**Cause**: `--force-reinstall` with constraints file

**Fix**: Remove `--force-reinstall`, constraints file is sufficient

### Pitfall 3: Missing Constraints File

**Symptom**: Dependency version conflicts in production

**Cause**: Requirements file allows version ranges

**Fix**: Use constraints file to pin critical dependencies

## Testing Checklist

Before deploying Dockerfile changes:

- [ ] Test build locally: `docker build -t test .`
- [ ] Verify dependencies install correctly
- [ ] Check cache mount is used (look for cache hits in logs)
- [ ] Verify constraints file works (check installed versions)
- [ ] Test with clean cache: `docker build --no-cache -t test .`
- [ ] Measure build time improvement
- [ ] Test on target platform (Render, etc.)

## Performance Optimization Checklist

- [ ] Use multi-stage builds
- [ ] Order layers by change frequency
- [ ] Use cache mounts (not conflicting flags)
- [ ] Clean up package lists
- [ ] Use constraints files for critical dependencies
- [ ] Avoid redundant flags (`--force-reinstall` with constraints)
- [ ] Test build performance improvements

## Render-Specific Considerations

### Build Time Limits

Render has build time limits. Optimize for:
- Faster builds (use cache mounts effectively)
- Fewer network requests (cache dependencies)
- Reliable builds (avoid conflicting flags)

### BuildKit Support

Render supports Docker BuildKit. Use:
- Cache mounts: `--mount=type=cache`
- Build secrets: `--mount=type=secret`
- SSH mounts: `--mount=type=ssh`

## Example: Optimal Dockerfile Pattern

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

# System dependencies with cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app
ENV PATH=/home/app/.local/bin:$PATH
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
# Note: NO PIP_NO_CACHE_DIR here

# Copy requirements and constraints
COPY --chown=app:app requirements.txt /tmp/requirements.txt
COPY --chown=app:app constraints.txt /tmp/constraints.txt

# Install dependencies with cache mount
USER app
RUN --mount=type=cache,target=/home/app/.cache/pip,sharing=locked \
    pip install --user --no-warn-script-location \
    -r /tmp/requirements.txt -c /tmp/constraints.txt
    # Note: NO --no-cache-dir or --force-reinstall

# Final stage
FROM python:3.11-slim

# Runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install -y \
    curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies and code
COPY --from=builder --chown=app:app /home/app/.local /home/app/.local
COPY --chown=app:app . .

# Set environment
ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# User and health check
RUN useradd --create-home --shell /bin/bash app
USER app
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Key Takeaways

1. **Use cache mounts, not conflicting flags**
2. **Constraints file is sufficient - don't add --force-reinstall**
3. **Choose ONE caching strategy, not multiple**
4. **Test locally before deploying**
5. **Monitor build performance after changes**

---

**Last Updated**: 2025-01-10  
**Based on**: FM-041 and FM-042 investigations

