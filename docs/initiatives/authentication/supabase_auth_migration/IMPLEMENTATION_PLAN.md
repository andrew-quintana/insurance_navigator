# Supabase Authentication Implementation Plan

## Overview

This plan migrates the Insurance Navigator from a hybrid authentication system (Supabase auth + custom `public.users` table) to using Supabase's built-in `auth.users` table directly.

## Current State Analysis

### What's Working
- Supabase auth APIs are being used (`sign_in_with_password`, `sign_up`)
- Upload pipeline RLS policies use `auth.uid()` correctly
- Basic authentication flow works

### What's Broken
- `public.users` table duplicates `auth.users` data
- RLS policies are inconsistent (some use `auth.uid()`, others use manual context)
- Complex trigger-based synchronization between tables
- Unnecessary maintenance overhead

## Implementation Strategy

### Phase 1: Database Cleanup (Week 1)

#### 1.1 Remove `public.users` Table
```sql
-- Backup existing data
CREATE TABLE public.users_backup AS SELECT * FROM public.users;

-- Remove triggers and policies
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP TABLE IF EXISTS public.users CASCADE;
```

#### 1.2 Update RLS Policies
```sql
-- Ensure all policies use auth.uid() consistently
-- Remove any policies that reference public.users
-- Update upload_pipeline policies to use auth.uid() only
```

#### 1.3 Migrate User Data
```sql
-- Move custom user data to auth.users.user_metadata
-- Update any foreign key references
-- Verify data integrity
```

### Phase 2: Authentication Service Update (Week 2)

#### 2.1 Simplify Auth Service
```python
class SupabaseAuthService:
    def authenticate_user(self, email, password):
        # Use Supabase auth directly
        response = self.supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response.user, response.session
    
    def create_user(self, email, password, metadata=None):
        # Use Supabase auth directly
        response = self.supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": metadata or {}}
        })
        return response.user, response.session
```

#### 2.2 Remove Custom User Management
- Delete `public.users` related code
- Remove trigger-based synchronization
- Simplify user data access

#### 2.3 Update API Endpoints
```python
@app.get("/documents")
async def get_documents(current_user = Depends(get_current_user)):
    # RLS automatically filters by auth.uid()
    return supabase.table("upload_pipeline.documents").select("*").execute()
```

### Phase 3: Frontend Integration (Week 3)

#### 3.1 Update Supabase Client
```typescript
// Use Supabase auth directly
const { data, error } = await supabase.auth.signInWithPassword({
  email: email,
  password: password
});
```

#### 3.2 Remove Custom JWT Handling
- Use Supabase session management
- Remove custom token validation
- Update authentication state management

#### 3.3 Update UI Components
- Use `auth.users` data structure
- Update user profile components
- Update authentication flows

### Phase 4: Testing and Validation (Week 4)

#### 4.1 Authentication Testing
- Test user registration
- Test user login
- Test session management
- Test logout

#### 4.2 RLS Testing
- Test data access permissions
- Test user isolation
- Test admin access
- Test service role access

#### 4.3 Integration Testing
- Test upload pipeline
- Test document access
- Test user management
- Test error handling

### Phase 5: Production Deployment (Week 5)

#### 5.1 Staging Deployment
- Deploy to staging environment
- Run full test suite
- Validate performance
- Test user workflows

#### 5.2 Production Migration
- Deploy to production
- Monitor system health
- Validate user access
- Monitor error rates

## Key Files to Update

### Database
- `supabase/migrations/` - Remove `public.users` table
- `sql/rls_policies.sql` - Update RLS policies
- `supabase/config.toml` - Configure auth settings

### Backend
- `db/services/auth_service.py` - Simplify to use Supabase auth
- `db/services/user_service.py` - Remove or simplify
- `db/services/auth_adapter.py` - Update for Supabase auth
- `main.py` - Update authentication middleware

### Frontend
- `ui/lib/supabase-client.ts` - Update client configuration
- `ui/components/auth/` - Update auth components
- `ui/components/SessionManager.tsx` - Update session management

## Migration Scripts

### 1. Data Migration Script
```python
# Export user data from public.users
# Import to auth.users.user_metadata
# Verify data integrity
```

### 2. RLS Policy Update Script
```sql
-- Update all policies to use auth.uid()
-- Remove public.users references
-- Test policy functionality
```

### 3. Code Update Script
```python
# Update authentication service
# Remove public.users dependencies
# Update API endpoints
```

## Testing Strategy

### Unit Tests
- Authentication service functions
- RLS policy validation
- User data access
- Error handling

### Integration Tests
- Complete authentication flow
- Data access with RLS
- User management operations
- API endpoint functionality

### End-to-End Tests
- User registration and login
- Document upload and access
- User profile management
- Admin operations

## Rollback Plan

### Database Rollback
- Restore `public.users` table from backup
- Restore original RLS policies
- Restore triggers and functions

### Code Rollback
- Revert to previous authentication service
- Restore custom user management
- Restore original API endpoints

### Data Rollback
- Restore user data from backup
- Verify data integrity
- Test system functionality

## Success Criteria

### Technical Criteria
- [ ] `public.users` table removed
- [ ] All RLS policies use `auth.uid()`
- [ ] Authentication service simplified
- [ ] No data loss during migration
- [ ] All tests passing

### Functional Criteria
- [ ] Users can register and login
- [ ] Users can access their data
- [ ] RLS policies work correctly
- [ ] Admin functions work
- [ ] System performance maintained

### Business Criteria
- [ ] No user disruption
- [ ] System stability maintained
- [ ] Security improved
- [ ] Maintenance reduced
- [ ] Development velocity increased

## Timeline

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | Database Cleanup | Remove `public.users`, update RLS policies |
| 2 | Auth Service Update | Simplify authentication, update APIs |
| 3 | Frontend Integration | Update UI components, remove custom JWT |
| 4 | Testing | Comprehensive testing and validation |
| 5 | Production | Deploy to production, monitor and support |

## Risk Mitigation

### Technical Risks
- **Data Loss**: Comprehensive backups and testing
- **RLS Misconfiguration**: Thorough policy testing
- **Authentication Failures**: Gradual rollout and monitoring

### Business Risks
- **User Disruption**: Clear communication and support
- **System Downtime**: Blue-green deployment
- **Performance Issues**: Load testing and optimization

## Conclusion

This plan eliminates the architectural confusion by embracing Supabase's built-in authentication system. The result will be a simpler, more maintainable, and more secure system that follows Supabase best practices.

