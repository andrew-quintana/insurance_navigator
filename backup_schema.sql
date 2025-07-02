-- Create backup tables
CREATE TABLE IF NOT EXISTS users_backup AS SELECT * FROM users;
CREATE TABLE IF NOT EXISTS documents_backup AS SELECT * FROM documents;

-- Create backup function
CREATE OR REPLACE FUNCTION create_table_backup(table_name text)
RETURNS void AS $$
DECLARE
    backup_table text;
    timestamp_str text;
BEGIN
    timestamp_str := to_char(now(), 'YYYYMMDD_HH24MISS');
    backup_table := table_name || '_backup_' || timestamp_str;
    
    EXECUTE format('CREATE TABLE %I AS SELECT * FROM %I', backup_table, table_name);
    
    RAISE NOTICE 'Created backup table: %', backup_table;
END;
$$ LANGUAGE plpgsql;
