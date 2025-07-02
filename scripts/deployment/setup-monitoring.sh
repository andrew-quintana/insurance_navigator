#!/bin/bash

# =============================================================================
# Insurance Navigator - Monitoring Setup Script
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

# Setup database monitoring
setup_db_monitoring() {
    print_status "Setting up database monitoring..."
    
    psql "$DATABASE_URL" << 'EOF'
    -- Create monitoring schema
    CREATE SCHEMA IF NOT EXISTS monitoring;

    -- Create performance monitoring view
    CREATE OR REPLACE VIEW monitoring.performance_metrics AS
    SELECT
        schemaname,
        relname,
        seq_scan,
        seq_tup_read,
        idx_scan,
        idx_tup_fetch,
        n_tup_ins,
        n_tup_upd,
        n_tup_del,
        n_live_tup,
        n_dead_tup,
        last_vacuum,
        last_autovacuum,
        last_analyze,
        last_autoanalyze
    FROM pg_stat_user_tables;

    -- Create query performance logging
    CREATE TABLE IF NOT EXISTS monitoring.query_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        query_text TEXT,
        execution_time INTERVAL,
        rows_affected INTEGER,
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        user_id UUID,
        client_info JSONB
    );

    -- Create error logging table
    CREATE TABLE IF NOT EXISTS monitoring.error_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        error_type TEXT,
        error_message TEXT,
        error_stack TEXT,
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        context JSONB
    );

    -- Create function to log slow queries
    CREATE OR REPLACE FUNCTION monitoring.log_slow_query()
    RETURNS trigger AS $$
    BEGIN
        IF NEW.execution_time > interval '1 second' THEN
            INSERT INTO monitoring.error_logs 
                (error_type, error_message, context)
            VALUES 
                ('slow_query', 
                 format('Query took %s seconds', extract(epoch from NEW.execution_time)),
                 jsonb_build_object('query', NEW.query_text, 'rows_affected', NEW.rows_affected));
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- Create trigger for slow query logging
    DROP TRIGGER IF EXISTS tr_log_slow_query ON monitoring.query_logs;
    CREATE TRIGGER tr_log_slow_query
        AFTER INSERT ON monitoring.query_logs
        FOR EACH ROW
        EXECUTE FUNCTION monitoring.log_slow_query();
EOF

    print_success "Database monitoring configured"
}

# Setup Edge Function monitoring
setup_edge_function_monitoring() {
    print_status "Setting up Edge Function monitoring..."
    
    psql "$DATABASE_URL" << 'EOF'
    -- Create Edge Function monitoring table
    CREATE TABLE IF NOT EXISTS monitoring.edge_function_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        function_name TEXT,
        execution_time INTERVAL,
        memory_used INTEGER,
        status TEXT,
        error_message TEXT,
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        request_id UUID,
        metadata JSONB
    );

    -- Create view for Edge Function performance
    CREATE OR REPLACE VIEW monitoring.edge_function_metrics AS
    SELECT
        function_name,
        COUNT(*) as total_executions,
        AVG(EXTRACT(EPOCH FROM execution_time)) as avg_execution_time,
        MAX(EXTRACT(EPOCH FROM execution_time)) as max_execution_time,
        MIN(EXTRACT(EPOCH FROM execution_time)) as min_execution_time,
        AVG(memory_used) as avg_memory_used,
        COUNT(*) FILTER (WHERE status = 'error') as error_count
    FROM monitoring.edge_function_logs
    WHERE timestamp > NOW() - INTERVAL '24 hours'
    GROUP BY function_name;
EOF

    print_success "Edge Function monitoring configured"
}

# Setup document processing monitoring
setup_processing_monitoring() {
    print_status "Setting up document processing monitoring..."
    
    psql "$DATABASE_URL" << 'EOF'
    -- Create document processing monitoring table
    CREATE TABLE IF NOT EXISTS monitoring.processing_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id UUID,
        stage TEXT,
        status TEXT,
        processing_time INTERVAL,
        error_message TEXT,
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        metadata JSONB
    );

    -- Create view for processing metrics
    CREATE OR REPLACE VIEW monitoring.processing_metrics AS
    SELECT
        stage,
        COUNT(*) as total_documents,
        AVG(EXTRACT(EPOCH FROM processing_time)) as avg_processing_time,
        COUNT(*) FILTER (WHERE status = 'error') as error_count,
        COUNT(*) FILTER (WHERE status = 'success') as success_count
    FROM monitoring.processing_logs
    WHERE timestamp > NOW() - INTERVAL '24 hours'
    GROUP BY stage;
EOF

    print_success "Document processing monitoring configured"
}

# Setup alert system
setup_alerts() {
    print_status "Setting up alert system..."
    
    psql "$DATABASE_URL" << 'EOF'
    -- Create alerts table
    CREATE TABLE IF NOT EXISTS monitoring.alerts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        alert_type TEXT,
        severity TEXT,
        message TEXT,
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        acknowledged BOOLEAN DEFAULT FALSE,
        acknowledged_by UUID,
        acknowledged_at TIMESTAMPTZ,
        metadata JSONB
    );

    -- Create alert trigger function
    CREATE OR REPLACE FUNCTION monitoring.create_alert(
        p_type TEXT,
        p_severity TEXT,
        p_message TEXT,
        p_metadata JSONB DEFAULT '{}'::JSONB
    ) RETURNS UUID AS $$
    DECLARE
        v_alert_id UUID;
    BEGIN
        INSERT INTO monitoring.alerts (alert_type, severity, message, metadata)
        VALUES (p_type, p_severity, p_message, p_metadata)
        RETURNING id INTO v_alert_id;
        
        -- Here you would typically call a notification service
        -- This is just a placeholder
        RAISE NOTICE 'Alert created: %', p_message;
        
        RETURN v_alert_id;
    END;
    $$ LANGUAGE plpgsql;
EOF

    print_success "Alert system configured"
}

# Setup monitoring views
setup_monitoring_views() {
    print_status "Setting up monitoring views..."
    
    psql "$DATABASE_URL" << 'EOF'
    -- Create system health view
    CREATE OR REPLACE VIEW monitoring.system_health AS
    SELECT
        (SELECT COUNT(*) FROM monitoring.error_logs WHERE timestamp > NOW() - INTERVAL '1 hour') as recent_errors,
        (SELECT COUNT(*) FROM monitoring.alerts WHERE NOT acknowledged) as active_alerts,
        (SELECT COUNT(*) FROM monitoring.query_logs WHERE execution_time > interval '1 second') as slow_queries,
        (SELECT COUNT(*) FROM monitoring.edge_function_logs WHERE status = 'error') as edge_function_errors;

    -- Create performance dashboard view
    CREATE OR REPLACE VIEW monitoring.performance_dashboard AS
    SELECT
        'database' as component,
        jsonb_build_object(
            'slow_queries', (SELECT COUNT(*) FROM monitoring.query_logs WHERE execution_time > interval '1 second'),
            'avg_query_time', (SELECT AVG(EXTRACT(EPOCH FROM execution_time)) FROM monitoring.query_logs)
        ) as metrics
    UNION ALL
    SELECT
        'edge_functions' as component,
        jsonb_build_object(
            'total_executions', COUNT(*),
            'error_rate', (COUNT(*) FILTER (WHERE status = 'error')::float / COUNT(*)::float)
        ) as metrics
    FROM monitoring.edge_function_logs
    UNION ALL
    SELECT
        'document_processing' as component,
        jsonb_build_object(
            'total_documents', COUNT(*),
            'success_rate', (COUNT(*) FILTER (WHERE status = 'success')::float / COUNT(*)::float)
        ) as metrics
    FROM monitoring.processing_logs;
EOF

    print_success "Monitoring views configured"
}

# Main setup flow
main() {
    print_status "Starting monitoring setup..."
    
    setup_db_monitoring
    setup_edge_function_monitoring
    setup_processing_monitoring
    setup_alerts
    setup_monitoring_views
    
    print_success "Monitoring setup completed successfully!"
    
    echo ""
    echo "🎉 Monitoring Setup Summary:"
    echo "=========================="
    echo "✅ Database monitoring configured"
    echo "✅ Edge Function monitoring enabled"
    echo "✅ Document processing tracking setup"
    echo "✅ Alert system implemented"
    echo "✅ Monitoring views created"
    echo ""
    echo "Next steps:"
    echo "1. Configure external monitoring service"
    echo "2. Set up alert notifications"
    echo "3. Create monitoring dashboards"
    echo "4. Test alert triggers"
}

main "$@" 