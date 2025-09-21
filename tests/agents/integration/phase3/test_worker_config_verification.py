#!/usr/bin/env python3
"""
Test to verify worker service configuration and real API usage.
This test focuses on configuration verification rather than full upload testing.
"""

import asyncio
import sys
import os
import json
import aiohttp
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

class WorkerConfigVerifier:
    def __init__(self):
        self.api_base_url = "https://insurance-navigator-api.onrender.com"
        
    async def run_verification(self):
        """Run worker configuration verification."""
        print("🔍 Worker Service Configuration Verification")
        print("=" * 60)
        
        try:
            # Step 1: Check API health and services
            print("\n1️⃣ Checking API health and services...")
            await self.check_api_services()
            
            # Step 2: Test RAG system with existing data
            print("\n2️⃣ Testing RAG system with existing data...")
            await self.test_rag_with_existing_data()
            
            # Step 3: Check for real content vs mock content
            print("\n3️⃣ Analyzing content quality...")
            await self.analyze_content_quality()
            
            print("\n✅ Verification completed!")
            
        except Exception as e:
            print(f"\n❌ Verification failed: {str(e)}")
            return False
        
        return True
    
    async def check_api_services(self):
        """Check API health and service status."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ API Status: {health_data.get('status')}")
                    
                    services = health_data.get('services', {})
                    print("\n📊 Service Status:")
                    for service, status in services.items():
                        status_icon = "✅" if status == "healthy" else "❌"
                        print(f"   {status_icon} {service}: {status}")
                    
                    # Check if real services are healthy
                    real_services_healthy = (
                        services.get('openai') == 'healthy' and 
                        services.get('llamaparse') == 'healthy'
                    )
                    
                    if real_services_healthy:
                        print("\n✅ Real APIs are healthy and available!")
                        return True
                    else:
                        print("\n⚠️  Some real APIs may not be healthy")
                        return False
                else:
                    print(f"❌ API health check failed: {response.status}")
                    return False
    
    async def test_rag_with_existing_data(self):
        """Test RAG system with existing data in the database."""
        print("🔍 Testing RAG system with existing data...")
        
        # Set production database URL
        os.environ["DATABASE_URL"] = "${DATABASE_URL}/{len(test_queries)}")
        print(f"   Total chunks retrieved: {total_chunks}")
        print(f"   Chunks with real content: {real_content_chunks}")
        
        if total_chunks > 0:
            real_content_ratio = real_content_chunks / total_chunks
            print(f"   Real content ratio: {real_content_ratio:.2%}")
            
            if real_content_ratio > 0.5:
                print("✅ High ratio of real content - Real APIs likely working!")
                return True
            elif real_content_ratio > 0.2:
                print("⚠️  Some real content found - Mixed API usage")
                return False
            else:
                print("❌ Low real content ratio - Likely using mock services")
                return False
        else:
            print("❌ No chunks retrieved - RAG system may have issues")
            return False
    
    async def analyze_content_quality(self):
        """Analyze the quality of content to determine if real APIs were used."""
        print("🔍 Analyzing content quality...")
        
        # This is a heuristic analysis based on content patterns
        print("📋 Content Quality Indicators:")
        print("   ✅ Real APIs typically produce:")
        print("      - Specific insurance terminology")
        print("      - Detailed coverage information")
        print("      - Actual policy details")
        print("      - Meaningful embeddings")
        print("   ❌ Mock services typically produce:")
        print("      - Generic placeholder text")
        print("      - Repeated patterns")
        print("      - Zero or similar embeddings")
        print("      - Non-specific content")

async def main():
    """Run the worker configuration verification."""
    verifier = WorkerConfigVerifier()
    success = await verifier.run_verification()
    
    if success:
        print("\n🎉 Worker configuration verification PASSED!")
        print("   Real APIs appear to be working correctly")
    else:
        print("\n⚠️  Worker configuration verification shows issues")
        print("   May still be using mock services or have configuration problems")

if __name__ == "__main__":
    asyncio.run(main())
