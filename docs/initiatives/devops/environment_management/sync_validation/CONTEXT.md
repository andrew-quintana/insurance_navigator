# Environment Sync Validation - Context Document

**Created:** 2025-09-23 15:00:02 PDT

## Project Overview

The Insurance Navigator is a comprehensive AI-powered application with a Python/FastAPI backend, React frontend, and Supabase database integration. The project includes:

### Core Architecture
- **Backend**: FastAPI application with SQLAlchemy ORM deployed on Render
- **Frontend**: React/Next.js application deployed on Vercel
- **Database**: Supabase PostgreSQL with pgvector
- **Workers**: Enhanced background workers for document processing (Render Workers)
- **AI Integration**: LangChain, Anthropic, OpenAI for intelligent features

### Infrastructure Deployment Strategy
- **Production**: 
  - Backend: Render Web Service + Render Workers
  - Frontend: Vercel Production Environment
- **Staging**: 
  - Backend: Render Web Service + Render Workers (staging instances)
  - Frontend: Vercel Preview/Staging Environment
- **Development**: 
  - Backend: Local development server or Render staging instance
  - Frontend: Vercel CLI (local development) or Vercel preview deployments

### Current Environment Structure
Based on analysis of the project structure and deployment architecture:

1. **Development Environment** 
   - Backend: Local FastAPI server or Render staging instance
   - Frontend: Vercel CLI local development server
   - Configuration: `.env.development`
2. **Staging Environment** 
   - Backend: Render Web Service + Workers (staging instances)
   - Frontend: Vercel staging deployment
   - Configuration: `.env.staging`
3. **Production Environment** 
   - Backend: Render Web Service + Workers (production instances)
   - Frontend: Vercel production deployment
   - Configuration: `.env.production`

### Key Components Requiring Validation

#### Backend Services (Render)
- Main API application (`main.py`) - Render Web Service
- Background workers (`backend/workers/`) - Render Workers
- Database integrations (`core/database.py`)
- Service management (`core/service_manager.py`)

#### Frontend Services (Vercel)
- React/Next.js UI (`ui/`) - Vercel deployments
- Supabase client integration
- API communication layer
- Vercel CLI for local development

#### Infrastructure
- Render Web Services and Workers
- Vercel deployment platform
- Docker containerization (for Render deployments)
- Supabase backend services
- Environment variable management across platforms

## Validation Scope

### Primary Objectives
1. **Environment Synchronization**: Ensure development (Vercel CLI), staging (Render/Vercel staging), and production environments are properly configured and isolated
2. **Component Testing**: Validate all major components function correctly across Render and Vercel platforms
3. **Integration Testing**: Verify cross-service communication works properly between Render backend and Vercel frontend
4. **Deployment Readiness**: Confirm staging environment mirrors production configuration across both platforms
5. **Vercel CLI Integration**: Validate local development workflow using Vercel CLI instead of local React server

### Testing Priorities
1. **Unit Tests**: Core functionality validation (backend on Render, frontend components)
2. **Component Tests**: Service-level validation across platforms
3. **Integration Tests**: End-to-end workflow validation between Render and Vercel
4. **Environment Tests**: Configuration and connectivity validation across platforms
5. **Vercel CLI Tests**: Local development environment validation

### Key Risk Areas
- Database schema consistency across environments
- Environment variable configuration mismatches between Render and Vercel
- API endpoint connectivity between Render backend and Vercel frontend
- Worker process functionality and queue management on Render
- Authentication and authorization flows across platforms
- Document processing pipeline integrity
- Vercel CLI configuration and local development workflow
- Cross-platform environment variable synchronization

## Success Criteria
- All unit tests pass across development (Vercel CLI), staging (Render/Vercel), and production environments
- Component tests validate service isolation on both Render and Vercel platforms
- Integration tests confirm cross-service communication between Render backend and Vercel frontend
- Environment-specific configurations are validated across both platforms
- Vercel CLI local development environment is fully functional and tested
- Cross-platform environment variable synchronization is validated
- Manual testing handoff with comprehensive test coverage documentation for both platforms