# Edge Functions Tests

## Setup

1. Create a `.env.test` file in the `supabase/functions` directory with the following variables:

```bash
SUPABASE_URL=http://localhost:54321
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
LLAMA_CLOUD_API_KEY=<your-test-api-key>
```

You can get the service role key by running:
```bash
supabase status
```

## Running Tests

Run the tests using:

```bash
deno test --allow-env --allow-net --allow-read
```

## Test Structure

The tests are organized as follows:

1. **Document Processing Tests** (`document_processing_test.ts`)
   - Tests document upload
   - Tests document parsing
   - Tests document chunking
   - Tests vector storage
   - Tests cleanup

2. **Authentication Tests** (Coming soon)
   - Will test service role authentication
   - Will test user authentication

## Debugging

If you encounter any issues:

1. Ensure Supabase is running locally:
   ```bash
   supabase start
   ```

2. Verify your environment variables are set correctly

3. Check that the RLS policies are properly configured:
   ```bash
   supabase db reset
   ```

## Common Issues

1. **RLS Policy Violations**
   - Make sure you're using the service role client for operations that need elevated permissions
   - Verify the RLS policies are correctly applied after running migrations

2. **Authentication Issues**
   - Ensure your service role key is correct
   - Check that the Supabase URL is accessible

3. **TypeScript/Deno Issues**
   - Make sure you're using the correct import paths as configured in `deno.json`
   - Run `deno cache --reload` if you're seeing stale type errors 