# 📚 Insurance Navigator Documentation

Welcome to the comprehensive documentation for the Insurance Navigator system. This directory contains all current project documentation organized by category.

## 📁 Documentation Structure

### 🏗️ [Architecture](./architecture/)
System architecture and design documents:
- System design patterns and diagrams
- Component interactions
- Data flow diagrams
- Agent workflow architecture

### 🎯 [Design](./design/)
Design specifications and system-level designs:
- System-level design
- Agent-level design
- I/O specifications
- Design rationale

### 🤖 [Agents](./agents/)
Agent system documentation:
- Agent organization and structure
- Regulatory agent documentation
- Agent troubleshooting guides
- Agent workflow patterns

### 🚀 [Deployment](./deployment/)
Production deployment documentation:
- Deployment guides and procedures
- Environment configuration
- Cloud service setup
- Troubleshooting guides

### 🔐 [Security](./security/)
Security documentation and compliance:
- Security configuration
- CORS management
- Environment management rules
- Function security guidelines

### 📋 [Project](./project/)
Core project information:
- Project overview and goals
- Implementation status
- Development guidelines
- Best practices

### 📊 [Examples](./examples/)
Usage examples and demonstrations:
- API usage examples
- Integration patterns
- Sample configurations

### 🔍 [FMEA](./fmea/)
Failure Mode and Effects Analysis:
- System-level FMEA
- Component-level analysis
- Risk assessment templates

## Historical Documentation

For historical context, implementation progress, and past technical decisions, please refer to the [archive](./archive/) directory.

## 🚀 Quick Start

1. **New to the project?** Start with [Project README](./project/README.md)
2. **Ready to deploy?** Check [Deployment Guide](./deployment/deploy-guide.md)
3. **Having issues?** Browse the troubleshooting guides in each section

## 📖 Integration Guides

Available in the root docs directory:
- **[supabase_integration_guide.md](./supabase_integration_guide.md)** - Complete Supabase setup
- **[fastapi_integration_guide.md](./fastapi_integration_guide.md)** - FastAPI configuration
- **[supabase_storage_integration.md](./supabase_storage_integration.md)** - File storage setup
- **[vector_migration_guide.md](./vector_migration_guide.md)** - Vector database migration
- **[phase2_summary.md](./phase2_summary.md)** - Development phase summary

## 🔍 Finding Information

### By Topic:
- **Setup & Installation** → [Project](./project/)
- **Production Deployment** → [Deployment](./deployment/)
- **Agent Configuration** → [Agents](./agents/)
- **API Integration** → Root directory integration guides
- **Security Setup** → [Security](./security/)
- **Troubleshooting** → Check relevant category folders

### By User Type:
- **Developers** → [Project](./project/), [Architecture](./architecture/), [Examples](./examples/)
- **DevOps Engineers** → [Deployment](./deployment/), [Security](./security/)
- **Product Managers** → [Project](./project/), [Design](./design/)
- **Data Scientists** → [Prompt Management](./prompt_management/), [Prompt Evaluation](./prompt_evaluation/)

## 📝 Contributing to Documentation

When adding new documentation:
1. Place it in the appropriate category directory
2. Update this README if adding new categories
3. Follow the established format and style
4. Include clear examples where applicable
5. Cross-reference related documentation

## 🏷️ Documentation Standards

- All documentation should be in Markdown format
- Use clear headings and subheadings
- Include code examples where relevant
- Keep content up-to-date with the current implementation
- Archive outdated documentation instead of deleting

---

**Need help?** Start with the most relevant category above or browse the integration guides for specific technical setup instructions.

---

# Documentation Contract

This repository standardizes initiative docs so tools (Cursor, Claude Code) can reliably discover adjacent systems and stay within context budgets.

**Hierarchy**
/docs/

	/initiatives/           # initiative serials (CONTEXTxxx, PRDxxx, RFCxxx, TODOxxx)

	/knowledge/             # cross-initiative knowledge: impl notes, test summaries, tech debt, change logs

	/summaries/rollups/     # 200–400 word per-component rollups

	/meta/                  # templates, indices, adjacency graph, search config

**Principles**
1. Adjacent-first: PRDs/RFCs/TODOs must cite the freshest adjacent rollups + interfaces.
2. Pin contracts: RFCs must include verbatim interface signatures for all integrations.
3. Budgeted context: Prefer rollups; only include code for interface surfaces.

## Isolation Exception
If an initiative is truly isolated, set in CONTEXTXXX.md:

> Isolation: true  
> Isolation_Justification: {1–2 sentences}

CI will skip adjacency freshness & citation checks when `Isolation: true`. 