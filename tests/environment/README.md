# Environment Tests

These tests verify that your environment files (`.env.development`, `.env.staging`, `.env.production`) are correctly configured for each environment, with special attention to Supabase edge function compatibility.

## Running the Tests

To run tests for all environments:
```bash
pytest tests/environment
```

To test a specific environment:
```bash
pytest tests/environment -m development
pytest tests/environment -m staging
pytest tests/environment -m production
```

## What's Being Tested

### Supabase URL Configuration
- Project URLs follow correct format
- API keys are valid JWT tokens
- Local development uses correct localhost URLs
- Hosted environments use correct Supabase domains

### Database Connections
- Direct connection URLs (port 5432 for hosted, 54322 for local)
- Pooler URLs (port 6543 for hosted, 54321 for local)
- Session pooler URLs
- Correct credential formats
- SSL configuration (required for production)

### Edge Function Compatibility
- Pooler configuration matches Supabase requirements
- JWT secrets meet length requirements
- Service role keys are present and valid
- Correct port numbers for edge function database access
- Proper domain configuration for pooler access

### Environment-Specific Checks

#### Development Environment
- Uses localhost (127.0.0.1)
- Correct local ports (54321 for pooler, 54322 for direct)
- Default development credentials
- Local JWT configuration

#### Staging Environment
- Uses correct Supabase project ID (dfgzeastcxnoqshgyotp)
- Proper hosted ports (6543 for pooler, 5432 for direct)
- Staging credentials
- Edge function compatibility

#### Production Environment
- Enhanced security requirements
- Password complexity rules
- SSL requirement
- No development/staging values
- Full edge function support

## Connection Types

The tests verify three types of database connections:

1. **Direct Connection** (`DATABASE_URL`)
   - Development: `postgresql://postgres:postgres@127.0.0.1:54322/postgres`
   - Hosted: `postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres`

2. **Transaction Pooler** (`SUPABASE_POOLER_URL`)
   - Development: `postgresql://postgres:postgres@127.0.0.1:54321/postgres`
   - Hosted: `postgresql://postgres.[project-id]:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres`

3. **Session Pooler** (`SUPABASE_SESSION_POOLER_URL`)
   - Development: `postgresql://postgres:postgres@127.0.0.1:54321/postgres`
   - Hosted: `postgresql://postgres.[project-id]:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres`

## Edge Function Requirements

For edge functions to work properly, your environment must have:
- Correct pooler configuration (port 6543 for hosted environments)
- Valid JWT secret (32+ characters)
- Service role key for authentication
- Proper database connection strings

## Adding New Tests

To add new environment variable checks:
1. Add checks to the relevant verification function
2. Add environment-specific assertions in the test functions
3. Update this README to document the new requirements

## Troubleshooting

If tests fail, check:
1. Port numbers match the environment (54321/54322 for local, 5432/6543 for hosted)
2. Database URLs use the correct format for the environment
3. JWT tokens are properly formatted
4. SSL is enabled for production connections
5. Pooler URLs match the Supabase edge function requirements

## Required Environment Variables

Each environment must define:
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `JWT_SECRET`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`
- `SUPABASE_POOLER_URL`
- `SUPABASE_SESSION_POOLER_URL` 