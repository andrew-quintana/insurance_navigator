#!/bin/bash
# Keep Render Free Tier App Warm
# Prevents the app from sleeping by pinging every 14 minutes

# Configuration
APP_URL="https://your-app-name.onrender.com"
HEALTH_ENDPOINT="/health"
PING_INTERVAL=840  # 14 minutes in seconds

echo "🔥 Starting Keep Warm Service for Render Free Tier"
echo "URL: ${APP_URL}${HEALTH_ENDPOINT}"
echo "Interval: ${PING_INTERVAL} seconds (14 minutes)"
echo "================================================"

# Function to ping the app
ping_app() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local response=$(curl -s -o /dev/null -w "%{http_code},%{time_total}" "${APP_URL}${HEALTH_ENDPOINT}")
    local status_code=$(echo $response | cut -d',' -f1)
    local response_time=$(echo $response | cut -d',' -f2)
    
    if [ "$status_code" = "200" ]; then
        echo "✅ [$timestamp] App is warm (${response_time}s)"
    else
        echo "⚠️  [$timestamp] App may be sleeping - Status: $status_code (${response_time}s)"
    fi
}

# Main loop
while true; do
    ping_app
    sleep $PING_INTERVAL
done 