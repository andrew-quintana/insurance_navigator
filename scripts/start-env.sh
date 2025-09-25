#!/bin/bash
# ========== ENVIRONMENT STARTER ==========
# Start development, staging, or production environment

set -e

ENV=${1:-dev}

case $ENV in
  dev|development)
    echo "🚀 Starting Development Environment..."
    ./scripts/start-dev.sh
    ;;
  staging)
    echo "🚀 Starting Staging Environment..."
    ./scripts/start-staging.sh
    ;;
  prod|production)
    echo "🚀 Starting Production Environment..."
    ./scripts/start-production.sh
    ;;
  *)
    echo "❌ Invalid environment. Usage:"
    echo "  ./scripts/start-env.sh dev|development    # Start development (all local)"
    echo "  ./scripts/start-env.sh staging            # Start staging (all cloud staging)"
    echo "  ./scripts/start-env.sh prod|production    # Start production (all cloud production)"
    exit 1
    ;;
esac
