# Emergency Quick Reference Prompt - Critical Issues Resolution

## Emergency Implementation Instructions

If you encounter critical issues during implementation that require immediate attention, use this quick reference to identify and resolve the most common problems.

### Critical Issue Quick Reference

#### **RAG Tool Not Available**
- **Reference**: @docs/initiatives/agents/integration/phase3/rca/20250915_comprehensive_refactor/rollups/rag_system_rollup.md
- **Check**: Service initialization in main.py startup sequence
- **Verify**: RAG tool import and dependency injection

#### **Configuration Not Loading**
- **Reference**: @docs/initiatives/agents/integration/phase3/rca/20250915_comprehensive_refactor/rollups/configuration_management_rollup.md
- **Check**: Environment variable loading and configuration validation
- **Verify**: Similarity threshold set to 0.3 for production

#### **Database Schema Errors**
- **Reference**: @docs/initiatives/agents/integration/phase3/rca/20250915_comprehensive_refactor/rollups/database_schema_rollup.md
- **Check**: Table name references (chunks vs document_chunks)
- **Verify**: Foreign key relationships and query structure

#### **UUID Generation Issues**
- **Reference**: @docs/initiatives/agents/integration/phase3/rca/202509100800_rag_conformance/uuid_refactor/RFC001_UUID_STANDARDIZATION.md
- **Check**: Deterministic UUID generation across all components
- **Verify**: Pipeline continuity from upload to retrieval

#### **Service Integration Failures**
- **Reference**: @docs/initiatives/agents/integration/phase3/rca/20250915_comprehensive_refactor/rollups/main_api_service_rollup.md
- **Check**: Service initialization and dependency injection
- **Verify**: All services properly connected and communicating

### Emergency Escalation
If issues cannot be resolved using the referenced documents:
1. **Immediate**: Check the risk mitigation strategies in @docs/initiatives/agents/integration/phase3/rca/20250915_comprehensive_refactor/TODO001.md
2. **Contingency**: Review contingency plans in @docs/initiatives/agents/integration/phase3/rca/20250915_comprehensive_refactor/EXECUTIVE_SUMMARY.md
3. **Rollback**: Follow rollback procedures as specified in the phase-specific prompts

### Quick Validation Checklist
- [ ] All services initialized correctly
- [ ] Configuration loaded from environment variables
- [ ] Database schema references correct table names
- [ ] UUID generation consistent across pipeline stages
- [ ] RAG tool available and functional
- [ ] End-to-end workflow working (upload → chat)

### Success Criteria Verification
- **Functional**: 100% end-to-end workflow functionality
- **Performance**: Upload < 500ms, RAG < 2s, complete workflow < 10s
- **Reliability**: 99%+ uptime with proper error handling
- **Production Ready**: All Phase 3 success criteria met

Use this quick reference only for emergency situations. For normal implementation, follow the phase-specific prompts and referenced documentation.
