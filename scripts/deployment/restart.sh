#!/bin/bash

echo "🔄 Restarting Insurance Navigator..."

echo "🛑 Killing existing processes..."
# Kill existing Python processes
pkill -f "python main.py" || echo "No Python processes to kill"

# Kill existing Node/Next.js processes
pkill -f "next dev" || echo "No Next.js processes to kill"
pkill -f "node.*next" || echo "No Node processes to kill"

# Wait a moment for processes to clean up
sleep 2

echo "🧹 Cleaning up caches..."
# Clean Next.js cache
if [ -d "ui/.next" ]; then
    rm -rf ui/.next
    echo "Cleared Next.js .next directory"
fi

if [ -d "ui/node_modules/.cache" ]; then
    rm -rf ui/node_modules/.cache
    echo "Cleared Node modules cache"
fi

echo "🚀 Starting services..."
# Start both services with concurrently
npm run dev 