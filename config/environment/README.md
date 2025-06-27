# Environment Configuration

This directory contains environment configuration templates for different deployment environments:

## Files

- `env.local` - Local development environment configuration
- `env.test` - Test environment configuration
- `env.production` - Production environment configuration

## Usage

1. Copy the appropriate environment file to your project root as `.env`:
   ```bash
   # For local development
   cp config/environment/env.local .env

   # For testing
   cp config/environment/env.test .env

   # For production
   cp config/environment/env.production .env
   ```

2. Replace placeholder values with actual credentials
3. Never commit `.env` files to version control
4. Keep the templates updated when adding new environment variables

## Environment Variables

### Database Configuration
- `SUPABASE_URL` - Supabase project URL
- `DATABASE_URL` - Direct PostgreSQL connection string
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `SUPABASE_ANON_KEY` - Supabase anonymous key

##***REMOVED***
- `OPENAI_API_KEY` - OpenAI API key
- `LLAMAPARSE_API_KEY` - LlamaParse API key

### Feature Flags
- `ENABLE_VECTOR_PROCESSING` - Enable/disable vector processing
- `ENABLE_REGULATORY_PROCESSING` - Enable/disable regulatory processing

### Security
- `NODE_ENV` - Node environment (development/production)
- `ENABLE_RATE_LIMITING` - Enable/disable rate limiting
- `MAX_REQUESTS_PER_MINUTE` - Rate limiting threshold

### Logging
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARN/ERROR)

## Environment-Specific Settings

### Local Development
- Uses local Supabase instance (ports 54321/54322)
- Debug logging enabled
- No rate limiting

### Test Environment
- Uses separate test database
- Mock external services
- Debug logging enabled

### Production
- Uses production Supabase instance
- Rate limiting enabled
- INFO level logging
- Enhanced security settings 