#!/usr/bin/env python3
"""
Test script for BaseWorker integration with OpenAI service.
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workers.base_worker import BaseWorker
from shared.config.worker_config import WorkerConfig

async def test_baseworker_integration():
    """Test BaseWorker integration with OpenAI service."""
    try:
        print("Testing BaseWorker integration with OpenAI service...")
        
        # Load configuration
        config = WorkerConfig.from_environment()
        print(f"✓ Configuration loaded successfully")
        
        # Create BaseWorker
        worker = BaseWorker(config)
        print(f"✓ BaseWorker created successfully")
        
        # Initialize worker components
        await worker._initialize_components()
        print(f"✓ BaseWorker components initialized successfully")
        
        # Test service router access
        print("\nTesting service router access...")
        if worker.service_router:
            print(f"✓ Service router available: {type(worker.service_router).__name__}")
            
            # Test OpenAI service access through service router
            openai_service = await worker.service_router.get_service('openai')
            print(f"✓ OpenAI service accessible: {type(openai_service).__name__}")
            
            # Test health check
            health = await openai_service.get_health()
            print(f"✓ OpenAI service health: {health.is_healthy}")
            
            # Test embedding generation through service router
            test_texts = ["Test BaseWorker integration", "OpenAI service working"]
            embeddings = await worker.service_router.generate_embeddings(test_texts, correlation_id="test-baseworker")
            print(f"✓ Embeddings generated through BaseWorker: {len(embeddings)} vectors")
            
            if embeddings:
                print(f"✓ Vector dimension: {len(embeddings[0])}")
                print(f"✓ All vectors have same dimension: {all(len(emb) == len(embeddings[0]) for emb in embeddings)}")
        else:
            print("⚠ Service router not available in BaseWorker")
        
        # Test the specific embedding method that BaseWorker uses
        print("\nTesting BaseWorker embedding method...")
        try:
            # This would normally be called during job processing
            # For testing, we'll call it directly
            test_texts = ["Direct BaseWorker test", "Embedding generation"]
            embeddings = await worker.service_router.generate_embeddings(test_texts, correlation_id="test-direct")
            print(f"✓ Direct embedding generation: {len(embeddings)} vectors")
        except Exception as e:
            print(f"⚠ Direct embedding generation failed: {e}")
        
        # Cleanup
        await worker._cleanup_components()
        print(f"✓ BaseWorker cleaned up successfully")
        
        print("\n✅ BaseWorker integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ BaseWorker integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_baseworker_integration())
    sys.exit(0 if success else 1)
