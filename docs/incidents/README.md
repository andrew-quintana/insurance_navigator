# Incidents Directory - Organized by FRACAS Failure Mode

This directory contains all incident reports, investigations, and resolutions organized by FRACAS failure mode (FM-XXX) for better maintainability and reference.

## 📁 **Directory Structure**

```
docs/incidents/
├── fm_009/                         # LlamaParse API Invalid Token Format
│   ├── prompts/                    # Investigation prompts
│   ├── docs/                       # Documentation and reports
│   └── README.md                   # Failure mode overview
├── fm_010/                         # Chat Configuration Error
│   ├── prompts/                    # Investigation prompts
│   ├── docs/                       # Documentation and reports
│   └── README.md                   # Failure mode overview
├── fm_011/                         # Render Worker IPv6 Connectivity
│   ├── prompts/                    # Investigation prompts
│   ├── docs/                       # Documentation and reports
│   └── README.md                   # Failure mode overview
├── fm_012/                         # Staging Worker Storage Access Failure
│   ├── prompts/                    # Investigation prompts
│   ├── docs/                       # Documentation and reports
│   └── README.md                   # Failure mode overview
├── fm_013/                         # Environment Configuration Inconsistencies
│   ├── prompts/                    # Investigation prompts
│   ├── docs/                       # Documentation and reports
│   └── README.md                   # Failure mode overview
├── fm_014/                         # API Upload Authentication Failure
│   ├── prompts/                    # Investigation prompts
│   ├── docs/                       # Documentation and reports
│   └── README.md                   # Failure mode overview
├── fm_015/                         # End-to-End Workflow Database Constraint Violation
│   ├── prompts/                    # Investigation prompts
│   ├── docs/                       # Documentation and reports
│   └── README.md                   # Failure mode overview
└── README.md                       # This file
```

## 🎯 **FRACAS Failure Modes**

### **FM-009: LlamaParse API Invalid Token Format** (`fm_009/`)
- **Category**: API Integration
- **Priority**: P0 - Critical
- **Status**: Open
- **Environment**: Development
- **Issue**: Environment variable priority mismatch causing 100% document processing failure

### **FM-010: Chat Configuration Error** (`fm_010/`)
- **Category**: Configuration
- **Priority**: P1 - High
- **Status**: Open
- **Environment**: All
- **Issue**: Chat interface completely non-functional due to missing translation service API keys

### **FM-011: Render Worker IPv6 Connectivity** (`fm_011/`)
- **Category**: Connectivity
- **Priority**: P0 - Critical
- **Status**: Open
- **Environment**: Staging (Render)
- **Issue**: Worker service fails to connect to Supabase database due to IPv6 connectivity issues

### **FM-012: Staging Worker Storage Access Failure** (`fm_012/`)
- **Category**: Storage Access
- **Priority**: P0 - Critical
- **Status**: Resolved
- **Environment**: Staging
- **Issue**: 400 Bad Request errors when accessing files from Supabase Storage (RESOLVED)

### **FM-013: Environment Configuration Inconsistencies** (`fm_013/`)
- **Category**: Configuration
- **Priority**: P1 - High
- **Status**: Open
- **Environment**: All
- **Issue**: Multiple different approaches for loading environment variables and configuration

### **FM-014: API Upload Authentication Failure** (`fm_014/`)
- **Category**: Authentication
- **Priority**: P2 - Medium
- **Status**: Resolved (Workaround)
- **Environment**: Staging
- **Issue**: FastAPI dependency injection issue in no-auth endpoint (RESOLVED with workaround)

### **FM-015: End-to-End Workflow Database Constraint Violation** (`fm_015/`)
- **Category**: Database Constraint Violation
- **Priority**: P2 - Medium
- **Status**: Active Investigation
- **Environment**: Staging
- **Issue**: Database constraint violation preventing end-to-end workflow completion

### **FM-028: Intermittent Webhook Failures in Staging** (`fm_028/`)
- **Category**: Webhook Processing
- **Priority**: P1 - High
- **Status**: Resolved
- **Environment**: Staging
- **Issue**: Intermittent webhook processing failures causing document processing pipeline interruptions (RESOLVED)

### **FM-029: Chat Endpoint and Agentic Workflow/RAG Issues** (`fm_029/`)
- **Category**: RAG System / Agentic Workflow
- **Priority**: P1 - High
- **Status**: Open
- **Environment**: Staging
- **Issue**: RAG system returning 0 chunks, InformationRetrievalAgent unavailable, users receiving generic responses

## 🔍 **Investigation Prompts**

Each FRACAS failure mode has a corresponding investigation prompt in `fm_XXX/prompts/`:

### **FM-009: LlamaParse API Invalid Token Format**
- **File**: `fm_009/prompts/FRACAS_FM_009_INVESTIGATION_PROMPT.md`
- **Category**: API Integration
- **Priority**: P0 - Critical
- **Status**: Ready for Assignment

### **FM-010: Chat Configuration Error**
- **File**: `fm_010/prompts/FRACAS_FM_010_INVESTIGATION_PROMPT.md`
- **Category**: Configuration
- **Priority**: P1 - High
- **Status**: Ready for Assignment

### **FM-011: Render Worker IPv6 Connectivity**
- **File**: `fm_011/prompts/FRACAS_FM_011_INVESTIGATION_PROMPT.md`
- **Category**: Connectivity
- **Priority**: P0 - Critical
- **Status**: Ready for Assignment

### **FM-012: Staging Worker Storage Access Failure**
- **File**: `fm_012/prompts/FRACAS_FM_012_INVESTIGATION_PROMPT.md`
- **Category**: Storage Access
- **Priority**: P0 - Critical
- **Status**: Ready for Assignment

### **FM-013: Environment Configuration Inconsistencies**
- **File**: `fm_013/prompts/FRACAS_FM_013_INVESTIGATION_PROMPT.md`
- **Category**: Configuration
- **Priority**: P1 - High
- **Status**: Ready for Assignment

### **FM-014: API Upload Authentication Failure**
- **File**: `fm_014/prompts/FRACAS_FM_014_INVESTIGATION_PROMPT.md`
- **Category**: Authentication
- **Priority**: P2 - Medium
- **Status**: Resolved (Workaround)

### **FM-015: End-to-End Workflow Database Constraint Violation**
- **File**: `fm_015/prompts/FRACAS_FM_015_INVESTIGATION_PROMPT.md`
- **Category**: Database Constraint Violation
- **Priority**: P2 - Medium
- **Status**: Ready for Assignment

### **FM-028: Intermittent Webhook Failures in Staging**
- **File**: `fm_028/prompts/FRACAS_FM_028_INVESTIGATION_PROMPT.md`
- **Category**: Webhook Processing
- **Priority**: P1 - High
- **Status**: Resolved

### **FM-029: Chat Endpoint and Agentic Workflow/RAG Issues**
- **File**: `fm_029/prompts/FRACAS_FM_029_INVESTIGATION_PROMPT.md`
- **Category**: RAG System / Agentic Workflow
- **Priority**: P1 - High
- **Status**: Ready for Assignment

## 📋 **How to Use Investigation Prompts**

1. **Select a FRACAS**: Choose the appropriate failure mode from `fm_XXX/`
2. **Read the README**: Review the failure mode overview in `fm_XXX/README.md`
3. **Read the Investigation Prompt**: Review `fm_XXX/prompts/FRACAS_FM_XXX_INVESTIGATION_PROMPT.md`
4. **Read the Reference Document**: Review the corresponding FRACAS document in `fm_XXX/docs/`
5. **Follow the Investigation Tasks**: Each prompt provides detailed investigation steps
6. **Use the Test Commands**: Provided test commands help verify the issue and solution
7. **Update Documentation**: Update the FRACAS document with findings and resolution

## 🔧 **Investigation Prompt Structure**

Each investigation prompt follows this structure:

- **Investigation Mission**: Clear objective and reference document
- **Current Situation**: Critical issue details and evidence
- **Investigation Tasks**: Step-by-step investigation with time estimates
- **Test Commands**: Specific commands to test and verify
- **Expected Output**: What should be achieved
- **Deliverables**: What needs to be produced
- **Critical Notes**: Important considerations
- **Escalation Criteria**: When to escalate the issue

## 📊 **Current Status Summary**

| FRACAS | Category | Priority | Status | Investigation Prompt |
|--------|----------|----------|---------|---------------------|
| FM-009 | API Integration | P0 | Open | ✅ Ready |
| FM-010 | Configuration | P1 | Open | ✅ Ready |
| FM-011 | Connectivity | P0 | Open | ✅ Ready |
| FM-012 | Storage Access | P0 | Resolved | ✅ Ready |
| FM-013 | Configuration | P1 | Open | ✅ Ready |
| FM-014 | Authentication | P2 | Resolved | ✅ Ready |
| FM-015 | Database Constraint Violation | P2 | Active Investigation | ✅ Ready |
| FM-028 | Webhook Processing | P1 | Resolved | ✅ Ready |
| FM-029 | RAG System / Agentic Workflow | P1 | Open | ✅ Ready |

## 🚀 **Next Steps**

1. **Assign Investigations**: Assign investigation prompts to appropriate team members
2. **Track Progress**: Use the investigation prompts to track investigation progress
3. **Update Documentation**: Keep FRACAS documents updated with findings
4. **Create New Prompts**: Create new investigation prompts for new failure modes
5. **Review and Improve**: Regularly review and improve the investigation process

## 📝 **Contributing**

When creating new incident reports or investigation prompts:

1. **Categorize by Failure Mode**: Place incidents in the appropriate failure mode directory
2. **Follow Naming Conventions**: Use consistent naming for files
3. **Create Investigation Prompts**: Create corresponding investigation prompts
4. **Update This README**: Keep the directory structure and status updated
5. **Reference FRACAS Documents**: Always reference the appropriate FRACAS document

---

**Last Updated**: 2025-10-01  
**Maintained By**: Development Team  
**Review Frequency**: Monthly
