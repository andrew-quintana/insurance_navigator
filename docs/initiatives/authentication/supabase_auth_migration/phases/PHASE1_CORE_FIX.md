# Phase 1: Core Authentication Fix

## Problem Statement

The current system has a **fundamental architectural conflict**:
- Uses Supabase auth APIs (`auth.sign_in_with_password`)
- BUT maintains a separate `public.users` table
- Creates unnecessary complexity and RLS conflicts

## Solution

**Eliminate the `public.users` table entirely** and use Supabase's built-in `auth.users` table directly.

## Phase 1 Implementation

### 1. Remove `public.users` Table

```sql
-- supabase/migrations/20250101000000_remove_public_users.sql
BEGIN;

-- Backup existing data
CREATE TABLE IF NOT EXISTS public.users_backup AS 
SELECT * FROM public.users;

-- Remove triggers and functions
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP FUNCTION IF EXISTS public.handle_updated_at();

-- Remove the table
DROP TABLE IF EXISTS public.users CASCADE;

COMMIT;
```

### 2. Update RLS Policies

```sql
-- supabase/migrations/20250101000001_update_rls_policies.sql
BEGIN;

-- Ensure all policies use auth.uid() consistently
-- Remove any policies that reference public.users

-- Update upload_pipeline policies (already correct)
-- These already use auth.uid() which is correct

-- Remove old policies that use current_setting
DROP POLICY IF EXISTS user_document_access ON upload_pipeline.documents;
DROP POLICY IF EXISTS user_upload_job_access ON upload_pipeline.upload_jobs;
DROP POLICY IF EXISTS user_chunk_access ON upload_pipeline.document_chunks;

-- The existing policies in 20250814000000_init_upload_pipeline.sql are correct:
-- They already use auth.uid() which is what we want

COMMIT;
```

### 3. Simplify Authentication Service

```python
# db/services/supabase_auth_service.py
class SupabaseAuthService:
    """Simplified authentication service using Supabase auth.users directly"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def authenticate_user(self, email: str, password: str):
        """Authenticate user using Supabase auth"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not response.user or not response.session:
                return None
                
            return {
                "user": response.user,
                "session": response.session,
                "success": True
            }
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    async def create_user(self, email: str, password: str, metadata: dict = None):
        """Create user using Supabase auth"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata or {}
                }
            })
            
            if not response.user:
                return None
                
            return {
                "user": response.user,
                "session": response.session,
                "success": True
            }
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            return None
    
    def validate_token(self, token: str):
        """Validate JWT token using Supabase"""
        try:
            response = self.supabase.auth.get_user(token)
            return response.user if response.user else None
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None
```

### 4. Update Auth Adapter

```python
# db/services/auth_adapter.py
class SupabaseAuthBackend(AuthBackend):
    """Simplified Supabase auth backend"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.auth_service = SupabaseAuthService(supabase_client)
    
    async def create_user(self, email: str, password: str, name: str = None):
        metadata = {"name": name} if name else {}
        return await self.auth_service.create_user(email, password, metadata)
    
    async def authenticate_user(self, email: str, password: str):
        return await self.auth_service.authenticate_user(email, password)
    
    def validate_token(self, token: str):
        return self.auth_service.validate_token(token)
    
    async def get_user_info(self, user_id: str):
        # Get user from auth.users using admin API
        try:
            response = self.supabase.auth.admin.get_user_by_id(user_id)
            return response if response else None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
```

### 5. Update API Endpoints

```python
# main.py - Update get_current_user function
async def get_current_user(request: Request) -> Dict[str, Any]:
    """Extract and validate user from Supabase session"""
    auth_header = request.headers.get("authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Use Supabase auth directly
        user_data = auth_adapter.validate_token(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return {
            "id": user_data.id,
            "email": user_data.email,
            "metadata": user_data.user_metadata or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

### 6. Update Frontend

```typescript
// ui/lib/supabase-client.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Authentication functions
export const signIn = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  return { data, error }
}

export const signUp = async (email: string, password: string, metadata?: any) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: metadata || {}
    }
  })
  return { data, error }
}

export const signOut = async () => {
  const { error } = await supabase.auth.signOut()
  return { error }
}
```

## Key Benefits

1. **Simplified Architecture**: Single source of truth for user data
2. **Native RLS Integration**: `auth.uid()` works seamlessly
3. **Reduced Maintenance**: No custom triggers or synchronization
4. **Better Security**: Leverages Supabase's built-in security
5. **Easier Development**: Standard Supabase patterns

## Migration Steps

1. **Backup Data**: Export user data from `public.users`
2. **Apply Migrations**: Remove `public.users` table
3. **Update Code**: Simplify authentication service
4. **Test System**: Verify authentication and RLS work
5. **Deploy**: Roll out changes

## Testing

```python
# tests/test_phase1_auth.py
import pytest
from db.services.supabase_auth_service import SupabaseAuthService

@pytest.mark.asyncio
async def test_authenticate_user():
    auth_service = SupabaseAuthService(supabase_client)
    
    # Test authentication
    result = await auth_service.authenticate_user("test@example.com", "password")
    assert result is not None
    assert result["success"] is True
    assert result["user"].email == "test@example.com"

@pytest.mark.asyncio
async def test_create_user():
    auth_service = SupabaseAuthService(supabase_client)
    
    # Test user creation
    result = await auth_service.create_user("new@example.com", "password", {"name": "Test User"})
    assert result is not None
    assert result["success"] is True
    assert result["user"].email == "new@example.com"
```

## Success Criteria

- [ ] `public.users` table removed
- [ ] Authentication works with `auth.users` only
- [ ] RLS policies use `auth.uid()` consistently
- [ ] No data loss during migration
- [ ] All tests passing
- [ ] System performance maintained

## Rollback Plan

If issues occur:
1. Restore `public.users` table from backup
2. Revert authentication service changes
3. Restore original RLS policies
4. Test system functionality

This Phase 1 implementation eliminates the architectural confusion and creates a clean, maintainable authentication system using Supabase's built-in features.

