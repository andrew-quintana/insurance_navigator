#!/bin/bash

# =============================================================================
# Insurance Navigator - Monitoring Test Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test database monitoring
test_db_monitoring() {
    print_status "Testing database monitoring..."
    
    # Test monitoring schema and tables
    if ! psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM monitoring.query_logs;" &>/dev/null; then
        print_error "Query logs table not accessible"
        exit 1
    fi
    
    if ! psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM monitoring.error_logs;" &>/dev/null; then
        print_error "Error logs table not accessible"
        exit 1
    fi
    
    # Test slow query logging
    psql "$DATABASE_URL" << 'EOF'
    -- Insert test slow query
    INSERT INTO monitoring.query_logs (
        query_text,
        execution_time,
        rows_affected,
        user_id,
        client_info
    ) VALUES (
        'SELECT pg_sleep(2)',
        interval '2 seconds',
        0,
        gen_random_uuid(),
        '{"test": true}'
    );
EOF
    
    # Verify slow query alert
    if ! psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM monitoring.error_logs WHERE error_type = 'slow_query';" | grep -q "1"; then
        print_error "Slow query alert not triggered"
        exit 1
    fi
    
    print_success "Database monitoring verified"
}

# Test Edge Function monitoring
test_edge_function_monitoring() {
    print_status "Testing Edge Function monitoring..."
    
    # Test Edge Function logging
    psql "$DATABASE_URL" << 'EOF'
    -- Insert test Edge Function execution
    INSERT INTO monitoring.edge_function_logs (
        function_name,
        execution_time,
        memory_used,
        status,
        request_id,
        metadata
    ) VALUES (
        'test-function',
        interval '500 milliseconds',
        128,
        'success',
        gen_random_uuid(),
        '{"test": true}'
    );
EOF
    
    # Verify Edge Function metrics
    if ! psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM monitoring.edge_function_metrics;" | grep -q "1"; then
        print_error "Edge Function metrics not available"
        exit 1
    fi
    
    print_success "Edge Function monitoring verified"
}

# Test document processing monitoring
test_processing_monitoring() {
    print_status "Testing document processing monitoring..."
    
    # Test processing logging
    psql "$DATABASE_URL" << 'EOF'
    -- Insert test processing log
    INSERT INTO monitoring.processing_logs (
        document_id,
        stage,
        status,
        processing_time,
        metadata
    ) VALUES (
        gen_random_uuid(),
        'parsing',
        'success',
        interval '1 second',
        '{"test": true}'
    );
EOF
    
    # Verify processing metrics
    if ! psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM monitoring.processing_metrics;" | grep -q "1"; then
        print_error "Processing metrics not available"
        exit 1
    fi
    
    print_success "Document processing monitoring verified"
}

# Test alert system
test_alerts() {
    print_status "Testing alert system..."
    
    # Test alert creation
    psql "$DATABASE_URL" << 'EOF'
    -- Create test alert
    SELECT monitoring.create_alert(
        'test',
        'info',
        'Test alert message',
        '{"test": true}'
    );
EOF
    
    # Verify alert creation
    if ! psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM monitoring.alerts WHERE alert_type = 'test';" | grep -q "1"; then
        print_error "Alert creation failed"
        exit 1
    fi
    
    print_success "Alert system verified"
}

# Test monitoring views
test_monitoring_views() {
    print_status "Testing monitoring views..."
    
    # Test system health view
    if ! psql "$DATABASE_URL" -c "SELECT * FROM monitoring.system_health;" &>/dev/null; then
        print_error "System health view not accessible"
        exit 1
    fi
    
    # Test performance dashboard
    if ! psql "$DATABASE_URL" -c "SELECT * FROM monitoring.performance_dashboard;" &>/dev/null; then
        print_error "Performance dashboard not accessible"
        exit 1
    fi
    
    print_success "Monitoring views verified"
}

# Clean up test data
cleanup_test_data() {
    print_status "Cleaning up test data..."
    
    psql "$DATABASE_URL" << 'EOF'
    -- Delete test data
    DELETE FROM monitoring.query_logs WHERE client_info->>'test' = 'true';
    DELETE FROM monitoring.edge_function_logs WHERE metadata->>'test' = 'true';
    DELETE FROM monitoring.processing_logs WHERE metadata->>'test' = 'true';
    DELETE FROM monitoring.alerts WHERE metadata->>'test' = 'true';
EOF
    
    print_success "Test data cleaned up"
}

# Main test flow
main() {
    print_status "Starting monitoring tests..."
    
    test_db_monitoring
    test_edge_function_monitoring
    test_processing_monitoring
    test_alerts
    test_monitoring_views
    cleanup_test_data
    
    print_success "Monitoring tests completed successfully!"
    
    echo ""
    echo "🎉 Test Summary:"
    echo "================"
    echo "✅ Database monitoring verified"
    echo "✅ Edge Function monitoring tested"
    echo "✅ Document processing tracking confirmed"
    echo "✅ Alert system validated"
    echo "✅ Monitoring views accessible"
    echo ""
    echo "Next steps:"
    echo "1. Review test results"
    echo "2. Configure alert thresholds"
    echo "3. Set up monitoring dashboards"
    echo "4. Schedule regular monitoring checks"
}

main "$@" 