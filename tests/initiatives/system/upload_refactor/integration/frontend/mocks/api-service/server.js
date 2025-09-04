const express = require('express');
const cors = require('cors');
const multer = require('multer');
const jwt = require('jsonwebtoken');
const bodyParser = require('body-parser');
const helmet = require('helmet');
const { v4: uuidv4 } = require('uuid');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3002;
const JWT_SECRET = process.env.JWT_SECRET || 'test-secret-key-12345';
const AUTH_SERVICE_URL = process.env.AUTH_SERVICE_URL || 'http://localhost:3001';
const UPLOAD_MAX_SIZE = parseInt(process.env.UPLOAD_MAX_SIZE) || 52428800; // 50MB
const ALLOWED_FILE_TYPES = (process.env.ALLOWED_FILE_TYPES || 'application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document').split(',');

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  credentials: true
}));
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '50mb' }));

// Configure multer for file uploads
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  limits: {
    fileSize: UPLOAD_MAX_SIZE
  },
  fileFilter: (req, file, cb) => {
    if (ALLOWED_FILE_TYPES.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error(`File type ${file.mimetype} not allowed. Allowed types: ${ALLOWED_FILE_TYPES.join(', ')}`));
    }
  }
});

// In-memory storage for testing
const documents = new Map();
const uploadJobs = new Map();
const conversations = new Map();
const messages = new Map();

// Helper functions
const verifyToken = async (token) => {
  try {
    // Verify token locally first
    const decoded = jwt.verify(token, JWT_SECRET);
    
    // Also verify with auth service
    const response = await fetch(`${AUTH_SERVICE_URL}/auth/v1/user`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.ok) {
      return decoded;
    }
    return null;
  } catch (error) {
    return null;
  }
};

const authenticateRequest = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Authorization header with Bearer token is required'
      });
    }
    
    const token = authHeader.substring(7);
    const decoded = await verifyToken(token);
    
    if (!decoded) {
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Invalid or expired token'
      });
    }
    
    req.user = decoded;
    next();
  } catch (error) {
    console.error('Authentication error:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: 'Authentication failed'
    });
  }
};

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'healthy', 
    service: 'mock-api-service',
    auth_service: AUTH_SERVICE_URL,
    upload_max_size: UPLOAD_MAX_SIZE,
    allowed_file_types: ALLOWED_FILE_TYPES
  });
});

// API endpoints

// POST /api/upload - Document upload
app.post('/api/upload', authenticateRequest, upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        error: 'No file provided',
        message: 'File is required'
      });
    }
    
    const documentId = uuidv4();
    const userId = req.user.userId;
    
    // Create document record
    const document = {
      id: documentId,
      userId: userId,
      filename: req.file.originalname,
      mimetype: req.file.mimetype,
      size: req.file.size,
      status: 'queued',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    documents.set(documentId, document);
    
    // Create upload job
    const jobId = uuidv4();
    const uploadJob = {
      id: jobId,
      documentId: documentId,
      userId: userId,
      status: 'queued',
      progress: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    uploadJobs.set(jobId, uploadJob);
    
    // Simulate processing
    setTimeout(() => {
      uploadJob.status = 'processing';
      uploadJob.progress = 25;
      uploadJob.updated_at = new Date().toISOString();
      
      setTimeout(() => {
        uploadJob.status = 'processing';
        uploadJob.progress = 50;
        uploadJob.updated_at = new Date().toISOString();
        
        setTimeout(() => {
          uploadJob.status = 'processing';
          uploadJob.progress = 75;
          uploadJob.updated_at = new Date().toISOString();
          
          setTimeout(() => {
            uploadJob.status = 'complete';
            uploadJob.progress = 100;
            uploadJob.updated_at = new Date().toISOString();
            
            document.status = 'complete';
            document.updated_at = new Date().toISOString();
          }, 1000);
        }, 1000);
      }, 1000);
    }, 1000);
    
    res.status(200).json({
      documentId: documentId,
      jobId: jobId,
      message: 'Document uploaded successfully',
      status: 'queued'
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({
      error: 'Upload failed',
      message: error.message
    });
  }
});

// GET /api/documents - Get user documents
app.get('/api/documents', authenticateRequest, (req, res) => {
  try {
    const userId = req.user.userId;
    const userDocuments = Array.from(documents.values())
      .filter(doc => doc.userId === userId)
      .map(doc => ({
        id: doc.id,
        filename: doc.filename,
        mimetype: doc.mimetype,
        size: doc.size,
        status: doc.status,
        created_at: doc.created_at,
        updated_at: doc.updated_at
      }));
    
    res.status(200).json(userDocuments);
  } catch (error) {
    console.error('Get documents error:', error);
    res.status(500).json({
      error: 'Failed to get documents',
      message: 'Internal server error'
    });
  }
});

// GET /api/documents/:id - Get specific document
app.get('/api/documents/:id', authenticateRequest, (req, res) => {
  try {
    const documentId = req.params.id;
    const userId = req.user.userId;
    
    const document = documents.get(documentId);
    if (!document) {
      return res.status(404).json({
        error: 'Document not found',
        message: 'Document not found'
      });
    }
    
    if (document.userId !== userId) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'Access denied to this document'
      });
    }
    
    res.status(200).json(document);
  } catch (error) {
    console.error('Get document error:', error);
    res.status(500).json({
      error: 'Failed to get document',
      message: 'Internal server error'
    });
  }
});

// DELETE /api/documents/:id - Delete document
app.delete('/api/documents/:id', authenticateRequest, (req, res) => {
  try {
    const documentId = req.params.id;
    const userId = req.user.userId;
    
    const document = documents.get(documentId);
    if (!document) {
      return res.status(404).json({
        error: 'Document not found',
        message: 'Document not found'
      });
    }
    
    if (document.userId !== userId) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'Access denied to this document'
      });
    }
    
    // Delete document and related data
    documents.delete(documentId);
    
    // Delete related upload jobs
    for (const [jobId, job] of uploadJobs.entries()) {
      if (job.documentId === documentId) {
        uploadJobs.delete(jobId);
      }
    }
    
    res.status(200).json({
      message: 'Document deleted successfully'
    });
  } catch (error) {
    console.error('Delete document error:', error);
    res.status(500).json({
      error: 'Failed to delete document',
      message: 'Internal server error'
    });
  }
});

// GET /api/documents/:id/status - Get document processing status
app.get('/api/documents/:id/status', authenticateRequest, (req, res) => {
  try {
    const documentId = req.params.id;
    const userId = req.user.userId;
    
    const document = documents.get(documentId);
    if (!document) {
      return res.status(404).json({
        error: 'Document not found',
        message: 'Document not found'
      });
    }
    
    if (document.userId !== userId) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'Access denied to this document'
      });
    }
    
    // Find related upload job
    const uploadJob = Array.from(uploadJobs.values())
      .find(job => job.documentId === documentId);
    
    res.status(200).json({
      documentId: documentId,
      status: document.status,
      progress: uploadJob ? uploadJob.progress : 0,
      updated_at: document.updated_at
    });
  } catch (error) {
    console.error('Get document status error:', error);
    res.status(500).json({
      error: 'Failed to get document status',
      message: 'Internal server error'
    });
  }
});

// POST /api/chat - Send chat message
app.post('/api/chat', authenticateRequest, async (req, res) => {
  try {
    const { message, conversationId, userId } = req.body;
    
    if (!message) {
      return res.status(400).json({
        error: 'Message required',
        message: 'Message content is required'
      });
    }
    
    const messageId = uuidv4();
    const currentUserId = req.user.userId;
    
    // Create or get conversation
    let conversation = conversations.get(conversationId);
    if (!conversation) {
      conversation = {
        id: conversationId || uuidv4(),
        userId: currentUserId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      conversations.set(conversation.id, conversation);
    }
    
    // Verify conversation ownership
    if (conversation.userId !== currentUserId) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'Access denied to this conversation'
      });
    }
    
    // Create message
    const chatMessage = {
      id: messageId,
      conversationId: conversation.id,
      userId: currentUserId,
      content: message,
      type: 'user',
      created_at: new Date().toISOString()
    };
    
    messages.set(messageId, chatMessage);
    
    // Simulate agent response
    setTimeout(() => {
      const agentMessageId = uuidv4();
      const agentMessage = {
        id: agentMessageId,
        conversationId: conversation.id,
        userId: 'agent',
        content: `This is a mock response to: "${message}". I'm simulating an AI agent response for testing purposes.`,
        type: 'agent',
        metadata: {
          agentType: 'mock-agent',
          documentContext: true,
          userId: currentUserId,
          responseTime: Math.random() * 2000 + 500
        },
        created_at: new Date().toISOString()
      };
      
      messages.set(agentMessageId, agentMessage);
      conversation.updated_at = new Date().toISOString();
    }, Math.random() * 2000 + 500); // Random delay between 500ms and 2.5s
    
    res.status(200).json({
      messageId: messageId,
      conversationId: conversation.id,
      message: 'Message sent successfully',
      status: 'processing'
    });
  } catch (error) {
    console.error('Chat error:', error);
    res.status(500).json({
      error: 'Failed to send message',
      message: 'Internal server error'
    });
  }
});

// GET /api/conversations - Get user conversations
app.get('/api/conversations', authenticateRequest, (req, res) => {
  try {
    const userId = req.user.userId;
    const userConversations = Array.from(conversations.values())
      .filter(conv => conv.userId === userId)
      .map(conv => ({
        id: conv.id,
        created_at: conv.created_at,
        updated_at: conv.updated_at,
        messageCount: Array.from(messages.values())
          .filter(msg => msg.conversationId === conv.id).length
      }));
    
    res.status(200).json(userConversations);
  } catch (error) {
    console.error('Get conversations error:', error);
    res.status(500).json({
      error: 'Failed to get conversations',
      message: 'Internal server error'
    });
  }
});

// GET /api/conversations/:id/messages - Get conversation messages
app.get('/api/conversations/:id/messages', authenticateRequest, (req, res) => {
  try {
    const conversationId = req.params.id;
    const userId = req.user.userId;
    
    const conversation = conversations.get(conversationId);
    if (!conversation) {
      return res.status(404).json({
        error: 'Conversation not found',
        message: 'Conversation not found'
      });
    }
    
    if (conversation.userId !== userId) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'Access denied to this conversation'
      });
    }
    
    const conversationMessages = Array.from(messages.values())
      .filter(msg => msg.conversationId === conversationId)
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    
    res.status(200).json(conversationMessages);
  } catch (error) {
    console.error('Get conversation messages error:', error);
    res.status(500).json({
      error: 'Failed to get conversation messages',
      message: 'Internal server error'
    });
  }
});

// WebSocket endpoint for real-time updates (simulated with polling)
app.get('/api/ws/upload-progress/:jobId', authenticateRequest, (req, res) => {
  try {
    const jobId = req.params.jobId;
    const userId = req.user.userId;
    
    const uploadJob = uploadJobs.get(jobId);
    if (!uploadJob) {
      return res.status(404).json({
        error: 'Upload job not found',
        message: 'Upload job not found'
      });
    }
    
    if (uploadJob.userId !== userId) {
      return res.status(403).json({
        error: 'Forbidden',
        message: 'Access denied to this upload job'
      });
    }
    
    res.status(200).json({
      jobId: jobId,
      status: uploadJob.status,
      progress: uploadJob.progress,
      updated_at: uploadJob.updated_at
    });
  } catch (error) {
    console.error('Get upload progress error:', error);
    res.status(500).json({
      error: 'Failed to get upload progress',
      message: 'Internal server error'
    });
  }
});

// Test endpoints for integration testing
app.get('/test/documents', (req, res) => {
  const documentList = Array.from(documents.values());
  res.json(documentList);
});

app.get('/test/upload-jobs', (req, res) => {
  const jobList = Array.from(uploadJobs.values());
  res.json(jobList);
});

app.get('/test/conversations', (req, res) => {
  const conversationList = Array.from(conversations.values());
  res.json(conversationList);
});

app.delete('/test/clear', (req, res) => {
  documents.clear();
  uploadJobs.clear();
  conversations.clear();
  messages.clear();
  res.json({ message: 'All test data cleared' });
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        error: 'File too large',
        message: `File size exceeds limit of ${UPLOAD_MAX_SIZE / 1024 / 1024}MB`
      });
    }
  }
  
  res.status(500).json({
    error: 'Internal server error',
    message: error.message || 'An unexpected error occurred'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    message: 'Endpoint not found'
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Mock API Service running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV}`);
  console.log(`Auth Service: ${AUTH_SERVICE_URL}`);
  console.log(`Upload Max Size: ${UPLOAD_MAX_SIZE / 1024 / 1024}MB`);
  console.log(`Allowed File Types: ${ALLOWED_FILE_TYPES.join(', ')}`);
});

module.exports = app;
