# Local Development Setup Implementation

Your task is to set up the local development environment for the Insurance Navigator project. This involves configuring three main components: FastAPI backend, local Supabase instance, and the Next.js frontend.

## Prerequisites
- Node.js >= 18.0.0
- npm >= 8.0.0
- Python 3.x
- Supabase CLI
- Docker (for local Supabase)

## Implementation Steps

### 1. Environment Setup
1. Create a `.env` file in the project root by copying from `config/environment/env.local`:
   ```env
   # Supabase Configuration
   SUPABASE_URL=http://localhost:54321
   DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
   SUPABASE_SERVICE_ROLE_KEY=your-local-service-role-key
   SUPABASE_ANON_KEY=your-local-anon-key

   ***REMOVED*** for Development
   OPENAI_API_KEY=your-openai-key
   LLAMAPARSE_API_KEY=your-llamaparse-key

   # Feature Flags
   ENABLE_VECTOR_PROCESSING=true
   ENABLE_REGULATORY_PROCESSING=true

   # Logging
   LOG_LEVEL=DEBUG
   ```

### 2. Supabase Local Setup
1. Install Supabase CLI if not already installed:
   ```bash
   npm install -g supabase
   ```

2. Initialize and start local Supabase:
   ```bash
   supabase init
   supabase start
   ```

3. Note down the local credentials provided after starting Supabase and update your `.env` file with them.

### 3. Backend Setup
1. Install Python dependencies:
   ```bash
   pip install -r config/python/requirements.txt
   ```

2. Start the FastAPI backend:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

3. Verify the backend is running by accessing:
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### 4. Frontend Setup
1. Install frontend dependencies:
   ```bash
   cd ui
   npm install
   ```

2. Create `.env.local` in the `ui` directory:
   ```env
   # Supabase Configuration
   NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-local-anon-key

   # API Configuration
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

3. Start the frontend development server:
   ```bash
   npm run dev -- --port 3000
   ```

### 5. Verification Steps
1. Check Supabase Studio is accessible at http://localhost:54323
2. Verify FastAPI backend is running at http://localhost:8000
3. Confirm frontend is accessible at http://localhost:3000
4. Test the database connection through the FastAPI health endpoint
5. Verify Supabase auth is working through the frontend login/signup forms

## Error Handling

### Common Issues and Solutions:

1. Port 8000 already in use:
   ```bash
   lsof -ti:8000 | xargs kill -9
   # Or use alternative port:
   uvicorn main:app --port 8001
   ```

2. Database connection issues:
   - Ensure Supabase is running: `supabase status`
   - Check PostgreSQL is accessible on port 54322
   - Verify database credentials in `.env`

3. Frontend connection issues:
   - Confirm API_BASE_URL matches backend port
   - Check CORS settings in backend
   - Verify Supabase URL and anon key

## Success Criteria
- [ ] Supabase local instance running (ports 54321-54323)
- [ ] FastAPI backend running on port 8000
- [ ] Frontend accessible on port 3000
- [ ] Environment variables properly configured
- [ ] Database connection successful
- [ ] Basic auth flow working

## Notes
- Keep the local instance running for development
- Use `supabase stop` when finished
- Monitor the logs for all three components for issues
- Remember to never commit `.env` files to version control