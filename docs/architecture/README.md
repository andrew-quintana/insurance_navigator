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

#### Component Architecture Overview

High-level overview of system components and their relationships:

![Component Architecture Overview](./../../media/diagrams/uml_v0_2-component-architecture_overview.svg)

#### Agentic Workflows

**Simplified Version** (current standard):
![Agentic Workflows Simplified](./../../media/diagrams/uml_v0_2-component-agentic_workflows_simplified.svg)

> **Note:** The agentic workflow diagram will be updated and consolidated to use this simplified version going forward.

**Current Detailed Version** (legacy):
![Agentic Workflows Current](./../../media/diagrams/uml_v0_2-component-agentic_workflows_current.svg)

### Sequence Diagrams

#### Upload Sequence

Document upload and processing workflow:

![Upload Sequence](./../../media/diagrams/uml_v0_2-sequence-upload.svg)

### State Diagrams

#### Job State Machine

States and transitions for document processing jobs:

![Job State Machine](./../../media/diagrams/uml_v0_2-state-job_state_machine.svg)

#### Status State Logic

Status tracking and state management logic:

![Status State Logic](./../../media/diagrams/uml_v0_2-state-status_state_logic.svg)

#### Status States

Overall status state management:

![Status States](./../../media/diagrams/uml_v0_2-state-status.svg)

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
