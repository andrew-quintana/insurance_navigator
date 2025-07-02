-- Create monitoring view
CREATE VIEW IF NOT EXISTS vw_table_stats AS
SELECT
    schemaname,
    relname,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public';

-- Create performance logging table
CREATE TABLE IF NOT EXISTS performance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    query_id TEXT,
    execution_time INTERVAL,
    rows_affected INTEGER,
    query_plan JSONB
);

-- Create alert function for long-running queries
CREATE OR REPLACE FUNCTION alert_long_running_queries()
RETURNS trigger AS $$
BEGIN
    IF NEW.execution_time > interval '30 seconds' THEN
        INSERT INTO alert_logs (alert_type, message)
        VALUES ('long_query', format('Query %s took %s', NEW.query_id, NEW.execution_time));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS tr_alert_long_queries ON performance_logs;
CREATE TRIGGER tr_alert_long_queries
AFTER INSERT ON performance_logs
FOR EACH ROW
EXECUTE FUNCTION alert_long_running_queries();
