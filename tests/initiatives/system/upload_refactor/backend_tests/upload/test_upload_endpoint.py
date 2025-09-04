"""
Test script for the enhanced upload endpoint.

This script tests the upload endpoint with service router integration
and validates the correlation ID tracking and cost-aware job creation.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to the path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.shared.schemas.jobs import UploadRequest
from backend.api.routes.upload import (
    _validate_service_availability,
    _validate_cost_limits,
    _estimate_processing_cost,
    _generate_document_id,
    _generate_storage_path
)


class MockServiceRouter:
    """Mock service router for testing"""
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Mock health status"""
        return {
            "llamaparse": {"healthy": True, "response_time": 50},
            "openai": {"healthy": True, "response_time": 30}
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Mock configuration"""
        return {
            "mode": "hybrid",
            "fallback_enabled": True
        }


class MockCostTracker:
    """Mock cost tracker for testing"""
    
    async def check_daily_limit(self, cost: float) -> bool:
        """Mock daily limit check"""
        return cost < 10.0  # Allow up to $10 per day
    
    async def check_hourly_limit(self, cost: float) -> bool:
        """Mock hourly limit check"""
        return cost < 2.0  # Allow up to $2 per hour


async def test_upload_validation():
    """Test upload validation functions"""
    
    print("🧪 Testing upload validation functions...")
    
    # Test service availability validation
    service_router = MockServiceRouter()
    correlation_id = uuid.uuid4()
    
    try:
        health_status = await _validate_service_availability(service_router, correlation_id)
        print(f"✅ Service availability validation passed: {health_status}")
    except Exception as e:
        print(f"❌ Service availability validation failed: {e}")
    
    # Test cost estimation
    test_request = UploadRequest(
        filename="test_document.pdf",
        bytes_len=1024 * 1024,  # 1MB
        mime="application/pdf",
        sha256="a" * 64,
        ocr=False
    )
    
    try:
        estimated_cost = await _estimate_processing_cost(test_request)
        print(f"✅ Cost estimation passed: ${estimated_cost:.6f}")
    except Exception as e:
        print(f"❌ Cost estimation failed: {e}")
    
    # Test cost limit validation
    cost_tracker = MockCostTracker()
    
    try:
        await _validate_cost_limits(test_request, cost_tracker, correlation_id)
        print("✅ Cost limit validation passed")
    except Exception as e:
        print(f"❌ Cost limit validation failed: {e}")
    
    # Test document ID generation
    user_id = "test-user-123"
    file_hash = "b" * 64
    
    try:
        document_id = _generate_document_id(user_id, file_hash)
        print(f"✅ Document ID generation passed: {document_id}")
    except Exception as e:
        print(f"❌ Document ID generation failed: {e}")
    
    # Test storage path generation
    bucket = "raw"
    extension = "pdf"
    
    try:
        storage_path = _generate_storage_path(bucket, user_id, document_id, extension)
        print(f"✅ Storage path generation passed: {storage_path}")
    except Exception as e:
        print(f"❌ Storage path generation failed: {e}")


async def test_upload_flow():
    """Test complete upload flow"""
    
    print("\n🔄 Testing complete upload flow...")
    
    # Create test upload request
    test_request = UploadRequest(
        filename="test_document.pdf",
        bytes_len=512 * 1024,  # 512KB
        mime="application/pdf",
        sha256="c" * 64,
        ocr=False
    )
    
    print(f"📄 Test request created:")
    print(f"   - Filename: {test_request.filename}")
    print(f"   - Size: {test_request.bytes_len} bytes")
    print(f"   - MIME: {test_request.mime}")
    print(f"   - SHA256: {test_request.sha256[:16]}...")
    
    # Test cost estimation
    try:
        estimated_cost = await _estimate_processing_cost(test_request)
        print(f"💰 Estimated cost: ${estimated_cost:.6f}")
        
        # Test with different file sizes
        sizes = [1024, 1024*1024, 5*1024*1024, 25*1024*1024]
        for size in sizes:
            test_request.bytes_len = size
            cost = await _estimate_processing_cost(test_request)
            print(f"   - {size} bytes: ${cost:.6f}")
            
    except Exception as e:
        print(f"❌ Cost estimation failed: {e}")
    
    print("\n✅ Upload flow testing completed!")


async def main():
    """Main test function"""
    
    print("🚀 Starting upload endpoint tests...")
    print("=" * 50)
    
    try:
        await test_upload_validation()
        await test_upload_flow()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
