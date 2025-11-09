# FRACAS FM-011: Render Worker IPv6 Connectivity Issue

## 🎯 **FAILURE MODE OVERVIEW**

**Category**: Connectivity  
**Priority**: P0 - Critical  
**Status**: Open  
**Environment**: Staging (Render)  

## 📁 **DIRECTORY STRUCTURE**

```
fm_011/
├── prompts/                         # Investigation prompts
│   └── FRACAS_FM_011_INVESTIGATION_PROMPT.md
├── docs/                           # Documentation and reports
│   ├── FRACAS_FM_011_RENDER_WORKER_IPV6_CONNECTIVITY.md
│   └── STAGING_WORKER_IPV6_FIX_CONTINUATION_PROMPT.md
└── README.md                       # This file
```

## 🔍 **INVESTIGATION PROMPTS**

- **File**: `prompts/FRACAS_FM_011_INVESTIGATION_PROMPT.md`
- **Purpose**: Comprehensive investigation guide for IPv6 connectivity issues
- **Time Estimate**: 100 minutes
- **Dependencies**: Access to Render staging environment and Supabase configuration

## 📄 **DOCUMENTATION**

- **File**: `docs/FRACAS_FM_011_RENDER_WORKER_IPV6_CONNECTIVITY.md`
- **Purpose**: Complete failure analysis and technical details
- **Status**: Ready for investigation

## 🚨 **CRITICAL ISSUE**

The staging worker service fails to connect to Supabase database due to IPv6 connectivity issues on Render platform.

## 🔧 **QUICK START**

1. Read the investigation prompt: `prompts/FRACAS_FM_011_INVESTIGATION_PROMPT.md`
2. Review the failure documentation: `docs/FRACAS_FM_011_RENDER_WORKER_IPV6_CONNECTIVITY.md`
3. Follow the investigation tasks in the prompt
4. Update documentation with findings

---

**Last Updated**: 2025-09-25  
**Maintained By**: Development Team
