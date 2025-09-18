# Insurance Navigator Service Setup Guide

## 🚀 Quick Start

### Option 1: All-in-One Script (Recommended)
```bash
./start_services.sh
```
This starts both API server and worker in the background and shows status.

### Option 2: Separate Terminals (For Development)

#### Terminal 1: API Server
```bash
./start_api_server.sh
```

#### Terminal 2: Simple Worker
```bash
./start_worker.sh
```

## 📋 Service Details

### API Server
- **Port**: 8000
- **URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Logs**: `tail -f logs/api_server.log`

### Simple Worker
- **Function**: Processes queued upload jobs
- **Logs**: `tail -f logs/simple_worker.log`

## 🔍 Monitoring Commands

### Check Service Status
```bash
# Check running processes
ps aux | grep -E "(python|uvicorn)" | grep -v grep

# Check API server health
curl http://localhost:8000/health

# Check worker logs
tail -f logs/simple_worker.log
```

### Test Upload Functionality
```bash
# Test upload endpoint
curl -X POST http://localhost:8000/upload-document-backend-no-auth \
  -F "file=@test_upload.pdf" \
  -F "policy_id=test-policy-123" \
  -s | jq .
```

## 🛠️ Troubleshooting

### If Services Won't Start
1. Check if ports are in use:
   ```bash
   lsof -i :8000
   ```

2. Check database connection:
   ```bash
   # Make sure Supabase is running locally
   curl http://localhost:54321/health
   ```

3. Check logs for errors:
   ```bash
   tail -20 logs/api_server.log
   tail -20 logs/simple_worker.log
   ```

### If Services Stop Unexpectedly
1. Check system resources:
   ```bash
   top
   ```

2. Restart services:
   ```bash
   # Kill existing processes
   pkill -f "python main.py"
   pkill -f "simple_worker.py"
   
   # Restart
   ./start_services.sh
   ```

## 📊 Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Server    │    │  Simple Worker  │
│   (Port 3000)   │───▶│   (Port 8000)   │───▶│   (Background)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Local Supabase │    │  Upload Jobs    │
                       │  (Port 54321)   │    │  Database       │
                       └─────────────────┘    └─────────────────┘
```

## 🔧 Environment Variables

The services use these environment variables:
- `ENVIRONMENT=development`
- `DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres?sslmode=disable`
- `SUPABASE_URL=http://localhost:54321`

## 📝 Log Locations

- **API Server**: `logs/api_server.log`
- **Simple Worker**: `logs/simple_worker.log`
- **Combined**: Use `tail -f logs/*.log` to watch all logs

## 🚨 Important Notes

1. **Keep Services Running**: Don't cancel the terminal processes - they need to run continuously
2. **Memory Usage**: The system is configured to handle high memory usage (up to 95% in development)
3. **Database**: Make sure local Supabase is running on port 54321
4. **Logs**: Monitor logs for any errors or issues

## 🎯 Next Steps

1. Start the services using one of the methods above
2. Test the upload functionality
3. Monitor the logs for any issues
4. Use the frontend to test the complete workflow
