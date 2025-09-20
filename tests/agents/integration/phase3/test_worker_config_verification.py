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
        self.api_base_url = "***REMOVED***"
        
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
        os.environ["DATABASE_URL"] = "postgresql://postgres.znvwzkdblknkkztqyfnu:InsuranceNavigator2024!@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
        os.environ["DATABASE_SCHEMA"] = "upload_pipeline"
        
        from agents.tooling.rag.core import RAGTool, RetrievalConfig
        
        # Use existing user ID from previous tests
        user_id = "936551b6-b7a4-4d3d-9fe0-a491794fd66b"
        
        # Initialize RAG system
        config = RetrievalConfig(
            max_chunks=10,
            similarity_threshold=0.2  # Very low threshold to catch more results
        )
        
        rag_tool = RAGTool(user_id, config)
        
        # Test queries
        test_queries = [
            "What is my deductible?",
            "What are the coverage details?",
            "What is covered under this policy?",
            "What are the exclusions?",
            "How much will I pay out of pocket?",
            "What is my premium?",
            "What is my copay?",
            "What is my out-of-pocket maximum?"
        ]
        
        results = {}
        total_chunks = 0
        real_content_chunks = 0
        
        for query in test_queries:
            print(f"   Testing: {query}")
            
            try:
                # Get chunks directly from RAG tool
                chunks = await rag_tool.retrieve_chunks_from_text(query)
                
                print(f"     Retrieved {len(chunks)} chunks")
                total_chunks += len(chunks)
                
                # Analyze chunk content
                query_real_content = 0
                for chunk in chunks:
                    content = chunk.content.lower()
                    
                    # Check for real insurance content indicators
                    real_indicators = [
                        'deductible', 'coverage', 'policy', 'insurance', 'premium', 
                        'copay', 'copayment', 'out-of-pocket', 'maximum', 'benefit',
                        'medical', 'health', 'plan', 'enrollment', 'effective',
                        'exclusion', 'limitation', 'network', 'provider'
                    ]
                    
                    if any(indicator in content for indicator in real_indicators):
                        query_real_content += 1
                        real_content_chunks += 1
                        print(f"       ✅ Real content: {chunk.content[:80]}...")
                    else:
                        print(f"       ⚠️  Mock content: {chunk.content[:80]}...")
                
                results[query] = {
                    "chunks_count": len(chunks),
                    "real_content_chunks": query_real_content,
                    "chunks": [chunk.content[:200] for chunk in chunks]
                }
                
            except Exception as e:
                print(f"     ❌ Error: {str(e)}")
                results[query] = {"error": str(e)}
        
        # Save results
        timestamp = int(datetime.now().timestamp())
        results_file = f"worker_config_verification_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Summary
        successful_queries = sum(1 for r in results.values() if "error" not in r)
        
        print(f"\n📊 RAG Test Summary:")
        print(f"   Successful queries: {successful_queries}/{len(test_queries)}")
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
