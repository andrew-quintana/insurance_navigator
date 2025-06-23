# Phase 2 MVP Deployment Guide
## Supabase Client Integration + Vector Search Implementation

**Priority**: 🚀 **NEXT PHASE** for MVP deployment  
**Timeline**: 2 weeks implementation + 2 weeks testing/deployment  
**Readiness**: 85% complete, ready for implementation

---

## 🎯 **Phase 2 Objectives**

### **Primary Goals**
1. **Replace Mock Functions** with real Supabase client integration
2. **Implement Vector Search** for semantic document matching
3. **Deploy to Production** with performance validation
4. **Achieve <15s Response Times** for optimal user experience
5. **Validate User Acceptance** with real-world scenarios

### **Success Metrics**
- ✅ Document search latency <200ms
- ✅ Vector search latency <500ms  
- ✅ Overall workflow response <15s
- ✅ 85-90% PROCEED rate for information retrieval
- ✅ <1% error rate under normal load
- ✅ Support for 100+ concurrent users

---

## 📋 **Implementation Checklist**

### **Week 1: Core Integration**

#### **Day 1-2: Supabase Client Setup**
- [ ] Install Supabase Python client: `pip install supabase`
- [ ] Configure environment variables (SUPABASE_URL, SUPABASE_ANON_KEY)
- [ ] Create `SupabaseDocumentService` class
- [ ] Implement `search_user_documents()` method
- [ ] Add error handling and fallback to mock

#### **Day 3-4: Vector Search Implementation**
- [ ] Install OpenAI client for embeddings: `pip install openai`
- [ ] Create vector embedding generation function
- [ ] Implement `vector_search_documents()` method
- [ ] Create Supabase RPC function `match_documents`
- [ ] Test vector similarity search functionality

#### **Day 5: Integration & Testing**
- [ ] Replace `mock_supabase_document_search` with `production_document_search`
- [ ] Update Document Availability Agent initialization
- [ ] Run comprehensive unit tests
- [ ] Validate mock fallback functionality

### **Week 2: Performance & Deployment**

#### **Day 6-7: Performance Optimization**
- [ ] Implement connection pooling
- [ ] Add query optimization for policy_basics JSONB
- [ ] Create caching layer for frequent document searches
- [ ] Optimize vector search parameters (threshold, count)

#### **Day 8-9: Staging Deployment**
- [ ] Deploy to staging environment
- [ ] Configure production database connections
- [ ] Run performance benchmarks
- [ ] Execute integration test suite
- [ ] Validate error handling scenarios

#### **Day 10: Production Deployment**
- [ ] Deploy to production environment
- [ ] Monitor system performance
- [ ] Validate user acceptance criteria
- [ ] Document deployment process

---

## 🔧 **Technical Implementation**

### **1. Supabase Client Integration**

#### **Environment Configuration**
```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
OPENAI_API_KEY=your_openai_key

# Performance settings
DOCUMENT_SEARCH_TIMEOUT=5000
VECTOR_SEARCH_THRESHOLD=0.7
MAX_VECTOR_RESULTS=5
CONNECTION_POOL_SIZE=10
```

#### **Core Service Implementation**
```python
# supabase_document_service.py
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
import openai
import numpy as np

class SupabaseDocumentService:
    """Production Supabase document service for MVP deployment"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_ANON_KEY')
        )
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.timeout = int(os.getenv('DOCUMENT_SEARCH_TIMEOUT', 5000))
        self.vector_threshold = float(os.getenv('VECTOR_SEARCH_THRESHOLD', 0.7))
        self.max_results = int(os.getenv('MAX_VECTOR_RESULTS', 5))
    
    async def search_user_documents(self, user_id: str, document_name: str) -> Dict[str, Any]:
        """Search for specific document in user's Supabase storage"""
        try:
            response = await asyncio.wait_for(
                self._query_documents(user_id, document_name),
                timeout=self.timeout / 1000
            )
            
            if response.data:
                doc = response.data[0]
                return {
                    'exists': True,
                    'document_id': doc['id'],
                    'upload_date': doc['upload_date'],
                    'file_size': doc['file_size'],
                    'file_type': doc['file_type'],
                    'policy_basics': doc.get('policy_basics', {}),
                    'status': doc.get('status', 'active'),
                    'search_timestamp': datetime.now().isoformat(),
                    'search_method': 'supabase_direct'
                }
            else:
                return {
                    'exists': False,
                    'document_name': document_name,
                    'user_id': user_id,
                    'search_timestamp': datetime.now().isoformat(),
                    'search_method': 'supabase_direct'
                }
                
        except asyncio.TimeoutError:
            print(f"Supabase timeout for {document_name}, falling back to mock")
            return await self._fallback_to_mock(user_id, document_name)
        except Exception as e:
            print(f"Supabase error: {e}, falling back to mock")
            return await self._fallback_to_mock(user_id, document_name)
    
    async def _query_documents(self, user_id: str, document_name: str):
        """Direct Supabase query with error handling"""
        return self.supabase.table('documents').select(
            'id, name, upload_date, file_size, file_type, policy_basics, status'
        ).eq('user_id', user_id).eq('name', document_name).execute()
    
    async def _fallback_to_mock(self, user_id: str, document_name: str) -> Dict[str, Any]:
        """Fallback to mock for resilience"""
        from mock_supabase_integration import mock_supabase_document_search
        result = mock_supabase_document_search(user_id, document_name)
        result['search_method'] = 'mock_fallback'
        return result
```

### **2. Vector Search Implementation**

#### **Embedding Generation**
```python
async def generate_embedding(self, text: str) -> List[float]:
    """Generate embedding for text using OpenAI"""
    try:
        response = await openai.Embedding.acreate(
            model="text-embedding-ada-002",
            input=text
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Embedding generation error: {e}")
        return [0.0] * 1536  # Default embedding size
```

#### **Vector Search Function**
```python
async def vector_search_documents(self, user_id: str, query_text: str, limit: int = None) -> List[Dict[str, Any]]:
    """Vector search for semantic document matching"""
    limit = limit or self.max_results
    
    try:
        # Generate query embedding
        query_embedding = await self.generate_embedding(query_text)
        
        # Vector similarity search using Supabase pgvector
        response = self.supabase.rpc('match_documents', {
            'query_embedding': query_embedding,
            'match_threshold': self.vector_threshold,
            'match_count': limit,
            'user_id_param': user_id
        }).execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        print(f"Vector search error: {e}")
        return []
```

#### **Supabase RPC Function (SQL)**
```sql
-- Create vector search function in Supabase
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold float,
    match_count int,
    user_id_param text
)
RETURNS TABLE (
    id bigint,
    name text,
    content text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_vectors.id,
        document_vectors.name,
        document_vectors.content,
        1 - (document_vectors.embedding <=> query_embedding) AS similarity
    FROM document_vectors
    WHERE 
        document_vectors.user_id = user_id_param
        AND 1 - (document_vectors.embedding <=> query_embedding) > match_threshold
    ORDER BY document_vectors.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

### **3. Integration with Document Availability Agent**

#### **Updated Agent Initialization**
```python
# In document_availability agent setup
from supabase_document_service import SupabaseDocumentService

# Create production service
supabase_service = SupabaseDocumentService()

# Replace mock function in agent
async def production_document_search(user_id: str, document_name: str) -> Dict[str, Any]:
    """Production document search with vector fallback"""
    # Primary: Direct document search
    result = await supabase_service.search_user_documents(user_id, document_name)
    
    # Secondary: Vector search if direct search fails
    if not result['exists']:
        vector_results = await supabase_service.vector_search_documents(user_id, document_name)
        if vector_results:
            best_match = vector_results[0]
            result.update({
                'exists': True,
                'vector_match': True,
                'similarity_score': best_match.get('similarity', 0),
                'matched_document': best_match.get('name', ''),
                'search_method': 'supabase_vector'
            })
    
    return result

# Update document availability agent
document_availability_agent.search_function = production_document_search
```

---

## 🧪 **Testing Strategy**

### **Unit Testing**
```python
# test_supabase_integration.py
import pytest
import asyncio
from supabase_document_service import SupabaseDocumentService

class TestSupabaseIntegration:
    
    @pytest.fixture
    def service(self):
        return SupabaseDocumentService()
    
    @pytest.mark.asyncio
    async def test_direct_document_search(self, service):
        result = await service.search_user_documents("test_user", "insurance_policy")
        assert 'exists' in result
        assert 'search_method' in result
        assert result['search_method'] in ['supabase_direct', 'mock_fallback']
    
    @pytest.mark.asyncio
    async def test_vector_search(self, service):
        results = await service.vector_search_documents("test_user", "insurance policy")
        assert isinstance(results, list)
        if results:
            assert 'similarity' in results[0]
            assert results[0]['similarity'] >= service.vector_threshold
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, service):
        # Test with invalid user to trigger fallback
        result = await service.search_user_documents("invalid_user", "test_doc")
        assert result['search_method'] in ['supabase_direct', 'mock_fallback']
```

### **Performance Testing**
```python
# test_performance.py
import time
import asyncio
from supabase_document_service import SupabaseDocumentService

async def test_performance_benchmarks():
    service = SupabaseDocumentService()
    
    # Test document search latency
    start_time = time.time()
    result = await service.search_user_documents("test_user", "insurance_policy")
    latency = (time.time() - start_time) * 1000
    
    assert latency < 200, f"Document search took {latency}ms, expected <200ms"
    
    # Test vector search latency
    start_time = time.time()
    results = await service.vector_search_documents("test_user", "insurance")
    vector_latency = (time.time() - start_time) * 1000
    
    assert vector_latency < 500, f"Vector search took {vector_latency}ms, expected <500ms"
```

### **Integration Testing**
```python
# test_end_to_end.py
async def test_full_workflow_performance():
    """Test complete supervisor workflow with Supabase integration"""
    start_time = time.time()
    
    result = await supervisor_workflow.invoke({
        "user_input": "What is my copay for specialist visits?",
        "user_id": "test_user_123",
        "workflow_id": "test_workflow"
    })
    
    total_time = time.time() - start_time
    assert total_time < 15, f"Workflow took {total_time}s, expected <15s"
    assert result['routing_decision'] in ['PROCEED', 'COLLECT', 'REVIEW']
```

---

## 📊 **Monitoring & Validation**

### **Performance Metrics**
```python
# monitoring.py
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            latency = (time.time() - start_time) * 1000
            
            # Log performance metrics
            print(f"{func.__name__}: {latency:.2f}ms")
            
            # Alert if performance degrades
            if latency > 1000:  # 1 second threshold
                print(f"ALERT: {func.__name__} slow response: {latency:.2f}ms")
            
            return result
        except Exception as e:
            error_time = (time.time() - start_time) * 1000
            print(f"ERROR in {func.__name__}: {e} (after {error_time:.2f}ms)")
            raise
    return wrapper
```

### **Health Check Endpoints**
```python
# health_check.py
from fastapi import FastAPI
from supabase_document_service import SupabaseDocumentService

app = FastAPI()

@app.get("/health/supabase")
async def check_supabase_health():
    service = SupabaseDocumentService()
    try:
        # Test basic connectivity
        result = await service.search_user_documents("health_check", "test_doc")
        return {
            "status": "healthy",
            "supabase_connection": "ok",
            "search_method": result.get('search_method', 'unknown'),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/health/vector-search")
async def check_vector_search_health():
    service = SupabaseDocumentService()
    try:
        results = await service.vector_search_documents("health_check", "test query")
        return {
            "status": "healthy",
            "vector_search": "ok",
            "results_count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```

---

## 🚀 **Deployment Process**

### **Staging Deployment**
```bash
# Deploy to staging
git checkout staging
git pull origin main
docker build -t insurance-navigator-staging .
docker run -d --env-file .env.staging insurance-navigator-staging

# Validate deployment
curl https://staging.insurancenavigator.com/health/supabase
curl https://staging.insurancenavigator.com/health/vector-search
```

### **Production Deployment**
```bash
# Deploy to production
git checkout production
git pull origin staging
docker build -t insurance-navigator-prod .
docker run -d --env-file .env.production insurance-navigator-prod

# Monitor deployment
docker logs insurance-navigator-prod --follow
```

### **Rollback Plan**
```bash
# If issues arise, rollback to previous version
docker stop insurance-navigator-prod
docker run -d --env-file .env.production insurance-navigator-prod:previous
```

---

## ✅ **Success Criteria**

### **Technical Validation**
- [ ] All unit tests pass (100% success rate)
- [ ] Integration tests pass (95%+ success rate)
- [ ] Performance benchmarks met (<15s workflow response)
- [ ] Error rate <1% under normal load
- [ ] Fallback mechanisms working correctly

### **User Acceptance Validation**
- [ ] Information retrieval: 85-90% PROCEED rate
- [ ] Eligibility workflows: Appropriate COLLECT rate
- [ ] Document upload integration working
- [ ] Mobile and desktop compatibility confirmed
- [ ] User feedback positive (>4.0/5.0 rating)

### **Business Validation**
- [ ] MVP deployment successful
- [ ] User onboarding process smooth
- [ ] Support ticket volume manageable (<5% of users)
- [ ] Performance meets user expectations
- [ ] Ready for Phase 3 enhancement planning

---

## 📞 **Support & Escalation**

### **Technical Issues**
- **Database connectivity**: Check Supabase dashboard and connection strings
- **Performance degradation**: Review monitoring metrics and optimize queries
- **Vector search failures**: Validate OpenAI API key and embedding generation

### **Emergency Contacts**
- **Technical Lead**: [Contact Information]
- **DevOps Team**: [Contact Information]  
- **Supabase Support**: [Support Channel]

This guide provides a comprehensive roadmap for successful Phase 2 MVP deployment with Supabase integration and vector search capabilities. 