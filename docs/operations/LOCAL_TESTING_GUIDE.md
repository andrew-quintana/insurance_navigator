# Local Testing Guide for Authentication Service

## 🎯 **Overview**

This guide shows how to test local modifications before deploying to Render, ensuring your changes work correctly in a local environment that mirrors production.

## 🚀 **Method 1: Local Development Server (Recommended)**

### **Step 1: Start Local API Server**

```bash
# Navigate to project directory
cd /Users/aq_home/1Projects/accessa/insurance_navigator

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start the local API server
python main.py
```

**Expected Output:**
```
INFO:main:🚀 Starting Insurance Navigator API v3.0.0
INFO:main:🔧 Backend-orchestrated processing enabled
INFO:main:🔄 Service initialization starting...
INFO:main:✅ Database pool initialized
INFO:main:✅ User service initialized
INFO:main:✅ Conversation service initialized
INFO:main:✅ Storage service initialized
INFO:main:✅ Core services initialized
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### **Step 2: Test Local API Endpoints**

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test registration with validation
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "ValidPass123!",
    "name": "Test User"
  }'

# Test invalid email (should fail with validation)
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email",
    "password": "ValidPass123!",
    "name": "Test User"
  }'
```

### **Step 3: Run Comprehensive Tests**

```bash
# Run the authentication test script against local server
python3 -c "
import requests
import json
import time

print('🔐 Testing Local Authentication Service')
print('=' * 45)

LOCAL_API_URL = 'http://localhost:8000'

# Test 1: Valid Registration
print('\\n1. Testing Valid Registration')
try:
    response = requests.post(f'{LOCAL_API_URL}/register', 
                           json={'email': f'valid-{int(time.time())}@example.com', 'password': 'ValidPass123!', 'name': 'Valid User'},
                           timeout=10)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        print('✅ Valid registration successful')
    else:
        print(f'❌ Registration failed: {response.text}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 2: Invalid Email Format
print('\\n2. Testing Invalid Email Format')
try:
    response = requests.post(f'{LOCAL_API_URL}/register', 
                           json={'email': 'invalid-email', 'password': 'ValidPass123!', 'name': 'Test User'},
                           timeout=10)
    print(f'Status: {response.status_code}')
    if response.status_code == 400:
        print('✅ Invalid email properly rejected')
    else:
        print(f'❌ Should have failed: {response.text}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test 3: Weak Password
print('\\n3. Testing Weak Password')
try:
    response = requests.post(f'{LOCAL_API_URL}/register', 
                           json={'email': f'weak-{int(time.time())}@example.com', 'password': '123', 'name': 'Test User'},
                           timeout=10)
    print(f'Status: {response.status_code}')
    if response.status_code == 400:
        print('✅ Weak password properly rejected')
    else:
        print(f'❌ Should have failed: {response.text}')
except Exception as e:
    print(f'❌ Error: {e}')

print('\\n' + '=' * 45)
print('Local Testing Complete')
"
```

## 🐳 **Method 2: Docker Local Testing**

### **Step 1: Build and Run with Docker**

```bash
# Build the Docker image
docker build -t insurance-navigator-local .

# Run the container with environment variables
docker run -p 8000:8000 \
  -e SUPABASE_URL="your_supabase_url" \
  -e SUPABASE_SERVICE_ROLE_KEY="your_service_key" \
  -e LLAMAPARSE_API_KEY="your_llamaparse_key" \
  -e OPENAI_API_KEY="your_openai_key" \
  insurance-navigator-local
```

### **Step 2: Test Docker Container**

```bash
# Test the containerized API
curl http://localhost:8000/health
```

## 🔧 **Method 3: Environment-Specific Testing**

### **Step 1: Create Local Environment File**

```bash
# Copy production environment for local testing
cp .env.production .env.local

# Edit .env.local to use local database if needed
# Or keep production database for testing
```

### **Step 2: Run with Local Environment**

```bash
# Load local environment and run
source .env.local
python main.py
```

## 📊 **Method 4: Automated Testing Script**

Create a comprehensive test script:

```python
# test_local_auth.py
import requests
import json
import time
import sys

def test_local_authentication():
    """Test local authentication service with validation"""
    
    LOCAL_API_URL = 'http://localhost:8000'
    
    print('🔐 Local Authentication Service Testing')
    print('=' * 50)
    
    # Test cases
    test_cases = [
        {
            'name': 'Valid Registration',
            'data': {'email': f'valid-{int(time.time())}@example.com', 'password': 'ValidPass123!', 'name': 'Valid User'},
            'expected_status': 200,
            'should_succeed': True
        },
        {
            'name': 'Invalid Email Format',
            'data': {'email': 'invalid-email', 'password': 'ValidPass123!', 'name': 'Test User'},
            'expected_status': 400,
            'should_succeed': False
        },
        {
            'name': 'Weak Password',
            'data': {'email': f'weak-{int(time.time())}@example.com', 'password': '123', 'name': 'Test User'},
            'expected_status': 400,
            'should_succeed': False
        },
        {
            'name': 'Missing Name',
            'data': {'email': f'missing-{int(time.time())}@example.com', 'password': 'ValidPass123!', 'name': ''},
            'expected_status': 400,
            'should_succeed': False
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f'\\n{test_case["name"]}')
        print('-' * 30)
        
        try:
            response = requests.post(f'{LOCAL_API_URL}/register', 
                                   json=test_case['data'], 
                                   timeout=10)
            
            success = (response.status_code == test_case['expected_status'])
            results.append(success)
            
            if success:
                print(f'✅ {test_case["name"]}: PASSED')
            else:
                print(f'❌ {test_case["name"]}: FAILED')
                print(f'   Expected: {test_case["expected_status"]}, Got: {response.status_code}')
                print(f'   Response: {response.text}')
                
        except Exception as e:
            print(f'❌ {test_case["name"]}: ERROR - {e}')
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print(f'\\n' + '=' * 50)
    print(f'Test Results: {passed}/{total} passed')
    
    if passed == total:
        print('🎉 All tests passed! Ready for deployment.')
        return True
    else:
        print('⚠️ Some tests failed. Fix issues before deploying.')
        return False

if __name__ == '__main__':
    success = test_local_authentication()
    sys.exit(0 if success else 1)
```

### **Run the Test Script**

```bash
python test_local_auth.py
```

## 🚀 **Method 5: Render Local Development**

### **Step 1: Use Render CLI for Local Development**

```bash
# Install Render CLI
npm install -g @render/cli

# Login to Render
render login

# Start local development server with Render environment
render dev
```

## 📋 **Testing Checklist**

Before deploying to Render, ensure:

- [ ] Local server starts without errors
- [ ] Health endpoint returns 200
- [ ] Valid registration works (200 status)
- [ ] Invalid email format rejected (400 status)
- [ ] Weak password rejected (400 status)
- [ ] Missing required fields rejected (400 status)
- [ ] Error messages are clear and helpful
- [ ] All validation rules work as expected

## 🔍 **Debugging Tips**

### **Check Logs**

```bash
# Monitor local server logs
tail -f logs/app.log

# Or run with verbose logging
python main.py --log-level DEBUG
```

### **Test Individual Components**

```bash
# Test validation service directly
python3 -c "
from db.services.auth_validation_service import auth_validation_service
result = auth_validation_service.validate_email('test@example.com')
print(result)
"
```

### **Verify Environment Variables**

```bash
# Check if environment variables are loaded
python3 -c "
import os
print('SUPABASE_URL:', os.getenv('SUPABASE_URL'))
print('SUPABASE_SERVICE_ROLE_KEY:', 'SET' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'NOT SET')
"
```

## 🎯 **Best Practices**

1. **Always test locally first** before deploying
2. **Use the same environment variables** as production
3. **Test all validation scenarios** thoroughly
4. **Check logs** for any errors or warnings
5. **Verify database connectivity** if using production DB
6. **Test with real data** similar to production usage

## 🚨 **Common Issues**

### **Issue: "Module not found" errors**
**Solution:** Ensure you're in the project directory and dependencies are installed

### **Issue: Database connection errors**
**Solution:** Check environment variables and database connectivity

### **Issue: Validation not working**
**Solution:** Verify the improved auth service is being imported correctly

### **Issue: Port already in use**
**Solution:** Kill existing processes or use a different port

---

*This guide ensures you can test all local modifications thoroughly before deploying to Render, preventing issues in production.*
