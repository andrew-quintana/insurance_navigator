# Insurance Navigator

A soon-to-be HIPAA-compliant AI-powered system that helps patients understand their insurance documents through intelligent document processing and conversational AI.

## 🎯 Overview

Insurance Navigator is a comprehensive platform that combines document processing, AI-powered analysis, and conversational interfaces to help patients navigate complex insurance information. The system processes insurance documents (PDFs, images) and provides intelligent responses to user questions about their coverage, benefits, and claims.

### Key Features

- **Document Processing**: Upload and process insurance documents with LlamaParse integration
- **AI-Powered Analysis**: Intelligent document understanding with RAG (Retrieval-Augmented Generation)
- **Conversational Interface**: Natural language chat interface for insurance queries
- **Soon-to-be HIPAA Compliance**: Secure, encrypted document storage and processing
- **Multi-User Support**: User authentication and document isolation
- **Real-time Processing**: Asynchronous document processing pipeline

## 🏗️ Architecture

The system consists of several key components:

### Backend (FastAPI)
- **Main API**: `main.py` - Core FastAPI application with authentication and chat endpoints
- **Upload Pipeline**: Document processing with job queue management
- **Agent System**: AI agents for information retrieval and workflow management
- **Database Services**: PostgreSQL with Supabase integration

### Frontend (React/TypeScript)
- **UI Components**: Modern React components for document upload and chat interface
- **Authentication**: Supabase Auth integration
- **Real-time Updates**: WebSocket connections for processing status

### AI/ML Components
- **RAG System**: Vector-based document retrieval and generation
- **Insurance Navigator Agents**: Specialized AI agents for insurance document analysis
- **Document Processing**: LlamaParse integration for PDF text extraction

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL database
- Supabase account
- OpenAI API key
- LlamaParse API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd insurance_navigator
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   npm install
   ```

4. **Set up environment variables**
   ```bash
   cp config/env.development.example .env.development
   # Edit .env.development with your configuration
   ```

5. **Initialize the database**
   ```bash
   # Apply Supabase migrations
   supabase db reset
   ```

6. **Start the development server**
   ```bash
   # Backend
   python main.py
   
   # Frontend (in another terminal)
   cd ui
   npm run dev
   ```

## 📁 Project Structure

```
insurance_navigator/
├── agents/                    # AI agents and workflows
│   ├── patient_navigator/    # Insurance navigation agents
│   └── tooling/              # RAG and MCP tools
├── api/                      # API endpoints
│   └── upload_pipeline/      # Document upload processing
├── backend/                  # Backend services
│   ├── integration/          # External service integration
│   ├── monitoring/           # System monitoring
│   └── workers/              # Background workers
├── config/                   # Configuration files
│   ├── docker/               # Docker configurations
│   └── environment/           # Environment-specific configs
├── core/                     # Core system components
├── db/                       # Database services
├── docs/                     # Documentation
├── examples/                 # Sample documents for testing
├── supabase/                 # Database migrations
├── tests/                    # Test suites
├── ui/                       # Frontend React application
└── utils/                    # Utility functions
```

## 📄 Testing with Example Documents

The `/examples` directory contains sample insurance documents for testing:

### Available Test Documents

1. **`scan_classic_hmo.pdf`** - Sample HMO insurance document
2. **`simulated_insurance_document.pdf`** - Simulated insurance policy document

### Using Example Documents

1. **Upload via Web Interface**
   - Navigate to the upload page in the UI
   - Drag and drop or select one of the example PDFs
   - Monitor the processing status in real-time

2. **Upload via API**
   ```bash
   # Get authentication token first
   curl -X POST http://localhost:8000/login \
     -H "Content-Type: application/json" \
     -d '{"email": "your-email", "password": "your-password"}'
   
   # Upload document
   curl -X POST http://localhost:8000/api/upload-pipeline/upload \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "filename": "scan_classic_hmo.pdf",
       "bytes_len": 1234567,
       "mime": "application/pdf",
       "sha256": "your-file-hash"
     }'
   ```

3. **Chat with Processed Documents**
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What is my deductible?",
       "conversation_id": "conv_123"
     }'
   ```

## 🔧 Configuration

### Environment Variables

Key environment variables for configuration:

```bash
# Database
DATABASE_URL=postgresql://...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI Services
OPENAI_API_KEY=your-openai-key
LLAMAPARSE_API_KEY=your-llamaparse-key

# Application
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
```

### Configuration Files

- **`config/config.yaml`** - Main configuration
- **`config/env.*.example`** - Environment-specific examples
- **`pyproject.toml`** - Python project configuration

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/fm_027/  # Incident-specific tests
```

### Test Organization

- **`tests/unit/`** - Unit tests for individual components
- **`tests/integration/`** - Integration tests across components
- **`tests/fm_027/`** - Tests related to specific incidents
- **`tests/debug/`** - Debugging and diagnostic tests

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Production Deployment

1. **Set production environment variables**
2. **Deploy to your preferred platform** (Render, Vercel, etc.)
3. **Configure database connections**
4. **Set up monitoring and logging**

## 📊 Monitoring

The system includes comprehensive monitoring:

- **Health Checks**: `/health` endpoint for system status
- **Debug Endpoints**: `/debug-auth`, `/debug-resilience` for diagnostics
- **Performance Metrics**: Request timing and processing metrics
- **Error Tracking**: Comprehensive error logging and handling

## 🔒 Security

### Soon-to-be HIPAA Compliance

- **Encryption**: All documents encrypted at rest and in transit
- **Access Control**: User-based document isolation
- **Audit Logging**: Comprehensive access and processing logs
- **Data Retention**: Configurable data retention policies

### Authentication

- **Supabase Auth**: Secure user authentication
- **JWT Tokens**: Stateless authentication
- **Row Level Security**: Database-level access control

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines

- Follow the existing code structure
- Add comprehensive tests
- Update documentation
- Ensure soon-to-be HIPAA compliance for any changes

## 📚 Documentation

- **`docs/`** - Comprehensive documentation
- **`docs/architecture/`** - System architecture details
- **`docs/deployment/`** - Deployment guides
- **`docs/development/`** - Development setup and guidelines

## 🐛 Troubleshooting

### Common Issues

1. **Document Processing Failures**
   - Check LlamaParse API key
   - Verify document format (PDF supported)
   - Check file size limits (5MB max)

2. **Authentication Issues**
   - Verify Supabase configuration
   - Check JWT token validity
   - Ensure proper CORS settings

3. **Database Connection Issues**
   - Verify DATABASE_URL
   - Check Supabase project status
   - Ensure proper network access

### Debug Endpoints

- **`/debug-auth`** - Authentication status
- **`/debug-resilience`** - System resilience status
- **`/debug-env`** - Environment variable status

## 📄 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the documentation in `/docs`
- Review the troubleshooting section above

---

**Insurance Navigator** - Making insurance documents accessible through AI-powered analysis and conversation.
