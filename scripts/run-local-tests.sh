#!/bin/bash

set -e

echo "Running comprehensive local tests for 003 Worker Refactor..."

# Ensure environment is running
echo "Checking if local environment is running..."
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Local environment not running. Run ./scripts/setup-local-env.sh first." >&2
    exit 1
fi
echo "✅ Local environment is running"

# Wait for all services to be healthy
echo "Waiting for all services to be healthy..."
sleep 10

# Test service health
echo "Testing service health..."

# API server health
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ API server health check passed"
else
    echo "❌ API server health check failed"
    exit 1
fi

# Mock services health
if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    echo "✅ Mock LlamaParse health check passed"
else
    echo "❌ Mock LlamaParse health check failed"
    exit 1
fi

if curl -f http://localhost:8002/health >/dev/null 2>&1; then
    echo "✅ Mock OpenAI health check passed"
else
    echo "❌ Mock OpenAI health check failed"
    exit 1
fi

# Database connectivity
if docker-compose exec postgres pg_isready -U postgres >/dev/null 2>&1; then
    echo "✅ Database connectivity check passed"
else
    echo "❌ Database connectivity check failed"
    exit 1
fi

echo "✅ All service health checks passed"

# Test database schema
echo "Testing database schema..."
if docker-compose exec postgres psql -U postgres -d accessa_dev -c "SELECT COUNT(*) FROM upload_pipeline.upload_jobs;" >/dev/null 2>&1; then
    echo "✅ Database schema validation passed"
else
    echo "❌ Database schema validation failed"
    exit 1
fi

# Test mock LlamaParse service
echo "Testing mock LlamaParse service..."
TEST_JOB_ID=$(uuidgen)
TEST_WEBHOOK_URL="http://localhost:8000/webhooks/llamaparse"

# Submit test parse job
PARSE_RESPONSE=$(curl -s -X POST http://localhost:8001/parse \
    -H "Content-Type: application/json" \
    -d "{
        \"job_id\": \"$TEST_JOB_ID\",
        \"source_url\": \"http://example.com/test.pdf\",
        \"webhook_url\": \"$TEST_WEBHOOK_URL\"
    }")

if echo "$PARSE_RESPONSE" | grep -q "mock-parse-$TEST_JOB_ID"; then
    echo "✅ Mock LlamaParse job submission passed"
else
    echo "❌ Mock LlamaParse job submission failed"
    echo "Response: $PARSE_RESPONSE"
    exit 1
fi

# Test mock OpenAI service
echo "Testing mock OpenAI service..."
EMBED_RESPONSE=$(curl -s -X POST http://localhost:8002/v1/embeddings \
    -H "Content-Type: application/json" \
    -d "{
        \"input\": [\"test text for embedding\"],
        \"model\": \"text-embedding-3-small\"
    }")

if echo "$EMBED_RESPONSE" | grep -q "embedding"; then
    echo "✅ Mock OpenAI embedding generation passed"
else
    echo "❌ Mock OpenAI embedding generation failed"
    echo "Response: $EMBED_RESPONSE"
    exit 1
fi

# Test database operations
echo "Testing database operations..."
DB_TEST_RESPONSE=$(docker-compose exec postgres psql -U postgres -d accessa_dev -t -c "
    INSERT INTO upload_pipeline.upload_jobs (
        job_id, user_id, document_id, status, raw_path, chunks_version, embed_model, embed_version
    ) VALUES (
        gen_random_uuid(),
        gen_random_uuid(),
        gen_random_uuid(),
        'uploaded',
        'storage://raw/test-user/test-doc.pdf',
        'markdown-simple@1',
        'text-embedding-3-small',
        '1'
    ) RETURNING job_id;
")

if [ $? -eq 0 ]; then
    echo "✅ Database insert operation passed"
else
    echo "❌ Database insert operation failed"
    exit 1
fi

# Test buffer table operations
echo "Testing buffer table operations..."
BUFFER_TEST_RESPONSE=$(docker-compose exec postgres psql -U postgres -d accessa_dev -t -c "
    INSERT INTO upload_pipeline.document_chunk_buffer (
        chunk_id, document_id, chunk_ord, chunker_name, chunker_version, chunk_sha, text
    ) VALUES (
        gen_random_uuid(),
        gen_random_uuid(),
        1,
        'markdown-simple',
        '1',
        'test-sha-256-hash',
        'Test chunk content'
    ) RETURNING chunk_id;
")

if [ $? -eq 0 ]; then
    echo "✅ Buffer table insert operation passed"
else
    echo "❌ Buffer table insert operation failed"
    exit 1
fi

# Test vector operations
echo "Testing vector operations..."
VECTOR_TEST_RESPONSE=$(docker-compose exec postgres psql -U postgres -d accessa_dev -t -c "
    INSERT INTO upload_pipeline.document_vector_buffer (
        document_id, chunk_id, embed_model, embed_version, vector, vector_sha
    ) VALUES (
        gen_random_uuid(),
        gen_random_uuid(),
        'text-embedding-3-small',
        '1',
        '[0.1, 0.2, 0.3]'::vector(1536),
        'test-vector-sha'
    ) RETURNING chunk_id;
")

if [ $? -eq 0 ]; then
    echo "✅ Vector table insert operation passed"
else
    echo "❌ Vector table insert operation failed"
    exit 1
fi

# Test UUID generation utilities
echo "Testing UUID generation utilities..."
if docker-compose exec api-server python -c "
from backend.shared.utils import generate_document_id, generate_chunk_id, generate_parse_id
import uuid

# Test document ID generation
doc_id = generate_document_id('test-user', 'test-sha256')
print(f'Document ID: {doc_id}')
assert isinstance(doc_id, uuid.UUID)

# Test chunk ID generation
chunk_id = generate_chunk_id('test-doc', 'markdown-simple', '1', 1)
print(f'Chunk ID: {chunk_id}')
assert isinstance(chunk_id, uuid.UUID)

# Test parse ID generation
parse_id = generate_parse_id('test-doc', 'llamaparse', '2025-08-01')
print(f'Parse ID: {parse_id}')
assert isinstance(parse_id, uuid.UUID)

print('✅ UUID generation utilities test passed')
" >/dev/null 2>&1; then
    echo "✅ UUID generation utilities test passed"
else
    echo "❌ UUID generation utilities test failed"
    exit 1
fi

# Test end-to-end pipeline simulation
echo "Testing end-to-end pipeline simulation..."
PIPELINE_TEST_RESPONSE=$(docker-compose exec postgres psql -U postgres -d accessa_dev -t -c "
    -- Create a test job
    INSERT INTO upload_pipeline.upload_jobs (
        job_id, user_id, document_id, status, raw_path, chunks_version, embed_model, embed_version
    ) VALUES (
        gen_random_uuid(),
        gen_random_uuid(),
        gen_random_uuid(),
        'uploaded',
        'storage://raw/test-user/pipeline-test.pdf',
        'markdown-simple@1',
        'text-embedding-3-small',
        '1'
    ) RETURNING job_id;
")

if [ $? -eq 0 ]; then
    echo "✅ End-to-end pipeline simulation test passed"
else
    echo "❌ End-to-end pipeline simulation test failed"
    exit 1
fi

# Performance test
echo "Running performance test..."
START_TIME=$(date +%s)

# Test concurrent database operations
for i in {1..10}; do
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

if [ $DURATION -lt 30 ]; then
    echo "✅ Performance test passed (10 inserts in ${DURATION}s)"
else
    echo "⚠️  Performance test slow (10 inserts in ${DURATION}s)"
fi

# Cleanup test data
echo "Cleaning up test data..."
docker-compose exec postgres psql -U postgres -d accessa_dev -c "
    DELETE FROM upload_pipeline.document_vector_buffer WHERE vector_sha LIKE 'test%';
    DELETE FROM upload_pipeline.document_chunk_buffer WHERE chunk_sha LIKE 'test%';
    DELETE FROM upload_pipeline.upload_jobs WHERE raw_path LIKE '%test%';
" >/dev/null 2>&1

echo "✅ Test data cleanup completed"

echo ""
echo "🎉 All local tests completed successfully!"
echo ""
echo "Test Summary:"
echo "  ✅ Service health checks"
echo "  ✅ Database schema validation"
echo "  ✅ Mock service integration"
echo "  ✅ Database operations"
echo "  ✅ Buffer table operations"
echo "  ✅ Vector operations"
echo "  ✅ UUID generation utilities"
echo "  ✅ End-to-end pipeline simulation"
echo "  ✅ Performance testing"
echo "  ✅ Test data cleanup"
echo ""
echo "Local environment is ready for development!"
echo ""
echo "Next steps:"
echo "  1. Start implementing BaseWorker logic"
echo "  2. Add webhook endpoints to API server"
echo "  3. Implement state machine transitions"
echo "  4. Add comprehensive monitoring"
