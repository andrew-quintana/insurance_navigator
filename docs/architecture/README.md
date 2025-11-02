# Architecture Documentation

This directory contains detailed system architecture documentation, design breakdowns, and diagrams for the Insurance Navigator platform.

## System Design Overview

The Insurance Navigator is built with a modular architecture that separates concerns across multiple layers:

### Core Components

1. **Frontend (Next.js)**
   - User interface and document upload
   - Chat interface for interacting with processed documents
   - Client-side document processing and validation

2. **Backend Services (FastAPI)**
   - RESTful API endpoints
   - Document processing pipeline
   - AI agent orchestration
   - Integration with external services

3. **AI/ML Layer**
   - Document parsing and extraction
   - Natural language processing
   - Conversational AI agents
   - Vector embeddings and semantic search

4. **Database Infrastructure (Supabase/PostgreSQL)**
   - User management and authentication
   - Document storage and metadata
   - Vector database for semantic search
   - Job and status tracking

5. **Storage Layer**
   - Document storage (Supabase Storage)
   - Processed document caching
   - Vector embeddings storage

## Architecture Diagrams

The following diagrams illustrate various aspects of the system architecture:

### Component Diagrams

- **[Component Architecture Overview](./../../media/diagrams/uml_v0_2-component-architecture_overview.svg)** - High-level overview of system components and their relationships

- **[Agentic Workflows (Simplified)](./../../media/diagrams/uml_v0_2-component-agentic_workflows_simplified.svg)** - Simplified view of the agentic workflow system
  - **Note:** The agentic workflow diagram will be updated and consolidated to use this simplified version going forward

- **[Agentic Workflows (Current)](./../../media/diagrams/uml_v0_2-component-agentic_workflows_current.svg)** - Current detailed agentic workflow diagram

### Sequence Diagrams

- **[Upload Sequence](./../../media/diagrams/uml_v0_2-sequence-upload.svg)** - Document upload and processing workflow

### State Diagrams

- **[Job State Machine](./../../media/diagrams/uml_v0_2-state-job_state_machine.svg)** - States and transitions for document processing jobs

- **[Status State Logic](./../../media/diagrams/uml_v0_2-state-status_state_logic.svg)** - Status tracking and state management logic

- **[Status States](./../../media/diagrams/uml_v0_2-state-status.svg)** - Overall status state management

## Pending Updates

### Upload Pipeline

The upload pipeline is currently being refactored to implement frontend deidentification of uploaded documents. **Corresponding architecture diagrams for the updated upload pipeline have not been created yet** and will be added once the refactoring is complete.

### Agentic Workflows

The agentic workflow documentation and diagrams are being consolidated. The current workflow will be updated to use the simplified version: `media/diagrams/uml_v0_2-component-agentic_workflows_simplified.svg`.

## Additional Documentation

For more detailed information about specific system components, refer to:

- Configuration and environment setup
- API endpoints and integration guides
- Security and HIPAA compliance measures
- Testing and deployment procedures
