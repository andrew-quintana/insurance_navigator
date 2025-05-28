# Row Level Security (RLS) Implementation Guide

## Overview

This document describes the complete Row Level Security (RLS) implementation for the Insurance Navigator system. RLS ensures that users can only access data they are authorized to see, providing data isolation and security at the database level.

## RLS Status Summary

✅ **RLS Enabled on All Tables**  
✅ **Comprehensive Policies Implemented**  
✅ **Helper Functions Available**  
✅ **Performance Optimized**  
✅ **Test Suite Available**

## Tables with RLS Enabled

| Table | RLS Status | Policies | Purpose |
|-------|------------|----------|---------|
| `users` | ✅ Enabled | 3 policies | User self-access and admin management |
| `policy_records` | ✅ Enabled | 3 policies | Policy access based on user links |
| `user_policy_links` | ✅ Enabled | 4 policies | User-policy relationship management |
| `policy_access_logs` | ✅ Enabled | 3 policies | Access audit trail |
| `agent_policy_context` | ✅ Enabled | 3 policies | Agent session context |
| `roles` | ✅ Enabled | 2 policies | Role management |
| `user_roles` | ✅ Enabled | 2 policies | User role assignments |
| `encryption_keys` | ✅ Enabled | 1 policy | Admin-only encryption key access |
| `policy_access_policies` | ✅ Enabled | 1 policy | Admin-only access policy management |
| `regulatory_documents` | ✅ Enabled | 3 policies | Regulatory content access |

## Policy Details

### Users Table Policies

#### `users_self_select`
- **Type**: SELECT
- **Purpose**: Allow users to view their own user record
- **Logic**: `id = auth.uid()`

#### `users_self_update`
- **Type**: UPDATE
- **Purpose**: Allow users to update their own profile
- **Logic**: `id = auth.uid()`

#### `users_admin_access`
- **Type**: ALL (SELECT, INSERT, UPDATE, DELETE)
- **Purpose**: Allow admin users to manage all user accounts
- **Logic**: User has 'admin' role

### Policy Records Table Policies

#### `policy_records_user_access`
- **Type**: SELECT
- **Purpose**: Allow users to view policies they are linked to with verified relationships
- **Logic**: User has verified link to policy in `user_policy_links`

#### `policy_records_admin_access`
- **Type**: ALL
- **Purpose**: Allow admin users full access to all policy records
- **Logic**: User has 'admin' role

#### `policy_records_user_insert`
- **Type**: INSERT
- **Purpose**: Allow users to create policy records for themselves
- **Logic**: User has link to policy with role 'subscriber' or 'self'

### User Policy Links Table Policies

#### `user_policy_links_user_access`
- **Type**: SELECT
- **Purpose**: Allow users to see their own policy links
- **Logic**: `user_id = auth.uid()`

#### `user_policy_links_user_insert`
- **Type**: INSERT
- **Purpose**: Allow users to create their own policy links
- **Logic**: `user_id = auth.uid()`

#### `user_policy_links_user_update`
- **Type**: UPDATE
- **Purpose**: Allow users to update their own policy links
- **Logic**: `user_id = auth.uid()`

#### `user_policy_links_admin_access`
- **Type**: ALL
- **Purpose**: Allow admin users to manage all policy links
- **Logic**: User has 'admin' role

### Policy Access Logs Table Policies

#### `policy_access_logs_user_access`
- **Type**: SELECT
- **Purpose**: Allow users to see audit logs for their own activities
- **Logic**: `user_id = auth.uid()`

#### `policy_access_logs_admin_access`
- **Type**: ALL
- **Purpose**: Allow admin users to access all audit logs
- **Logic**: User has 'admin' role

#### `policy_access_logs_system_insert`
- **Type**: INSERT
- **Purpose**: Allow system processes to create audit log entries
- **Logic**: Always true (system-level access)

### Agent Policy Context Table Policies

#### `agent_policy_context_user_access`
- **Type**: SELECT
- **Purpose**: Allow users to see their own agent context
- **Logic**: `user_id = auth.uid()`

#### `agent_policy_context_admin_access`
- **Type**: ALL
- **Purpose**: Allow admin users to manage all agent context
- **Logic**: User has 'admin' role

#### `agent_policy_context_system_insert`
- **Type**: INSERT
- **Purpose**: Allow system to create agent context records
- **Logic**: Always true (system-level access)

### Roles Table Policies

#### `roles_admin_access`
- **Type**: ALL
- **Purpose**: Allow admin users to manage system roles
- **Logic**: User has 'admin' role

#### `roles_read_access`
- **Type**: SELECT
- **Purpose**: Allow all authenticated users to read roles for UI purposes
- **Logic**: `auth.uid() IS NOT NULL`

### User Roles Table Policies

#### `user_roles_self_access`
- **Type**: SELECT
- **Purpose**: Allow users to see their own role assignments
- **Logic**: `user_id = auth.uid()`

#### `user_roles_admin_access`
- **Type**: ALL
- **Purpose**: Allow admin users to manage all role assignments
- **Logic**: User has 'admin' role

### Encryption Keys Table Policies

#### `encryption_keys_admin_only`
- **Type**: ALL
- **Purpose**: Restrict encryption key access to admin users only
- **Logic**: User has 'admin' role

### Policy Access Policies Table Policies

#### `policy_access_policies_admin_only`
- **Type**: ALL
- **Purpose**: Restrict access policy management to admin users only
- **Logic**: User has 'admin' role

### Regulatory Documents Table Policies

#### `regulatory_docs_read`
- **Type**: SELECT
- **Purpose**: Allow admin and regulatory agent users to read regulatory documents
- **Logic**: User has 'admin' or 'regulatory_agent' role

#### `regulatory_docs_write`
- **Type**: INSERT
- **Purpose**: Allow admin users to create regulatory documents
- **Logic**: User has 'admin' role

#### `regulatory_docs_update`
- **Type**: UPDATE
- **Purpose**: Allow admin users to update regulatory documents
- **Logic**: User has 'admin' role

## Helper Functions

### `auth.is_admin()`
- **Returns**: boolean
- **Purpose**: Check if current user has admin role
- **Usage**: `SELECT auth.is_admin()`

### `auth.has_role(role_name text)`
- **Returns**: boolean
- **Purpose**: Check if current user has specific role
- **Usage**: `SELECT auth.has_role('regulatory_agent')`

### `auth.can_access_policy(policy_uuid uuid)`
- **Returns**: boolean
- **Purpose**: Check if current user can access specific policy
- **Usage**: `SELECT auth.can_access_policy('123e4567-e89b-12d3-a456-426614174000')`

## Performance Considerations

### Indexes Created for RLS

1. **`idx_user_roles_user_id_role_name`**
   - Table: `user_roles`
   - Columns: `user_id` (includes `role_id`)
   - Purpose: Optimize role checking in RLS policies

2. **`idx_roles_name`**
   - Table: `roles`
   - Columns: `name`
   - Purpose: Fast role name lookups

3. **`idx_user_policy_links_user_policy`**
   - Table: `user_policy_links`
   - Columns: `user_id, policy_id`
   - Condition: `WHERE relationship_verified = true`
   - Purpose: Optimize policy access checks

### Query Optimization Tips

1. **Avoid N+1 Queries**: Use joins instead of subqueries where possible
2. **Index Usage**: Ensure RLS conditions use indexed columns
3. **Policy Simplicity**: Keep RLS conditions as simple as possible
4. **Caching**: Consider caching role information at application level

## Security Best Practices

### 1. Principle of Least Privilege
- Users can only access their own data by default
- Admin access is explicitly granted through role checks
- System operations have minimal required permissions

### 2. Defense in Depth
- RLS policies work alongside application-level security
- Multiple policy types (SELECT, INSERT, UPDATE, DELETE) for granular control
- Helper functions encapsulate complex logic

### 3. Audit Trail
- All data access is logged through `policy_access_logs`
- RLS policies don't prevent audit logging
- Admin actions are clearly identified

### 4. Data Isolation
- User data is completely isolated between users
- Policy records are only accessible through verified links
- Admin access is clearly separated and audited

## Testing and Validation

### Automated Test Suite
Run the RLS test suite to verify all policies:

```bash
cd db/scripts
python test_rls_policies.py --database-url $DATABASE_URL
```

### Manual Testing Commands

#### Test User Isolation
```sql
-- Set user context
SELECT set_config('rls.current_user_id', 'user-uuid-here', false);

-- Try to access other user's data (should return 0 rows)
SELECT COUNT(*) FROM users WHERE id != 'user-uuid-here';
```

#### Test Admin Access
```sql
-- Set admin user context
SELECT set_config('rls.current_user_id', 'admin-uuid-here', false);

-- Should return all users
SELECT COUNT(*) FROM users;
```

#### Test Policy Access
```sql
-- Set user context
SELECT set_config('rls.current_user_id', 'user-uuid-here', false);

-- Should only return policies user has access to
SELECT COUNT(*) FROM policy_records;
```

## Troubleshooting

### Common Issues

#### 1. RLS Prevents Expected Access
**Symptoms**: Queries return no results unexpectedly
**Solutions**:
- Check if user has correct role assignments
- Verify relationship_verified flag in user_policy_links
- Ensure auth.uid() returns expected user ID

#### 2. Performance Issues
**Symptoms**: Slow query performance with RLS enabled
**Solutions**:
- Check index usage with EXPLAIN
- Verify RLS conditions use indexed columns
- Consider simplifying complex RLS policies

#### 3. Helper Functions Not Working
**Symptoms**: auth.is_admin() returns unexpected results
**Solutions**:
- Verify user has role assignments in user_roles table
- Check that roles table has correct role names
- Ensure functions have proper SECURITY DEFINER

### Debugging Commands

#### Check RLS Status
```sql
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;
```

#### List All Policies
```sql
SELECT schemaname, tablename, policyname, cmd, permissive
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

#### Check User Roles
```sql
SELECT u.email, r.name as role_name
FROM users u
JOIN user_roles ur ON ur.user_id = u.id
JOIN roles r ON r.id = ur.role_id
WHERE u.id = 'user-uuid-here';
```

## Migration and Deployment

### Applying RLS Migration
```bash
# Apply the RLS migration
psql -f db/migrations/005_enable_rls_policies.sql

# Verify policies were created
psql -c "SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public';"
```

### Rollback if Needed
```bash
# Only use for debugging - removes security features
psql -f db/migrations/005_enable_rls_policies_rollback.sql
```

### Production Deployment
1. Test in staging environment first
2. Apply migration during maintenance window
3. Run test suite to verify functionality
4. Monitor performance after deployment
5. Keep rollback plan ready (but avoid using in production)

## Compliance and Auditing

### HIPAA Compliance
- RLS ensures patient data isolation
- Access logs track all data access
- Admin access is controlled and audited
- Encryption keys are protected

### Audit Requirements
- All policy access is logged in policy_access_logs
- User actions are tracked with actor_type and actor_id
- Purpose tracking for compliance reporting
- Soft deletion tracking available

### Regular Audits
1. Review access patterns monthly
2. Monitor for unusual access activity
3. Verify role assignments quarterly
4. Test RLS policies during security reviews

## Future Enhancements

### Planned Improvements
1. **Time-based Access**: Policies based on business hours
2. **IP-based Restrictions**: Location-aware access controls
3. **Data Classification**: Different policies for different data sensitivity levels
4. **Hierarchical Roles**: Support for role inheritance

### Monitoring Additions
1. **Real-time Alerts**: Unusual access pattern detection
2. **Performance Metrics**: RLS query performance tracking
3. **Compliance Dashboard**: Automated compliance reporting
4. **Access Analytics**: User behavior analysis

## Contact and Support

For questions about RLS implementation:
- Review this documentation
- Run the test suite for validation
- Check the troubleshooting section
- Consult the security team for policy changes

Remember: RLS is a critical security feature. Any changes should be thoroughly tested and reviewed before deployment. 