#!/usr/bin/env python3
"""
Test script for OpenAI service integration.
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.external.service_router import ServiceRouter
from shared.config.worker_config import WorkerConfig

async def test_openai_integration():
    """Test OpenAI service integration."""
    try:
        print("Testing OpenAI service integration...")
        
        # Load configuration
        config = WorkerConfig.from_environment()
        print(f"✓ Configuration loaded successfully")
        
        # Create service router
        service_router_config = config.get_service_router_config()
        print(f"✓ Service router config created")
        
        router = ServiceRouter(service_router_config)
        print(f"✓ Service router created successfully")
        
        # Test OpenAI service access
        print("\nTesting OpenAI service access...")
        service = await router.get_service('openai')
        print(f"✓ Service retrieved: {type(service).__name__}")
        
        # Check service availability
        is_available = await service.is_available()
        print(f"✓ Service available: {is_available}")
        
        # Test health check
        health = await service.get_health()
        print(f"✓ Health check: {health}")
        
        # Test embedding generation (with a small test)
        print("\nTesting embedding generation...")
        test_texts = ["Hello world", "Test embedding"]
        
        if hasattr(service, 'generate_embeddings'):
            embeddings = await service.generate_embeddings(test_texts)
            print(f"✓ Embeddings generated: {len(embeddings)} vectors")
            if embeddings:
                print(f"✓ Vector dimension: {len(embeddings[0])}")
        elif hasattr(service, 'create_embeddings'):
            response = await service.create_embeddings(test_texts)
            print(f"✓ Embeddings created: {len(response.data)} vectors")
            if response.data:
                print(f"✓ Vector dimension: {len(response.data[0]['embedding'])}")
        else:
            print("⚠ Service doesn't have expected embedding methods")
        
        print("\n✅ OpenAI service integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ OpenAI service integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_integration())
    sys.exit(0 if success else 1)
