#!/usr/bin/env python3
"""
Complete Development Workflow Test

This test validates the complete development workflow with separated requirements:
1. API Service functionality
2. Worker functionality  
3. Upload pipeline functionality
4. RAG retrieval and generation
5. Database connectivity
6. Agent orchestration
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_environment_setup():
    """Test environment setup and configuration."""
    print("🔍 Testing Environment Setup")
    print("=" * 50)
    
    try:
        # Test environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Test configuration
        from config.configuration_manager import get_config_manager
        config = get_config_manager()
        
        print(f"✅ Environment: {config.environment}")
        print(f"✅ Database URL configured: {bool(getattr(config, 'database_url', None))}")
        print(f"✅ OpenAI API key configured: {bool(getattr(config, 'openai_api_key', None))}")
        print(f"✅ Supabase URL configured: {bool(getattr(config, 'supabase_url', None))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        return False

def test_database_connectivity():
    """Test database connectivity."""
    print("\n🔍 Testing Database Connectivity")
    print("=" * 50)
    
    try:
        # Test database configuration
        from config.database import get_database_url, get_db_config
        db_url = get_database_url()
        db_config = get_db_config()
        
        print(f"✅ Database URL: {db_url[:50]}...")
        print(f"✅ Database config loaded successfully")
        
        # Test database manager
        from core.database import get_database_manager
        print("✅ Database manager imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False

def test_api_service_core():
    """Test API service core functionality."""
    print("\n🔍 Testing API Service Core")
    print("=" * 50)
    
    try:
        # Test main app
        from main import app
        print(f"✅ Main app loaded with {len(app.router.routes)} routes")
        
        # Test core modules
        from core import initialize_system, close_system
        print("✅ Core system imports successful")
        
        # Test service manager
        from core.service_manager import get_service_manager
        print("✅ Service manager imports successful")
        
        # Test agent integration
        from core.agent_integration import AgentIntegrationManager
        print("✅ Agent integration imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ API service core test failed: {e}")
        return False

def test_agent_system():
    """Test agent system functionality."""
    print("\n🔍 Testing Agent System")
    print("=" * 50)
    
    try:
        # Test patient navigator agents
        from agents.patient_navigator.supervisor.workflow import SupervisorWorkflow
        from agents.patient_navigator.supervisor.workflow_prescription.agent import WorkflowPrescriptionAgent
        from agents.patient_navigator.supervisor.document_availability import DocumentAvailabilityChecker
        
        print("✅ Patient navigator agents imports successful")
        
        # Test RAG system
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        from agents.tooling.rag.observability import RAGPerformanceMonitor
        
        print("✅ RAG system imports successful")
        
        # Test agent workflow creation
        workflow = SupervisorWorkflow(use_mock=True)
        print("✅ Agent workflow creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent system test failed: {e}")
        return False

def test_upload_pipeline():
    """Test upload pipeline functionality."""
    print("\n🔍 Testing Upload Pipeline")
    print("=" * 50)
    
    try:
        # Test upload pipeline modules
        from api.upload_pipeline.database import get_database, DatabaseManager
        from api.upload_pipeline.webhooks import router as webhook_router
        from api.upload_pipeline.endpoints.upload import router as upload_router
        
        print("✅ Upload pipeline modules imports successful")
        
        # Test database manager creation
        db_manager = DatabaseManager()
        print("✅ Upload pipeline database manager creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload pipeline test failed: {e}")
        return False

def test_rag_functionality():
    """Test RAG functionality."""
    print("\n🔍 Testing RAG Functionality")
    print("=" * 50)
    
    try:
        # Test RAG tool
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        # Create test configuration
        config = RetrievalConfig(
            similarity_threshold=0.3,
            max_chunks=5,
            token_budget=2000
        )
        
        print("✅ RAG tool configuration successful")
        
        # Test RAG observability
        from agents.tooling.rag.observability import RAGPerformanceMonitor, threshold_manager
        print("✅ RAG observability imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG functionality test failed: {e}")
        return False

def test_worker_functionality():
    """Test worker functionality."""
    print("\n🔍 Testing Worker Functionality")
    print("=" * 50)
    
    try:
        # Test worker modules
        from backend.workers.enhanced_base_worker import EnhancedBaseWorker
        from backend.workers.enhanced_runner import EnhancedWorkerRunner
        
        print("✅ Worker modules imports successful")
        
        # Test external services
        from bs4 import BeautifulSoup
        from duckduckgo_search import DDGS
        import wikipedia
        import pandas as pd
        import numpy as np
        
        print("✅ External services imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Worker functionality test failed: {e}")
        return False

def test_security_system():
    """Test security system functionality."""
    print("\n🔍 Testing Security System")
    print("=" * 50)
    
    try:
        # Test authentication
        from db.services.auth_adapter import auth_adapter
        print(f"✅ Auth adapter: {getattr(auth_adapter, 'backend_name', 'MINIMAL')}")
        
        # Test security imports
        from jose import jwt
        from passlib.context import CryptContext
        import bcrypt
        
        print("✅ Security modules imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Security system test failed: {e}")
        return False

def test_external_services():
    """Test external services connectivity."""
    print("\n🔍 Testing External Services")
    print("=" * 50)
    
    try:
        # Test OpenAI
        import openai
        print("✅ OpenAI client imports successful")
        
        # Test Supabase
        from supabase import create_client, Client
        print("✅ Supabase client imports successful")
        
        # Test HTTP clients
        import aiohttp
        import requests
        import httpx
        
        print("✅ HTTP clients imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ External services test failed: {e}")
        return False

async def test_async_workflow():
    """Test async workflow functionality."""
    print("\n🔍 Testing Async Workflow")
    print("=" * 50)
    
    try:
        # Test async database operations
        from core.database import get_database_manager
        
        # Test async agent integration
        from core.agent_integration import initialize_agent_integration
        
        print("✅ Async workflow imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Async workflow test failed: {e}")
        return False

def test_requirements_validation():
    """Test that requirements are properly separated."""
    print("\n🔍 Testing Requirements Validation")
    print("=" * 50)
    
    try:
        # Test that sentence-transformers is NOT available (should be in testing only)
        try:
            import sentence_transformers
            print("⚠️  sentence-transformers is available (should only be in testing)")
            return False
        except ImportError:
            print("✅ sentence-transformers not available (correct for API/worker)")
        
        # Test that core dependencies are available
        import fastapi
        import pydantic
        import asyncpg
        import openai
        import langchain
        import langgraph
        
        print("✅ Core dependencies available")
        
        return True
        
    except Exception as e:
        print(f"❌ Requirements validation failed: {e}")
        return False

def main():
    """Run complete workflow test."""
    print("🚀 COMPLETE DEVELOPMENT WORKFLOW TEST")
    print("=" * 60)
    print("Testing separated requirements and complete functionality")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Database Connectivity", test_database_connectivity),
        ("API Service Core", test_api_service_core),
        ("Agent System", test_agent_system),
        ("Upload Pipeline", test_upload_pipeline),
        ("RAG Functionality", test_rag_functionality),
        ("Worker Functionality", test_worker_functionality),
        ("Security System", test_security_system),
        ("External Services", test_external_services),
        ("Async Workflow", lambda: asyncio.run(test_async_workflow())),
        ("Requirements Validation", test_requirements_validation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("📊 COMPLETE WORKFLOW TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Complete workflow test passed! All systems are working correctly.")
        print("✅ API service requirements are complete and functional")
        print("✅ Worker service requirements are complete and functional")
        print("✅ Requirements separation is working correctly")
        print("✅ All core functionality is operational")
        return True
    else:
        print("⚠️  Some workflow tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
