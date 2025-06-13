# Configuration Files

This directory contains all configuration files organized by category.

## Directory Structure

### `docker/`
- `Dockerfile` - Docker container configuration
- `.dockerignore` - Files to exclude from Docker builds

### `python/`
- `requirements.txt` - Python dependencies for production
- `requirements-dev.txt` - Additional dependencies for development
- `requirements_backup.txt` - Backup of previous requirements
- `setup.py` - Python package setup configuration
- `pytest.ini` - Pytest configuration

### `node/`
- `package.json` - Node.js dependencies and scripts
- `package-lock.json` - Locked dependency versions

### `render/`
- `render.yaml` - Render deployment configuration
- `.render-deploy-trigger` - Render deployment trigger file

### `environment/`
- `env.example` - Environment variables template
- `.cursorrules` - Cursor editor rules
- `.cursorignore` - Files to ignore in Cursor editor

## Backward Compatibility

Symlinks are maintained in the root directory for commonly referenced files:
- `requirements.txt` → `config/python/requirements.txt`
- `Dockerfile` → `config/docker/Dockerfile`
- `render.yaml` → `config/render/render.yaml`

This ensures existing scripts and deployment processes continue to work without modification. 