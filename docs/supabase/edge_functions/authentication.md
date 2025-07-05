# Edge Functions Authentication & Interactions

## Overview

This document outlines how edge functions in the Insurance Navigator system handle authentication and interact with other system components. It serves as a guide for developers working with edge functions and the authentication system.

## Authentication System

### Core Components

1. **JWT-Based Authentication**
   - Uses Supabase JWT tokens for authentication
   - Two primary token types:
     - Service Role JWT: For system-level operations
     - User JWT: For authenticated user operations
   - JWT secrets managed via environment variables:
     - `SUPABASE_JWT_SECRET` (primary)
     - `JWT_SECRET` (fallback)

2. **Authentication Headers**
   ```typescript
   {
     'Authorization': 'Bearer <jwt_token>',
     'apikey': '<supabase_anon_key_or_service_role_key>'
   }
   ```

### Token Generation & Validation

1. **Service Role Tokens**
   ```typescript
   const serviceRoleJWT = await createServiceRoleJWT();
   // Valid for 1 hour, has service_role permissions
   ```

2. **User Tokens**
   ```typescript
   const userJWT = await createUserJWT(userId);
   // Valid for 1 hour, has authenticated user permissions
   ```

3. **Token Validation**
   ```typescript
   const payload = await verifyJWT(token);
   // Verifies signature and expiration
   ```

## Developer Controls

### Environment Configuration

1. **Required Variables**
   ```env
   SUPABASE_URL=your_project_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   SUPABASE_JWT_SECRET=your_jwt_secret
   ```

2. **Optional Features**
   ```env
   ENABLE_VECTOR_PROCESSING=true
   ENABLE_REGULATORY_PROCESSING=true
   ```

### Authentication Modes

1. **Anonymous Access**
   - Uses Supabase anon key
   - Limited to public resources
   - Example:
     ```typescript
     createClient(supabaseUrl, anonKey)
     ```

2. **Authenticated User**
   - Requires valid user JWT
   - Access controlled by RLS policies
   - Example:
     ```typescript
     createClient(supabaseUrl, anonKey, {
       global: {
         headers: { Authorization: `Bearer ${userJWT}` }
       }
     })
     ```

3. **Service Role**
   - Full database access
   - Bypasses RLS
   - Example:
     ```typescript
     createClient(supabaseUrl, serviceRoleKey, {
       global: {
         headers: { Authorization: `Bearer ${serviceRoleJWT}` }
       }
     })
     ```

## Edge Function Implementation

### Basic Structure

```typescript
serve(async (req) => {
  // 1. Extract JWT from request
  const authHeader = req.headers.get('Authorization');
  const token = authHeader?.replace('Bearer ', '');

  // 2. Create Supabase client with auth context
  const supabaseClient = createClient(
    edgeConfig.supabaseUrl,
    edgeConfig.supabaseKey,
    {
      global: {
        headers: { Authorization: authHeader }
      }
    }
  );

  // 3. Your function logic here
  // ...
});
```

### Security Best Practices

1. **Token Validation**
   - Always verify tokens before processing
   - Check token expiration
   - Validate permissions

2. **Error Handling**
   ```typescript
   if (!token) {
     return new Response(
       JSON.stringify({ error: 'Unauthorized' }),
       { status: 401 }
     );
   }
   ```

3. **CORS Headers**
   ```typescript
   const corsHeaders = {
     'Access-Control-Allow-Origin': '*',
     'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
     'Access-Control-Allow-Headers': 'Authorization, X-Client-Info, Content-Type'
   };
   ```

## Testing

### Test Environment Setup

1. **Configuration**
   ```env
   # .env.test
   SUPABASE_URL=http://127.0.0.1:54321
   SUPABASE_SERVICE_ROLE_KEY=test-key
   SUPABASE_JWT_SECRET=test-secret
   TEST_USER_ID=test-user-id
   ```

2. **Test Helpers**
   ```typescript
   // Create test user with JWT
   async function setupTestUser(supabase: SupabaseClient) {
     const testUser = {
       id: "test-user-id",
       email: "test@example.com"
     };
     await supabase.auth.admin.createUser(testUser);
     return createUserJWT(testUser.id);
   }
   ```

### Test Cases

1. **Authentication Tests**
   ```typescript
   // Test unauthorized access
   const response = await fetch(endpoint, {
     headers: { 'Content-Type': 'application/json' }
   });
   assertEquals(response.status, 401);

   // Test authorized access
   const response = await fetch(endpoint, {
     headers: {
       'Authorization': `Bearer ${testJWT}`,
       'Content-Type': 'application/json'
     }
   });
   assertEquals(response.status, 200);
   ```

## Troubleshooting

### Common Issues

1. **Invalid JWT**
   - Check JWT secret in environment
   - Verify token expiration
   - Ensure correct token format

2. **Permission Denied**
   - Verify RLS policies
   - Check user role in JWT
   - Confirm service role configuration

3. **CORS Issues**
   - Include proper CORS headers
   - Check allowed origins
   - Verify HTTP methods

### Debugging Tools

1. **JWT Debugging**
   ```typescript
   console.log('Token payload:', await verifyJWT(token));
   ```

2. **Request Logging**
   ```typescript
   console.log('Auth header:', req.headers.get('Authorization'));
   console.log('Client info:', req.headers.get('X-Client-Info'));
   ```

## References

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [JWT Documentation](https://jwt.io/)
- [Edge Functions Documentation](https://supabase.com/docs/guides/functions) 