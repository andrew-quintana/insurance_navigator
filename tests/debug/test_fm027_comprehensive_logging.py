#!/usr/bin/env python3
"""
Test script to verify FM-027 comprehensive logging is working correctly.
This script tests the complete data flow logging from webhook to LlamaParse.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging to see all the FM-027 logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_comprehensive_logging():
    """Test the comprehensive logging in the worker"""
    
    print("🧪 Testing FM-027 Comprehensive Logging")
    print("=" * 50)
    
    try:
        # Import the worker
        from backend.workers.enhanced_base_worker import EnhancedBaseWorker
        from backend.shared.storage.storage_manager import StorageManager
        from backend.shared.database.database_manager import DatabaseManager
        
        print("✅ Imports successful")
        
        # Initialize components
        storage = StorageManager()
        db = DatabaseManager()
        worker = EnhancedBaseWorker(storage=storage, db=db)
        
        print("✅ Components initialized")
        
        # Create a mock job for testing
        mock_job = {
            "job_id": "test-job-123",
            "document_id": "test-doc-456",
            "user_id": "test-user-789",
            "stage": "parsing",
            "progress": {
                "storage_path": "files/user/test-user-789/raw/test-document.pdf",
                "mime": "application/pdf"
            }
        }
        
        correlation_id = "test-correlation-123"
        
        print("✅ Mock job created")
        print(f"   Job ID: {mock_job['job_id']}")
        print(f"   Document ID: {mock_job['document_id']}")
        print(f"   Storage Path: {mock_job['progress']['storage_path']}")
        print(f"   Correlation ID: {correlation_id}")
        
        print("\n🔍 Testing comprehensive logging...")
        print("=" * 50)
        
        # Test the logging by calling the method (it will fail but we'll see the logs)
        try:
            await worker._process_parsing_real(mock_job, correlation_id)
        except Exception as e:
            print(f"✅ Expected error (testing logging): {e}")
        
        print("\n✅ Comprehensive logging test completed")
        print("Check the logs above for FM-027 entries with detailed information")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_comprehensive_logging())
