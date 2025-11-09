# Insurance Navigator

A near HIPAA-compliant AI-powered system that helps patients understand their insurance documents through intelligent document processing and conversational AI. It's goal is to help people understand their 

## 🌐 Try It Now

**🚀 [Live Demo](https://insurance-navigator.vercel.app)**

The Insurance Navigator is available as a live demo. Upload your insurance documents and start asking questions immediately. The webapp is fully functional and ready to help you understand your insurance coverage, benefits, and claims.

**Note:** The project is now set up for local development. See the [Development Setup](#-development-setup) section below.

## 🎯 Overview

Insurance Navigator is a comprehensive platform that combines document processing, AI-powered analysis, and conversational interfaces to help patients navigate complex insurance information. The system processes insurance documents (PDFs, images) and provides intelligent responses to user questions about their coverage, benefits, and claims.

## 🏗️ System Architecture

System design diagrams coming soon.

The system consists of several key components including backend services, frontend UI, AI/ML components, and database infrastructure. Detailed architecture documentation and diagrams will be added shortly.

## 🔒 HIPAA Compliance Status

Insurance Navigator is **near HIPAA-compliant** and would achieve full HIPAA compliance if external services were to have Business Associate Agreements (BAAs) in place.

**Current Status:**
- The system architecture is designed with HIPAA compliance in mind
- Full HIPAA compliance requires BAAs with all external service providers

**Upcoming Work:**
- Deidentification and decoupling of all data from users
- This includes information sent to external APIs during:
  - Document processing
  - Chat interactions
  - Context processing

## 🛠️ Development Setup

The project uses [Overmind](https://github.com/DarthSim/overmind) to orchestrate development services.

**Prerequisites:**
- Docker Desktop (running)
- Supabase CLI
- Node.js (v18+)
- Overmind

**Installation:**
```bash
# Install Overmind
brew install overmind  # macOS
# See docs/environments/development/OVERMIND_SETUP.md for other platforms

# Install Supabase CLI
brew install supabase/tap/supabase  # macOS
```

**Start Development Environment:**
```bash
./scripts/dev-start.sh
# or
overmind start
```

**Stop Development Environment:**
```bash
./scripts/dev-stop.sh
# or
overmind stop
```

**View Logs:**
```bash
overmind logs
overmind logs frontend
overmind logs docker-services
overmind logs supabase
```

**Service URLs:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Supabase API: http://127.0.0.1:54321
- Supabase Studio: http://127.0.0.1:54323

See [docs/environments/development/OVERMIND_SETUP.md](docs/environments/development/OVERMIND_SETUP.md) for detailed setup and troubleshooting.

## 🚧 Next Steps

1. **Debug Concurrency Failures** - Resolve concurrent processing issues in the agentic system that cause timeouts and failures in the chat workflow
2. **Documentation** - Expand and improve project documentation
3. **Refactor Upload Pipeline** - Implement frontend deidentification of uploaded documents
4. **Refactor Agentic Workflows** - Simplify by removing strategy workflow (will be better once I can implement a strategy database and MCP) and focusing more on guardrails instead of routing between workflows. Also working to incorporate NLLB-200 to support helping as many people as possible
5. **Restructure User Profiles** - Buffer user info from user messages, documents, and other context
6. **OSS Launch** - With deidentification and stopgaps protecting data, launching an direct to consumer OSS to get feedback and help people!

## 📄 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

---

**Insurance Navigator** - Making insurance documents accessible through AI-powered analysis and conversation.
