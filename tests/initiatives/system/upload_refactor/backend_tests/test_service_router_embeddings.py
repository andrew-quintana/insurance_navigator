#!/usr/bin/env python3
"""
Test script for service router embedding generation.
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.external.service_router import ServiceRouter
from shared.config.worker_config import WorkerConfig

async def test_service_router_embeddings():
    """Test service router embedding generation."""
    try:
        print("Testing service router embedding generation...")
        
        # Load configuration
        config = WorkerConfig.from_environment()
        print(f"✓ Configuration loaded successfully")
        
        # Create service router
        service_router_config = config.get_service_router_config()
        print(f"✓ Service router config created")
        
        router = ServiceRouter(service_router_config)
        print(f"✓ Service router created successfully")
        
        # Test embedding generation through service router
        print("\nTesting embedding generation through service router...")
        test_texts = ["Hello world", "Test embedding", "Another test"]
        
        embeddings = await router.generate_embeddings(test_texts, correlation_id="test-123")
        print(f"✓ Embeddings generated: {len(embeddings)} vectors")
        
        if embeddings:
            print(f"✓ Vector dimension: {len(embeddings[0])}")
            print(f"✓ All vectors have same dimension: {all(len(emb) == len(embeddings[0]) for emb in embeddings)}")
            
            # Check for valid vectors (no NaN or infinite values)
            import math
            has_nan = any(math.isnan(val) for emb in embeddings for val in emb)
            has_inf = any(math.isinf(val) for emb in embeddings for val in emb)
            print(f"✓ No NaN values: {not has_nan}")
            print(f"✓ No infinite values: {not has_inf}")
        
        # Test different service modes
        print("\nTesting different service modes...")
        
        # Test HYBRID mode (current)
        print(f"Current mode: {router.mode}")
        embeddings_hybrid = await router.generate_embeddings(["Test mode switching"], correlation_id="test-hybrid")
        print(f"✓ HYBRID mode embeddings: {len(embeddings_hybrid)}")
        
        # Test REAL mode
        from shared.external.service_router import ServiceMode
        router.set_mode(ServiceMode.REAL)
        print(f"Switched to mode: {router.mode}")
        embeddings_real = await router.generate_embeddings(["Test real mode"], correlation_id="test-real")
        print(f"✓ REAL mode embeddings: {len(embeddings_real)}")
        
        # Test MOCK mode
        router.set_mode(ServiceMode.MOCK)
        print(f"Switched to mode: {router.mode}")
        embeddings_mock = await router.generate_embeddings(["Test mock mode"], correlation_id="test-mock")
        print(f"✓ MOCK mode embeddings: {len(embeddings_mock)}")
        
        # Switch back to HYBRID
        router.set_mode(ServiceMode.HYBRID)
        print(f"Switched back to mode: {router.mode}")
        
        print("\n✅ Service router embedding generation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Service router embedding generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_service_router_embeddings())
    sys.exit(0 if success else 1)
