# Development Scripts

This directory contains scripts to streamline the development workflow, particularly for setting up ngrok tunnels and updating configuration files automatically.

## Scripts

### `dev_setup.sh` / `dev_setup.py`
Automatically starts ngrok, extracts the URL, and updates all necessary configuration files.

**Features:**
- ✅ Checks if API server is running
- ✅ Starts ngrok tunnel on port 8000
- ✅ Extracts ngrok URL automatically
- ✅ Updates `.env.development` with ngrok URL
- ✅ Updates `ui/.env.local` with ngrok URL
- ✅ Updates worker configuration with ngrok URL
- ✅ Creates backup files before modification
- ✅ Provides clear status messages and next steps

**Usage:**
```bash
# Bash version (Linux/macOS)
./scripts/dev_setup.sh

# Python version (cross-platform)
python scripts/dev_setup.py
```

### `dev_cleanup.sh`
Stops ngrok and restores original configuration files.

**Features:**
- ✅ Stops ngrok processes
- ✅ Cleans up log files
- ✅ Restores backup configuration files
- ✅ Provides cleanup summary

**Usage:**
```bash
./scripts/dev_cleanup.sh
```

## Prerequisites

1. **ngrok installed**: Download from [ngrok.com](https://ngrok.com/download) or install via package manager
2. **API server running**: Start with `ENVIRONMENT=development python main.py`
3. **Python 3.6+** (for Python version of dev_setup)

## Workflow

### Quick Start
```bash
# 1. Start API server
ENVIRONMENT=development python main.py &

# 2. Run development setup
./scripts/dev_setup.sh

# 3. Start enhanced worker
python backend/workers/enhanced_runner.py &

# 4. Start frontend
cd ui && npm run dev &
```

### Cleanup
```bash
# Stop everything and restore configs
./scripts/dev_cleanup.sh
```

## What Gets Updated

The scripts automatically update these files with the ngrok URL:

1. **`.env.development`**
   ```bash
   NGROK_URL=https://abc123.ngrok-free.app
   ```

2. **`ui/.env.local`**
   ```bash
   NEXT_PUBLIC_API_URL=https://abc123.ngrok-free.app
   NEXT_PUBLIC_API_BASE_URL=https://abc123.ngrok-free.app
   ```

3. **`backend/workers/enhanced_base_worker.py`**
   ```python
   base_url = "https://abc123.ngrok-free.app"
   ```

## Troubleshooting

### ngrok not found
```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/download
```

### API server not running
```bash
# Start API server first
ENVIRONMENT=development python main.py
```

### Permission denied
```bash
# Make scripts executable
chmod +x scripts/*.sh scripts/*.py
```

### Port 8000 already in use
```bash
# Kill existing processes
pkill -f "python.*main.py"
# or change port in the scripts
```

## Benefits

- **🚀 Faster setup**: No manual URL copying and pasting
- **🔄 Consistent configuration**: All files updated with same URL
- **🛡️ Safe**: Creates backups before modifying files
- **📊 Monitoring**: Easy access to ngrok dashboard
- **🧹 Cleanup**: Easy restoration of original state

## Integration with CI/CD

These scripts can be integrated into your development workflow:

```bash
# In your development workflow
make dev-setup    # calls ./scripts/dev_setup.sh
make dev-cleanup  # calls ./scripts/dev_cleanup.sh
```

Or add to your `package.json`:
```json
{
  "scripts": {
    "dev:setup": "./scripts/dev_setup.sh",
    "dev:cleanup": "./scripts/dev_cleanup.sh"
  }
}
```
