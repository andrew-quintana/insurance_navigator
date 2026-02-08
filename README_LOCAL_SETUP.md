# Local Development Setup - Quick Reference

## 🚀 One-Command Setup

```bash
# Complete automated setup
./setup_local_dev.sh
```

## 📝 Manual Setup

```bash
# 1. Start Supabase
supabase start

# 2. Setup Python environment  
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Start backend
python main.py

# 4. Start frontend (new terminal)
cd ui && npm install && npm run dev
```

## 🧪 Validation & Testing

```bash
# Validate complete setup
python validate_local_setup.py

# Run API integration tests  
python test_api_endpoint_direct.py

# Test frontend build & TypeScript validation
cd ui && npm run build

# TypeScript-only validation (faster)
cd ui && npm run type-check

# Vercel deployment readiness check
cd ui && NODE_ENV=production npm run build
```

## 🛑 Stop All Services

```bash
# Stop everything cleanly
./stop_local_dev.sh

# Stop and clean logs
./stop_local_dev.sh --clean-logs
```

## 🌐 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000  
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Supabase Studio**: http://localhost:54323

## 📖 Detailed Documentation

See `SETUP_AND_TEST_LOCAL.md` for complete setup instructions, troubleshooting, and testing procedures.

## ✨ What's Included

- **Automated Environment Setup**: Virtual environment, dependencies, database
- **Service Orchestration**: Supabase, FastAPI backend, Next.js frontend
- **Health Validation**: Comprehensive testing of all components
- **Development Tools**: Hot reload, API docs, database studio
- **Troubleshooting**: Common issues and solutions