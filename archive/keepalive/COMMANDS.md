# API Keep-Alive Commands

## Quick Commands

### From project root:
```bash
# Start keep-alive service
./backend/scripts/keepalive/run_keepalive.sh start

# Check status
./backend/scripts/keepalive/run_keepalive.sh status

# Stop service
./backend/scripts/keepalive/run_keepalive.sh stop

# Monitor logs
tail -f backend/scripts/keepalive/api_keepalive.log
```

### From keepalive directory:
```bash
cd backend/scripts/keepalive

# Start service
./start_keepalive.sh

# Check status
./status_keepalive.sh

# Stop service
./stop_keepalive.sh

# Monitor logs
tail -f api_keepalive.log
```

## Custom Configuration

```bash
# Custom interval (2 minutes)
INTERVAL=120 ./backend/scripts/keepalive/start_keepalive.sh

# Different API URL
API_URL=https://my-api.onrender.com ./backend/scripts/keepalive/start_keepalive.sh

# Run directly with Python
python3 backend/scripts/keepalive/keep_api_warm_simple.py
```

## Current Status

The keep-alive service is currently **RUNNING** and will:
- Make health checks every 5 minutes
- Keep the API service warm to prevent spin-down
- Log all activity to `backend/scripts/keepalive/api_keepalive.log`
- Run continuously until stopped
