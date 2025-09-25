#!/bin/bash
# ========== START DEVELOPMENT ENVIRONMENT ==========
# All components are LOCAL (frontend, backend, database)

set -e

echo "🚀 Starting Development Environment (All Local Components)"
echo "=================================================="

# Set environment and load development environment
export ENVIRONMENT=development
export $(cat .env.development | grep -v '^#' | xargs)

echo "📊 Environment: Development"
echo "🏠 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"
echo "🗄️  Database: http://127.0.0.1:54321"
echo ""

# Start Supabase local development
echo "1️⃣ Starting Supabase local development..."
supabase start

# Start ngrok tunnel for webhooks
echo "1.5️⃣ Starting ngrok tunnel..."
ngrok http 8000 --log=stdout &
NGROK_PID=$!

# Wait for ngrok to be ready
echo "Waiting for ngrok to be ready..."
sleep 5
if curl -f http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')
    echo "✅ Ngrok ready: $NGROK_URL"
else
    echo "⚠️  Ngrok not ready yet, continuing..."
fi

# Store ngrok PID for cleanup
echo $NGROK_PID > .ngrok.pid

# Start backend API
echo "2️⃣ Starting backend API..."
docker-compose up -d api worker

# Wait for backend to be ready
echo "3️⃣ Waiting for backend to be ready..."
sleep 10
curl -f http://localhost:8000/health > /dev/null 2>&1 || echo "⚠️  Backend not ready yet, continuing..."

# Start frontend
echo "4️⃣ Starting frontend..."
cd ui
cp .env.development .env.local
npm run dev &

echo ""
echo "✅ Development environment started!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"
echo "🗄️  Database: http://127.0.0.1:54321"
echo "📊 Supabase Studio: http://127.0.0.1:54323"
echo "🌐 Ngrok Tunnel: $NGROK_URL"
echo "📊 Ngrok Dashboard: http://localhost:4040"
echo ""
echo "Press Ctrl+C to stop all services"
