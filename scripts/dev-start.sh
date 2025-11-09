#!/bin/bash
# ========== DEVELOPMENT ENVIRONMENT STARTER ==========
# Convenience wrapper for Overmind to start development environment
# This script checks prerequisites and starts all services via Overmind

set -e

echo "🚀 Starting Development Environment with Overmind"
echo "=================================================="

# Check if Overmind is installed
if ! command -v overmind &> /dev/null; then
    echo "❌ Overmind is not installed."
    echo ""
    echo "Installation instructions:"
    echo "  macOS:  brew install overmind"
    echo "  Linux:  See https://github.com/DarthSim/overmind#installation"
    echo ""
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI is not installed."
    echo ""
    echo "Installation:"
    echo "  macOS:  brew install supabase/tap/supabase"
    echo "  Linux:  See https://supabase.com/docs/guides/cli"
    echo ""
    exit 1
fi

# Check if .env.development exists
if [ ! -f .env.development ]; then
    echo "⚠️  Warning: .env.development not found"
    echo "   Create it from config/env.development.example"
    echo ""
fi

# Check if Node.js is installed (for frontend)
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed."
    echo "   Required for frontend development server"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed."
    echo "   Required for frontend development server"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Start Overmind
echo "Starting all services..."
echo ""
overmind start

