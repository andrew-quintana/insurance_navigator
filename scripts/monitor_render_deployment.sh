#!/bin/bash
# Monitor Render Production Deployment
# Guide for tracking build progress and testing deployment

echo "🚀 Render Production Deployment Monitor"
echo "======================================="
echo

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}📊 Real-Time Monitoring Available:${NC}"
echo "1. 🔍 Live Build Logs with timestamps"
echo "2. 📈 Resource usage (CPU, memory, build time)"
echo "3. 🐳 Docker layer progress"
echo "4. 📦 Package installation status"
echo "5. 🚨 Error detection with stack traces"
echo

echo -e "${BLUE}🌐 Access Your Render Dashboard:${NC}"
echo "1. Go to: https://dashboard.render.com"
echo "2. Click on your service: 'insurance-navigator-api'"
echo "3. Navigate to: 'Events' or 'Logs' tab"
echo

echo -e "${BLUE}⏱️  Expected Build Timeline:${NC}"
echo "├─ 📥 Pulling base image: ~30-60 seconds"
echo "├─ 🔧 Installing system deps: ~1-2 minutes"
echo "├─ 🐍 Installing Python packages: ~8-15 minutes"
echo "│   ├─ torch, transformers: ~5-8 minutes"
echo "│   ├─ langchain, anthropic: ~2-3 minutes"
echo "│   └─ other packages: ~1-4 minutes"
echo "├─ 📂 Copying application: ~10-30 seconds"
echo "├─ 🏗️  Final image creation: ~30-60 seconds"
echo "└─ 🚀 Service startup: ~30-60 seconds"
echo
echo -e "${YELLOW}Total Expected Time: 10-20 minutes${NC}"
echo

echo -e "${BLUE}🧪 Test Commands (Run after deployment):${NC}"
echo
echo "# Health Check"
echo "curl https://your-app-name.onrender.com/health"
echo
echo "# API Documentation"
echo "curl https://your-app-name.onrender.com/docs"
echo
echo "# Test with response time"
echo "curl -w \"@curl-format.txt\" https://your-app-name.onrender.com/health"
echo

echo -e "${BLUE}📱 Render Mobile App:${NC}"
echo "Download Render mobile app for push notifications!"
echo

echo -e "${GREEN}🔔 What to Watch For:${NC}"
echo "✅ 'Building...' → 'Live' status change"
echo "✅ Green checkmarks in build logs"
echo "✅ Final message: 'Service is live'"
echo "⚠️  Yellow warnings (usually non-critical)"
echo "❌ Red errors (need investigation)"

# Function to generate curl format file
create_curl_format() {
    cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}s\n
        time_connect:  %{time_connect}s\n
     time_appconnect:  %{time_appconnect}s\n
    time_pretransfer:  %{time_pretransfer}s\n
       time_redirect:  %{time_redirect}s\n
  time_starttransfer:  %{time_starttransfer}s\n
                     ----------\n
          time_total:  %{time_total}s\n
           http_code:  %{http_code}\n
EOF
    echo -e "${GREEN}✅ Created curl-format.txt for response time testing${NC}"
}

echo
echo -e "${BLUE}🛠️  Would you like to create curl timing format? (y/n)${NC}"
read -p "Create curl-format.txt? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    create_curl_format
fi

echo
echo -e "${GREEN}🎯 Quick Actions:${NC}"
echo "1. Open Render Dashboard: https://dashboard.render.com"
echo "2. Check build logs in real-time"
echo "3. Wait for 'Live' status"
echo "4. Test health endpoint"
echo "5. Share API URL with frontend team!"
echo 