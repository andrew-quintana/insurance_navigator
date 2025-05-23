#!/usr/bin/env python3
"""
Regulatory Agent Integration Example

This script demonstrates how to integrate both mock and isolated regulatory agents
into your application with proper error handling and fallback patterns.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add core directory to path (bypass dependency conflicts)
core_path = os.path.join(os.path.dirname(__file__), 'core')
sys.path.insert(0, core_path)

# Import both agents
from mock_tools import create_mock_agent
from regulatory_isolated import create_isolated_regulatory_agent


def example_1_mock_agent():
    """Example 1: Using mock agent for testing/development."""
    print("📋 Example 1: Mock Agent (Zero Dependencies)")
    print("-" * 50)
    
    # Create mock agent - works immediately
    agent = create_mock_agent()
    
    # Test strategy
    strategy = "Implement Medicare Part D coverage for digital therapeutics"
    context = {
        "jurisdiction": "federal",
        "program": "Medicare",
        "focus_area": "digital health"
    }
    
    # Analyze (synchronous)
    result = agent.analyze_strategy(strategy, context)
    
    print(f"✅ Analysis completed in {result['processing_time_seconds']:.3f}s")
    print(f"📄 Sources found: {result['sources_found']}")
    print(f"💾 Documents cached: {result['documents_cached']}")
    print(f"🎭 Mock mode: {result.get('mock_mode', 'Unknown')}")
    
    # Show analysis preview
    analysis_lines = result['analysis'].split('\n')[:10]
    print(f"\n📝 Analysis Preview:")
    for line in analysis_lines:
        if line.strip():
            print(f"   {line}")
    
    return result


async def example_2_isolated_agent():
    """Example 2: Using isolated agent for production."""
    print(f"\n📋 Example 2: Isolated Agent (Production)")
    print("-" * 50)
    
    try:
        # Create isolated agent
        agent = create_isolated_regulatory_agent()
        
        # Show capabilities
        capabilities = agent.get_capabilities()
        print(f"🚀 Agent: {capabilities['agent_type']} v{capabilities['version']}")
        print(f"🔗 AI Integration: {capabilities['ai_integration']}")
        print(f"💾 Database: {capabilities['database_integration']}")
        print(f"☁️  Supabase: {capabilities['supabase_integration']}")
        
        # Test strategy
        strategy = "Establish Medicaid coverage pathway for AI-assisted diagnostics"
        context = {
            "jurisdiction": "CA",
            "program": "Medi-Cal",
            "timeline": "12 months"
        }
        
        # Analyze (asynchronous)
        result = await agent.analyze_strategy(strategy, context)
        
        print(f"\n✅ Analysis completed in {result['processing_time_seconds']:.2f}s")
        print(f"📄 Sources found: {result['sources_found']}")
        print(f"💾 Documents cached: {result['documents_cached']}")
        
        if result.get('cached_document_ids'):
            print(f"🗂️  Document IDs: {len(result['cached_document_ids'])} cached")
        
        # Show analysis preview
        analysis_lines = result['analysis'].split('\n')[:10]
        print(f"\n📝 Analysis Preview:")
        for line in analysis_lines:
            if line.strip():
                print(f"   {line}")
        
        return result
        
    except Exception as e:
        print(f"❌ Isolated agent error: {str(e)}")
        print("ℹ️  This may be due to missing environment variables or dependencies")
        return None


async def example_3_production_pattern():
    """Example 3: Production pattern with fallback."""
    print(f"\n📋 Example 3: Production Pattern with Fallback")
    print("-" * 50)
    
    strategy = "Medicare reimbursement for remote patient monitoring devices"
    context = {"jurisdiction": "federal", "program": "Medicare"}
    
    try:
        # Try production agent first
        print("🚀 Attempting production agent...")
        agent = create_isolated_regulatory_agent()
        result = await agent.analyze_strategy(strategy, context)
        
        print(f"✅ Production analysis successful!")
        print(f"⏱️  Time: {result['processing_time_seconds']:.2f}s")
        print(f"📄 Sources: {result['sources_found']}")
        
        return result
        
    except Exception as e:
        print(f"⚠️  Production agent failed: {str(e)}")
        print("🎭 Falling back to mock agent...")
        
        # Fallback to mock agent
        agent = create_mock_agent()
        result = agent.analyze_strategy(strategy, context)
        
        print(f"✅ Mock analysis successful!")
        print(f"⏱️  Time: {result['processing_time_seconds']:.3f}s")
        print(f"📄 Sources: {result['sources_found']}")
        print(f"🎭 Mode: Fallback (mock)")
        
        return result


def example_4_environment_detection():
    """Example 4: Environment-based agent selection."""
    print(f"\n📋 Example 4: Environment-Based Selection")
    print("-" * 50)
    
    def get_regulatory_agent():
        """Factory function that returns appropriate agent based on environment."""
        env = os.getenv('ENVIRONMENT', 'development').lower()
        
        if env == 'production':
            print("🚀 Production environment detected - using isolated agent")
            return create_isolated_regulatory_agent(), True  # async
        else:
            print("🎭 Development environment detected - using mock agent")
            return create_mock_agent(), False  # sync
    
    # Get appropriate agent
    agent, is_async = get_regulatory_agent()
    
    strategy = "Medicaid coverage for wearable health monitoring"
    context = {"jurisdiction": "federal", "program": "Medicaid"}
    
    if is_async:
        # Would need async wrapper in real application
        print("ℹ️  Would use async analysis in production")
        print(f"📊 Agent capabilities: {agent.get_capabilities()['features'][:3]}")
    else:
        # Synchronous analysis
        result = agent.analyze_strategy(strategy, context)
        print(f"✅ Analysis completed: {result['sources_found']} sources found")
    
    return agent


async def example_5_search_and_cache():
    """Example 5: Direct search and caching functionality."""
    print(f"\n📋 Example 5: Direct Search and Caching")
    print("-" * 50)
    
    try:
        agent = create_isolated_regulatory_agent()
        
        # Direct document search
        print("🔍 Searching regulatory documents...")
        search_results = await agent.search_regulatory_documents(
            query="Medicare Part B coverage guidelines",
            jurisdiction="federal",
            program="Medicare",
            max_results=3
        )
        
        print(f"📊 Found {search_results['total_results']} documents")
        print(f"⏱️  Search time: {search_results['processing_time_seconds']:.2f}s")
        
        for i, result in enumerate(search_results['results'][:2], 1):
            print(f"\n📄 Document {i}:")
            print(f"   Title: {result['title'][:60]}...")
            print(f"   Domain: {result['domain']}")
            print(f"   Type: {result['document_type']}")
            print(f"   Priority: {result['priority_score']:.2f}")
            
            # Extract content from first document
            if i == 1:
                print(f"   🔄 Extracting content...")
                content = await agent.extract_document_content(result['url'])
                if content.get('content'):
                    print(f"   📄 Content length: {len(content['content'])} chars")
                    print(f"   🛠️  Extraction: {content.get('extraction_method', 'unknown')}")
                
                # Cache the document
                doc_id = await agent.cache_document({**result, **content})
                print(f"   💾 Cached as: {doc_id}")
        
        return search_results
        
    except Exception as e:
        print(f"❌ Search example failed: {str(e)}")
        print("🎭 Using mock search instead...")
        
        # Fallback to mock search
        agent = create_mock_agent()
        search_results = agent.search_regulatory_documents(
            query="Medicare Part B coverage guidelines",
            jurisdiction="federal",
            program="Medicare",
            max_results=3
        )
        
        print(f"📊 Mock search found {search_results['total_results']} documents")
        return search_results


async def main():
    """Run all integration examples."""
    print("🚀 Regulatory Agent Integration Examples")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run examples
    example_1_mock_agent()
    await example_2_isolated_agent()
    await example_3_production_pattern()
    example_4_environment_detection()
    await example_5_search_and_cache()
    
    print(f"\n🎉 All examples completed!")
    print("=" * 60)
    print("ℹ️  Integration Tips:")
    print("   • Use mock agent for testing and development")
    print("   • Use isolated agent for production with proper environment setup")
    print("   • Always include fallback patterns for reliability")
    print("   • Check agent capabilities before using advanced features")
    print("   • Enable debug logging for troubleshooting")


if __name__ == "__main__":
    asyncio.run(main()) 