# API Keep-Alive Service

This directory contains scripts to keep the API service warm and prevent it from spinning down due to inactivity on Render.com.

## Files

- `keep_api_warm.py` - Full-featured async keep-alive service with detailed logging
- `keep_api_warm_simple.py` - Lightweight synchronous version for continuous operation
- `start_keepalive.sh` - Start the keep-alive service
- `stop_keepalive.sh` - Stop the keep-alive service
- `status_keepalive.sh` - Check the status of the keep-alive service

## Quick Start

### Start the keep-alive service
```bash
cd backend/scripts/keepalive
./start_keepalive.sh
```

### Check status
```bash
cd backend/scripts/keepalive
./status_keepalive.sh
```

### Stop the service
```bash
cd backend/scripts/keepalive
./stop_keepalive.sh
```

### Monitor logs
```bash
cd backend/scripts/keepalive
tail -f api_keepalive.log
```

## Configuration

You can customize the behavior using environment variables:

- `API_URL` - API service URL (default: ***REMOVED***)
- `INTERVAL` - Keep-alive interval in seconds (default: 300 = 5 minutes)
- `LOG_FILE` - Log file path (default: api_keepalive.log)
- `PID_FILE` - PID file path (default: api_keepalive.pid)

## Examples

### Custom interval (2 minutes)
```bash
INTERVAL=120 ./start_keepalive.sh
```

### Different API URL
```bash
API_URL=https://my-api.onrender.com ./start_keepalive.sh
```

### Run directly with Python
```bash
python3 keep_api_warm_simple.py ***REMOVED*** 300
```

## How it works

The keep-alive service periodically makes HTTP requests to the API service to prevent it from spinning down due to inactivity. It:

1. Makes a health check request to `/health` endpoint
2. If health check fails, tries a test endpoint as fallback
3. Logs all activity and maintains success/failure statistics
4. Runs continuously until stopped

## Troubleshooting

- If the service fails to start, check the log file for errors
- If the API is not responding, the service will retry every minute
- Use `./status_keepalive.sh` to check if the service is running
- Check the process with `ps aux | grep keep_api_warm`
