# Database Infrastructure

This directory contains the database infrastructure for the Insurance Navigator system. The infrastructure is designed to handle policy management, access control, and secure storage of sensitive information.

## Directory Structure

```
db/
├── migrations/     # SQL migration files
├── models/        # Database models and types
└── services/      # Database service implementations
```

## Core Tables

### encryption_keys
Stores encryption keys used for securing sensitive policy data.

### roles
Defines system roles for access control.

### user_roles
Maps users to their assigned roles.

### policy_records
Stores policy information with encrypted sensitive data.

### user_policy_links
Links users to policies they have access to.

### policy_access_policies
Defines access control policies for different roles.

### policy_access_logs
Logs all policy access attempts and actions.

### agent_policy_context
Stores encrypted context for agent sessions.

## Security Features

1. **Row Level Security (RLS)**
   - Implemented on policy_records, user_policy_links, and policy_access_logs
   - Ensures users can only access their authorized data

2. **Encryption**
   - Sensitive data is encrypted using keys from encryption_keys table
   - Supports key rotation and versioning

3. **Access Control**
   - Role-based access control through user_roles
   - Granular permissions through policy_access_policies

## Migration Process

1. Apply migrations in order:
   ```bash
   psql -f db/migrations/001_initial_schema.sql
   ```

2. To rollback:
   ```bash
   psql -f db/migrations/001_initial_schema_rollback.sql
   ```

## Best Practices

1. Always use parameterized queries to prevent SQL injection
2. Follow the principle of least privilege in RLS policies
3. Log all sensitive data access through policy_access_logs
4. Use encryption for all sensitive data
5. Maintain proper key rotation schedules

## Development Guidelines

1. Test all migrations in a development environment first
2. Include rollback scripts for all migrations
3. Document any schema changes in this README
4. Follow naming conventions for tables and indexes
5. Add appropriate indexes for common query patterns

## Monitoring and Maintenance

1. Regularly review access logs for suspicious activity
2. Monitor encryption key rotation schedules
3. Review and update RLS policies as needed
4. Maintain and update indexes based on query patterns
5. Regular backup of encryption keys and sensitive data 