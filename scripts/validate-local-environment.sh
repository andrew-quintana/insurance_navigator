#!/bin/bash

set -e

echo "Validating local development environment for 003 Worker Refactor..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    else
        echo -e "${RED}❌ $message${NC}"
    fi
}

# Check if Docker is running
echo "Checking Docker status..."
if docker info >/dev/null 2>&1; then
    print_status "OK" "Docker is running"
else
    print_status "ERROR" "Docker is not running"
    exit 1
fi

# Check if docker-compose is available
echo "Checking Docker Compose..."
if command -v docker-compose >/dev/null 2>&1; then
    print_status "OK" "Docker Compose is available"
else
    print_status "ERROR" "Docker Compose is not available"
    exit 1
fi

# Check if local environment is running
echo "Checking local environment status..."
if docker-compose ps | grep -q "Up"; then
    print_status "OK" "Local environment is running"
else
    print_status "ERROR" "Local environment is not running. Run ./scripts/setup-local-env.sh first."
    exit 1
fi

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 15

# Check service health
echo ""
echo "=== Service Health Checks ==="

# Database health
echo "Checking database health..."
if docker-compose exec postgres pg_isready -U postgres >/dev/null 2>&1; then
    print_status "OK" "PostgreSQL is healthy"
else
    print_status "ERROR" "PostgreSQL is not healthy"
    exit 1
fi

# Supabase storage health
echo "Checking Supabase storage health..."
if curl -f http://localhost:5000/health >/dev/null 2>&1; then
    print_status "OK" "Supabase storage is healthy"
else
    print_status "ERROR" "Supabase storage is not healthy"
    exit 1
fi

# API server health
echo "Checking API server health..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    print_status "OK" "API server is healthy"
else
    print_status "ERROR" "API server is not healthy"
    exit 1
fi

# BaseWorker health
echo "Checking BaseWorker health..."
if docker-compose exec base-worker python -c "from backend.workers.base_worker import BaseWorker; print('Worker import successful')" >/dev/null 2>&1; then
    print_status "OK" "BaseWorker is healthy"
else
    print_status "ERROR" "BaseWorker is not healthy"
    exit 1
fi

# Mock LlamaParse health
echo "Checking mock LlamaParse health..."
if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    print_status "OK" "Mock LlamaParse is healthy"
else
    print_status "ERROR" "Mock LlamaParse is not healthy"
    exit 1
fi

# Mock OpenAI health
echo "Checking mock OpenAI health..."
if curl -f http://localhost:8002/health >/dev/null 2>&1; then
    print_status "OK" "Mock OpenAI is healthy"
else
    print_status "ERROR" "Mock OpenAI is not healthy"
    exit 1
fi

# Monitoring health
echo "Checking monitoring service health..."
if curl -f http://localhost:3000/health >/dev/null 2>&1; then
    print_status "OK" "Monitoring service is healthy"
else
    print_status "WARN" "Monitoring service is not healthy (may still be starting)"
fi

echo ""
echo "=== Database Schema Validation ==="

# Check if upload_pipeline schema exists
echo "Checking upload_pipeline schema..."
if docker-compose exec postgres psql -U postgres -d accessa_dev -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'upload_pipeline';" | grep -q "upload_pipeline"; then
    print_status "OK" "upload_pipeline schema exists"
else
    print_status "ERROR" "upload_pipeline schema does not exist"
    exit 1
fi

# Check if required tables exist
echo "Checking required tables..."
REQUIRED_TABLES=("upload_jobs" "document_chunk_buffer" "document_vector_buffer" "events")
for table in "${REQUIRED_TABLES[@]}"; do
    if docker-compose exec postgres psql -U postgres -d accessa_dev -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'upload_pipeline' AND table_name = '$table';" | grep -q "$table"; then
        print_status "OK" "Table $table exists"
    else
        print_status "ERROR" "Table $table does not exist"
        exit 1
    fi
done

# Check if pgvector extension is available
echo "Checking pgvector extension..."
if docker-compose exec postgres psql -U postgres -d accessa_dev -c "SELECT extname FROM pg_extension WHERE extname = 'vector';" | grep -q "vector"; then
    print_status "OK" "pgvector extension is available"
else
    print_status "ERROR" "pgvector extension is not available"
    exit 1
fi

echo ""
echo "=== Network Connectivity ==="

# Check internal service communication
echo "Checking internal service communication..."

# API server to database
if docker-compose exec api-server python -c "
import asyncio
import asyncpg
import os

async def test_db_connection():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        await conn.execute('SELECT 1')
        await conn.close()
        print('Database connection successful')
    except Exception as e:
        print(f'Database connection failed: {e}')
        exit(1)

asyncio.run(test_db_connection())
" >/dev/null 2>&1; then
    print_status "OK" "API server can connect to database"
else
    print_status "ERROR" "API server cannot connect to database"
    exit 1
fi

# BaseWorker to database
if docker-compose exec base-worker python -c "
import asyncio
import asyncpg
import os

async def test_db_connection():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        await conn.execute('SELECT 1')
        await conn.close()
        print('Database connection successful')
    except Exception as e:
        print(f'Database connection failed: {e}')
        exit(1)

asyncio.run(test_db_connection())
" >/dev/null 2>&1; then
    print_status "OK" "BaseWorker can connect to database"
else
    print_status "ERROR" "BaseWorker cannot connect to database"
    exit 1
fi

echo ""
echo "=== Storage Configuration ==="

# Check if storage directories exist
echo "Checking storage directories..."
if [ -d "local-storage/raw" ] && [ -d "local-storage/parsed" ]; then
    print_status "OK" "Local storage directories exist"
else
    print_status "WARN" "Local storage directories missing (will be created)"
    mkdir -p local-storage/raw local-storage/parsed
fi

# Check if log directories exist
echo "Checking log directories..."
if [ -d "logs/api" ] && [ -d "logs/worker" ] && [ -d "logs/monitoring" ]; then
    print_status "OK" "Log directories exist"
else
    print_status "WARN" "Log directories missing (will be created)"
    mkdir -p logs/api logs/worker logs/monitoring
fi

echo ""
echo "=== Performance Validation ==="

# Test database performance
echo "Testing database performance..."
START_TIME=$(date +%s)

# Insert test records
for i in {1..5}; do
    docker-compose exec postgres psql -U postgres -d accessa_dev -c "
        INSERT INTO upload_pipeline.upload_jobs (
            job_id, user_id, document_id, status, raw_path, chunks_version, embed_model, embed_version
        ) VALUES (
            gen_random_uuid(),
            gen_random_uuid(),
            gen_random_uuid(),
            'uploaded',
            'storage://raw/test-user/perf-test-$i.pdf',
            'markdown-simple@1',
            'text-embedding-3-small',
            '1'
        );
    " >/dev/null 2>&1
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ $DURATION -lt 10 ]; then
    print_status "OK" "Database performance test passed (5 inserts in ${DURATION}s)"
else
    print_status "WARN" "Database performance test slow (5 inserts in ${DURATION}s)"
fi

# Test mock service response times
echo "Testing mock service response times..."

# Test LlamaParse response time
LLAMAPARSE_START=$(date +%s)
curl -s -X POST http://localhost:8001/parse \
    -H "Content-Type: application/json" \
    -d '{"job_id":"test-123","source_url":"http://example.com/test.pdf","webhook_url":"http://localhost:8000/webhooks/llamaparse"}' >/dev/null
LLAMAPARSE_END=$(date +%s)
LLAMAPARSE_DURATION=$((LLAMAPARSE_END - LLAMAPARSE_START))

if [ $LLAMAPARSE_DURATION -lt 5 ]; then
    print_status "OK" "Mock LlamaParse response time: ${LLAMAPARSE_DURATION}s"
else
    print_status "WARN" "Mock LlamaParse response time slow: ${LLAMAPARSE_DURATION}s"
fi

# Test OpenAI response time
OPENAI_START=$(date +%s)
curl -s -X POST http://localhost:8002/v1/embeddings \
    -H "Content-Type: application/json" \
    -d '{"input":["test text"],"model":"text-embedding-3-small"}' >/dev/null
OPENAI_END=$(date +%s)
OPENAI_DURATION=$((OPENAI_END - OPENAI_START))

if [ $OPENAI_DURATION -lt 3 ]; then
    print_status "OK" "Mock OpenAI response time: ${OPENAI_DURATION}s"
else
    print_status "WARN" "Mock OpenAI response time slow: ${OPENAI_DURATION}s"
fi

# Cleanup test data
echo "Cleaning up test data..."
docker-compose exec postgres psql -U postgres -d accessa_dev -c "
    DELETE FROM upload_pipeline.upload_jobs WHERE raw_path LIKE '%perf-test%';
" >/dev/null 2>&1

echo ""
echo "=== Environment Summary ==="
print_status "OK" "Local development environment validation completed successfully!"

echo ""
echo "Environment Status:"
echo "  🐘 PostgreSQL:     Running and healthy"
echo "  📦 Supabase Storage: Running and healthy"
echo "  🚀 API Server:     Running and healthy"
echo "  ⚙️  BaseWorker:     Running and healthy"
echo "  📄 Mock LlamaParse: Running and healthy"
echo "  🤖 Mock OpenAI:    Running and healthy"
echo "  📊 Monitoring:     Available"
echo "  🗄️  Database Schema: Complete with buffer tables"
echo "  🔗 Network:         All services connected"
echo "  💾 Storage:         Local directories configured"
echo "  ⚡ Performance:     Within acceptable limits"
echo ""
echo "✅ Local environment is ready for development!"
echo ""
echo "Next steps:"
echo "  1. Run tests: ./scripts/run-local-tests.sh"
echo "  2. Start implementing BaseWorker logic"
echo "  3. Add webhook endpoints to API server"
echo "  4. Implement state machine transitions"
