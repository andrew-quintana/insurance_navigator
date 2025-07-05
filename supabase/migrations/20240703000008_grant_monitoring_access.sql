-- Grant access to monitoring schema for PostgREST
ALTER ROLE authenticator SET search_path TO public, storage, graphql_public, monitoring;

-- Grant usage on monitoring schema to authenticator
GRANT USAGE ON SCHEMA monitoring TO authenticator;
GRANT USAGE ON SCHEMA monitoring TO anon;
GRANT USAGE ON SCHEMA monitoring TO authenticated;

-- Grant select access to edge function logs
GRANT SELECT ON monitoring.edge_function_logs TO authenticator;
GRANT SELECT ON monitoring.edge_function_logs TO anon;
GRANT SELECT ON monitoring.edge_function_logs TO authenticated;

-- Grant execute on monitoring functions
GRANT EXECUTE ON FUNCTION monitoring.log_edge_function TO authenticator;
GRANT EXECUTE ON FUNCTION monitoring.log_edge_function TO anon;
GRANT EXECUTE ON FUNCTION monitoring.log_edge_function TO authenticated; 