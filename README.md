# Insurance Navigator

A near HIPAA-compliant AI-powered system that helps patients understand their insurance documents through intelligent document processing and conversational AI.

## 🌐 Try It Now

**🚀 [Live Demo](https://insurance-navigator.vercel.app)**

The Insurance Navigator is available as a live demo. Upload your insurance documents and start asking questions immediately. The webapp is fully functional and ready to help you understand your insurance coverage, benefits, and claims.

**📹 Demo Video**

Watch a demonstration of the Insurance Navigator in action, showing how it processes insurance documents and answers questions about coverage and benefits.

<div align="center">

![Insurance Navigator Demo](docs/media/gifs/chat_demo.gif)

</div>

**Note:** The project is not yet set up to be run locally on other machines. For now, please use the demo link above to experience the Insurance Navigator.

## 🎯 Overview

Insurance Navigator is a comprehensive platform that combines document processing, AI-powered analysis, and conversational interfaces to help patients navigate complex insurance information. The system processes insurance documents (PDFs, images) and provides intelligent responses to user questions about their coverage, benefits, and claims.

## 🏗️ System Architecture

The system consists of several key components including backend services, frontend UI, AI/ML components, and database infrastructure.

**📚 [System Design Documentation](./docs/architecture/README.md)**

Detailed architecture documentation, system design breakdowns, and diagrams are available in the [architecture documentation](./docs/architecture/README.md). System designs are created and expanded upon there.

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

1. **Debug Concurrency Failures** - Resolve concurrent processing issues in the system
2. **Documentation** - Expand and improve project documentation
3. **Refactor Upload Pipeline** - Implement frontend deidentification of uploaded documents
4. **Restructure User Profiles** - Buffer user info from user messages, documents, and other context

## 📄 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

---

**Insurance Navigator** - Making insurance documents accessible through AI-powered analysis and conversation.
