# Phase 2: Code Simplification - Implementation Prompt

## Overview
This prompt guides the implementation of Phase 2 of the Supabase Authentication Migration initiative. The goal is to simplify the codebase by removing custom user management logic and updating all components to use Supabase's built-in authentication system.

## Phase 2 Objectives
- Remove custom user management logic
- Update API endpoints for Supabase integration
- Simplify frontend authentication
- Remove all references to `public.users` table
- Update all components to use `auth.users` directly

## Required Documents

### Core Documents
- **[PRD](prd/PRD_SUPABASE_AUTH_MIGRATION.md)**: Product Requirements Document - Business objectives and requirements
- **[RFC](rfc/RFC_SUPABASE_AUTH_MIGRATION.md)**: Request for Comments - Technical design and implementation approach
- **[Phase Implementation Plan](phases/PHASE_IMPLEMENTATION_PLAN.md)**: Detailed phase breakdown and timeline

### Intermediate Documents (From Phase 1)
- **Phase 1 Handoff Document**: Environment setup completion and handoff details
- **Phase 1 Decision Log**: Key decisions made during environment configuration
- **Phase 1 Notes**: Observations, lessons learned, and configuration insights
- **Phase 1 Testing Summary**: Test results, validation outcomes, and environment verification

### Phase 2 Tasks
Refer to the Phase Implementation Plan for detailed task breakdown:
- **Phase 2.1**: Remove Custom User Management (Days 1-3)
- **Phase 2.2**: Update API Endpoints (Days 4-5)
- **Phase 2.3**: Simplify Frontend Integration (Days 6-7)

## Phase 2 Success Criteria

### Technical Success Criteria
- [ ] Custom user management logic removed
- [ ] API endpoints updated for Supabase integration
- [ ] Frontend authentication simplified
- [ ] All references to `public.users` removed
- [ ] All components use `auth.users` directly

### Functional Success Criteria
- [ ] Authentication works with Supabase auth only
- [ ] No custom user management needed
- [ ] All user data comes from `auth.users`
- [ ] Database queries use RLS automatically
- [ ] Upload pipeline works without errors

### Quality Success Criteria
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Error handling is comprehensive
- [ ] Performance meets requirements
- [ ] Code follows project standards

## Phase 2 Deliverables

### Code Deliverables
- [ ] `SupabaseAuthService` class
- [ ] Updated `AuthAdapter` with Supabase backend
- [ ] Updated API endpoints
- [ ] Updated middleware
- [ ] RLS context management

### Testing Deliverables
- [ ] Unit tests for authentication service
- [ ] Integration tests for API endpoints
- [ ] RLS policy tests
- [ ] Performance tests
- [ ] Error handling tests

### Documentation Deliverables
- [ ] API documentation updated
- [ ] Authentication flow documentation
- [ ] RLS integration guide
- [ ] Error handling documentation
- [ ] Migration procedures

### Intermediate Documents (End of Phase 2)
- [ ] **Phase 2 Handoff Document**: Summary of authentication implementation and handoff to Phase 3
- [ ] **Phase 2 Decision Log**: Key decisions made during auth service development
- [ ] **Phase 2 Notes**: Observations, lessons learned, and implementation insights
- [ ] **Phase 2 Testing Summary**: Test results, validation outcomes, and auth service verification

## Next Steps

After completing Phase 2:
1. **Review Phase 2 Results**: Validate all success criteria met
2. **Create Intermediate Documents**: Complete handoff, decision log, notes, and testing summary
3. **Prepare for Phase 3**: Set up database migration environment
4. **Begin Phase 3**: Start database migration and RLS integration

## Troubleshooting

### Common Issues
1. **Supabase Connection Issues**
   - Verify environment variables
   - Check Supabase project settings
   - Test connection with Supabase dashboard

2. **Token Validation Issues**
   - Verify JWT secret configuration
   - Check token format and expiration
   - Test token validation with Supabase

3. **RLS Policy Issues**
   - Verify RLS policies are enabled
   - Test policies with Supabase SQL editor
   - Check user permissions and roles

### Support Resources
- Supabase Documentation: https://supabase.com/docs
- Supabase Community: https://github.com/supabase/supabase/discussions
- Project Documentation: `docs/technical/auth_system.md`

---

**Phase 2 Completion Checklist**
- [ ] All tasks completed
- [ ] All deliverables created
- [ ] All success criteria met
- [ ] Intermediate documents created
- [ ] Ready for Phase 3
