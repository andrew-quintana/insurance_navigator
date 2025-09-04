const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const bodyParser = require('body-parser');
const helmet = require('helmet');

const app = express();
const PORT = process.env.PORT || 3001;
const JWT_SECRET = process.env.JWT_SECRET || 'test-secret-key-12345';

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  credentials: true
}));
app.use(bodyParser.json());

// In-memory storage for testing
const users = new Map();
const sessions = new Map();

// Helper functions
const generateTokens = (userId, email) => {
  const accessToken = jwt.sign(
    { userId, email, type: 'access' },
    JWT_SECRET,
    { expiresIn: '15m' }
  );
  
  const refreshToken = jwt.sign(
    { userId, email, type: 'refresh' },
    JWT_SECRET,
    { expiresIn: '7d' }
  );
  
  return { accessToken, refreshToken };
};

const verifyToken = (token) => {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (error) {
    return null;
  }
};

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy', service: 'mock-auth-service' });
});

// Supabase Auth API endpoints

// POST /auth/v1/signup - User registration
app.post('/auth/v1/signup', async (req, res) => {
  try {
    const { email, password } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'Email and password are required'
      });
    }
    
    if (users.has(email)) {
      return res.status(400).json({
        error: 'User already registered',
        message: 'Email already registered'
      });
    }
    
    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);
    
    // Create user
    const userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const user = {
      id: userId,
      email,
      password: hashedPassword,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    users.set(email, user);
    
    // Generate tokens
    const { accessToken, refreshToken } = generateTokens(userId, email);
    
    // Store session
    sessions.set(userId, {
      accessToken,
      refreshToken,
      userId,
      email,
      created_at: new Date().toISOString()
    });
    
    res.status(200).json({
      user: {
        id: userId,
        email,
        created_at: user.created_at,
        updated_at: user.updated_at
      },
      session: {
        access_token: accessToken,
        refresh_token: refreshToken,
        user_id: userId,
        expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString()
      }
    });
  } catch (error) {
    console.error('Signup error:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to create user'
    });
  }
});

// POST /auth/v1/token?grant_type=password - User login
app.post('/auth/v1/token', async (req, res) => {
  try {
    const { grant_type, email, password } = req.body;
    
    if (grant_type !== 'password') {
      return res.status(400).json({
        error: 'Invalid grant type',
        message: 'Only password grant type is supported'
      });
    }
    
    if (!email || !password) {
      return res.status(400).json({
        error: 'Missing required fields',
        message: 'Email and password are required'
      });
    }
    
    const user = users.get(email);
    if (!user) {
      return res.status(400).json({
        error: 'Invalid credentials',
        message: 'Invalid email or password'
      });
    }
    
    const isValidPassword = await bcrypt.compare(password, user.password);
    if (!isValidPassword) {
      return res.status(400).json({
        error: 'Invalid credentials',
        message: 'Invalid email or password'
      });
    }
    
    // Generate new tokens
    const { accessToken, refreshToken } = generateTokens(user.id, email);
    
    // Update session
    sessions.set(user.id, {
      accessToken,
      refreshToken,
      userId: user.id,
      email,
      created_at: new Date().toISOString()
    });
    
    res.status(200).json({
      access_token: accessToken,
      refresh_token: refreshToken,
      user_id: user.id,
      expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString()
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to authenticate user'
    });
  }
});

// POST /auth/v1/token?grant_type=refresh_token - Token refresh
app.post('/auth/v1/token', async (req, res) => {
  try {
    const { grant_type, refresh_token } = req.body;
    
    if (grant_type !== 'refresh_token') {
      return res.status(400).json({
        error: 'Invalid grant type',
        message: 'Only password and refresh_token grant types are supported'
      });
    }
    
    if (!refresh_token) {
      return res.status(400).json({
        error: 'Missing refresh token',
        message: 'Refresh token is required'
      });
    }
    
    const decoded = verifyToken(refresh_token);
    if (!decoded || decoded.type !== 'refresh') {
      return res.status(400).json({
        error: 'Invalid refresh token',
        message: 'Invalid or expired refresh token'
      });
    }
    
    const user = users.get(decoded.email);
    if (!user) {
      return res.status(400).json({
        error: 'User not found',
        message: 'User associated with refresh token not found'
      });
    }
    
    // Generate new tokens
    const { accessToken, newRefreshToken } = generateTokens(user.id, user.email);
    
    // Update session
    sessions.set(user.id, {
      accessToken,
      refreshToken: newRefreshToken,
      userId: user.id,
      email: user.email,
      created_at: new Date().toISOString()
    });
    
    res.status(200).json({
      access_token: accessToken,
      refresh_token: newRefreshToken,
      user_id: user.id,
      expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString()
    });
  } catch (error) {
    console.error('Token refresh error:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to refresh token'
    });
  }
});

// GET /auth/v1/user - Get current user
app.get('/auth/v1/user', (req, res) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        error: 'Missing authorization header',
        message: 'Authorization header with Bearer token is required'
      });
    }
    
    const token = authHeader.substring(7);
    const decoded = verifyToken(token);
    
    if (!decoded || decoded.type !== 'access') {
      return res.status(401).json({
        error: 'Invalid token',
        message: 'Invalid or expired access token'
      });
    }
    
    const user = users.get(decoded.email);
    if (!user) {
      return res.status(404).json({
        error: 'User not found',
        message: 'User not found'
      });
    }
    
    res.status(200).json({
      id: user.id,
      email: user.email,
      created_at: user.created_at,
      updated_at: user.updated_at
    });
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to get user'
    });
  }
});

// POST /auth/v1/logout - Sign out
app.post('/auth/v1/logout', (req, res) => {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        error: 'Missing authorization header',
        message: 'Authorization header with Bearer token is required'
      });
    }
    
    const token = authHeader.substring(7);
    const decoded = verifyToken(token);
    
    if (decoded && decoded.userId) {
      sessions.delete(decoded.userId);
    }
    
    res.status(200).json({
      message: 'Successfully logged out'
    });
  } catch (error) {
    console.error('Logout error:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to logout'
    });
  }
});

// Test endpoints for integration testing
app.get('/test/users', (req, res) => {
  const userList = Array.from(users.values()).map(user => ({
    id: user.id,
    email: user.email,
    created_at: user.created_at
  }));
  res.json(userList);
});

app.delete('/test/users', (req, res) => {
  users.clear();
  sessions.clear();
  res.json({ message: 'All test users cleared' });
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  res.status(500).json({
    error: 'Internal server error',
    message: 'An unexpected error occurred'
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
  console.log(`Mock Auth Service running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV}`);
  console.log(`JWT Secret: ${JWT_SECRET.substring(0, 10)}...`);
});

module.exports = app;
