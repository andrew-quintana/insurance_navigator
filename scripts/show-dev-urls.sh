#!/bin/bash
# ========== DEVELOPMENT ENVIRONMENT URLS ==========
# Shows all service URLs and log viewing commands

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Development Environment Ready"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get Supabase URLs if running
if supabase status >/dev/null 2>&1; then
    SUPABASE_STATUS=$(supabase status 2>/dev/null)
    echo "📊 Supabase Services:"
    echo "$SUPABASE_STATUS" | grep -E "(API URL|Database URL|Studio URL)" | sed 's/^/   /'
    echo ""
fi

# Show service URLs
echo "🌐 Service URLs:"
echo "   Frontend:     http://localhost:5200"
echo "   API:          http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   Supabase:     http://127.0.0.1:54321"
echo "   Supabase Studio: http://127.0.0.1:54323"
echo ""

echo "📋 View Service Logs:"
echo "   All services:     overmind logs"
echo "   Frontend:         overmind logs frontend"
echo "   API & Worker:     overmind logs docker-services"
echo "   Supabase:         overmind logs supabase"
echo "   Specific service: overmind connect <service-name>"
echo ""

echo "🔧 Other Commands:"
echo "   Stop services:    overmind stop  (or Ctrl+C)"
echo "   Restart service:   overmind restart <service-name>"
echo "   Service status:   overmind status"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

