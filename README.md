# Insurance Navigator

A near HIPAA-compliant AI-powered system that helps patients understand their insurance documents through intelligent document processing and conversational AI. It's goal is to help people understand their 

## 🌐 Try It Now

**🚀 [Live Demo](https://insurance-navigator.vercel.app)**

The Insurance Navigator is available as a live demo. Upload your insurance documents and start asking questions immediately. The webapp is fully functional and ready to help you understand your insurance coverage, benefits, and claims.

**Note:** The project is not yet set up to be run locally on other machines. For now, please use the demo link above to experience the Insurance Navigator.

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
