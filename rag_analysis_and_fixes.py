#!/usr/bin/env python3
"""
RAG Analysis and Fixes
Analyze RAG similarity histogram and fix configuration issues.
"""

import asyncio
import os
from dotenv import load_dotenv
from agents.tooling.rag.core import RAGTool, RetrievalConfig
from typing import List, Dict, Any

async def analyze_rag_similarity():
    """Analyze RAG similarity scores and provide recommendations."""
    
    # Load production environment
    load_dotenv('.env.production')
    
    print("🔍 RAG SIMILARITY ANALYSIS")
    print("=" * 50)
    
    # Test with the user from the frontend
    user_id = 'b4b0c962-fd49-49b8-993b-4b14c8edc37b'
    
    # Test with very low threshold to see all similarities
    config = RetrievalConfig(similarity_threshold=0.01, max_chunks=50)
    rag_tool = RAGTool(user_id, config)
    
    # Test queries
    queries = [
        "What is my deductible?",
        "Medicare Part B coverage",
        "annual deductible",
        "coverage details",
        "preventive services"
    ]
    
    all_similarities = []
    
    for query in queries:
        print(f"\n📝 Query: '{query}'")
        chunks = await rag_tool.retrieve_chunks_from_text(query)
        
        if chunks:
            similarities = [chunk.similarity for chunk in chunks if chunk.similarity is not None]
            all_similarities.extend(similarities)
            
            print(f"   Chunks found: {len(chunks)}")
            print(f"   Similarity range: {min(similarities):.4f} - {max(similarities):.4f}")
            print(f"   Average similarity: {sum(similarities)/len(similarities):.4f}")
            
            # Show top chunk content
            if chunks:
                top_chunk = chunks[0]
                print(f"   Top chunk: {top_chunk.content[:100]}...")
        else:
            print("   No chunks found")
    
    # Overall analysis
    if all_similarities:
        print(f"\n📊 OVERALL SIMILARITY ANALYSIS")
        print(f"Total similarity scores: {len(all_similarities)}")
        print(f"Min similarity: {min(all_similarities):.4f}")
        print(f"Max similarity: {max(all_similarities):.4f}")
        print(f"Average similarity: {sum(all_similarities)/len(all_similarities):.4f}")
        
        # Histogram analysis
        print(f"\n📈 SIMILARITY HISTOGRAM")
        ranges = [
            (0.0, 0.1, "Very Low"),
            (0.1, 0.2, "Low"),
            (0.2, 0.3, "Below Average"),
            (0.3, 0.4, "Average"),
            (0.4, 0.5, "Above Average"),
            (0.5, 0.6, "Good"),
            (0.6, 0.7, "Very Good"),
            (0.7, 0.8, "Excellent"),
            (0.8, 0.9, "Outstanding"),
            (0.9, 1.0, "Perfect")
        ]
        
        for min_val, max_val, label in ranges:
            count = sum(1 for s in all_similarities if min_val <= s < max_val)
            percentage = (count / len(all_similarities)) * 100
            print(f"   {label:12} ({min_val:.1f}-{max_val:.1f}): {count:3d} scores ({percentage:5.1f}%)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        if max(all_similarities) < 0.3:
            print("   🚨 CRITICAL: All similarities are very low (< 0.3)")
            print("   📝 Action: Lower similarity threshold to 0.05-0.1")
            print("   📝 Action: Check if documents are being processed correctly")
        elif max(all_similarities) < 0.5:
            print("   ⚠️  WARNING: Similarities are low (< 0.5)")
            print("   📝 Action: Lower similarity threshold to 0.2-0.3")
        else:
            print("   ✅ Similarities look reasonable")
        
        # Current threshold analysis
        current_threshold = 0.7  # Default threshold
        chunks_above_threshold = sum(1 for s in all_similarities if s >= current_threshold)
        print(f"\n🎯 CURRENT THRESHOLD ANALYSIS")
        print(f"   Current threshold: {current_threshold}")
        print(f"   Chunks above threshold: {chunks_above_threshold} / {len(all_similarities)}")
        print(f"   Percentage above threshold: {(chunks_above_threshold/len(all_similarities)*100):.1f}%")
        
        if chunks_above_threshold == 0:
            print("   🚨 CRITICAL: No chunks above current threshold!")
            print("   📝 Action: Lower threshold to 0.1-0.2 for immediate results")
        elif chunks_above_threshold < len(all_similarities) * 0.1:
            print("   ⚠️  WARNING: Very few chunks above threshold")
            print("   📝 Action: Consider lowering threshold to 0.2-0.3")
    
    return all_similarities

async def check_external_apis():
    """Check if we're using external APIs or mock services."""
    
    print(f"\n🔌 EXTERNAL API USAGE CHECK")
    print("=" * 50)
    
    # Check OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print("✅ OpenAI API Key: Set")
    else:
        print("❌ OpenAI API Key: Not set")
    
    # Check database configuration
    database_url = os.getenv('DATABASE_URL')
    if database_url and 'supabase' in database_url:
        print("✅ Database: Using production Supabase")
    else:
        print("❌ Database: Not using production Supabase")
    
    # Check for mock usage in configuration
    mock_usage = []
    
    # Check worker configuration
    try:
        from backend.shared.config.worker_config import WorkerConfig
        config = WorkerConfig.from_env()
        if hasattr(config, 'use_mock_storage') and config.use_mock_storage:
            mock_usage.append("Worker storage using mock")
    except:
        pass
    
    # Check upload pipeline configuration
    try:
        from api.upload_pipeline.config import UploadPipelineConfig
        config = UploadPipelineConfig.from_env()
        if hasattr(config, 'storage_environment') and config.storage_environment == "mock":
            mock_usage.append("Upload pipeline using mock storage")
    except:
        pass
    
    if mock_usage:
        print("⚠️  MOCK USAGE DETECTED:")
        for usage in mock_usage:
            print(f"   - {usage}")
    else:
        print("✅ No mock usage detected in configuration")
    
    return mock_usage

async def main():
    """Main analysis function."""
    
    print("🚀 RAG SYSTEM ANALYSIS")
    print("=" * 50)
    
    # Analyze similarity scores
    similarities = await analyze_rag_similarity()
    
    # Check external API usage
    mock_usage = await check_external_apis()
    
    # Summary
    print(f"\n📋 SUMMARY")
    print("=" * 50)
    
    if similarities:
        max_sim = max(similarities)
        if max_sim < 0.3:
            print("🚨 CRITICAL ISSUES FOUND:")
            print("   1. Similarity scores are very low (< 0.3)")
            print("   2. RAG threshold (0.7) is too high")
            print("   3. No relevant content being retrieved")
        elif max_sim < 0.5:
            print("⚠️  WARNING ISSUES FOUND:")
            print("   1. Similarity scores are low (< 0.5)")
            print("   2. RAG threshold (0.7) is too high")
            print("   3. Limited relevant content being retrieved")
        else:
            print("✅ Similarity scores look reasonable")
    
    if mock_usage:
        print("⚠️  MOCK USAGE DETECTED:")
        for usage in mock_usage:
            print(f"   - {usage}")
    else:
        print("✅ Using external APIs correctly")
    
    print(f"\n🔧 IMMEDIATE ACTIONS NEEDED:")
    print("   1. Lower RAG similarity threshold to 0.1-0.2")
    print("   2. Verify document processing is working")
    print("   3. Check if mock services are being used")
    print("   4. Test with real insurance documents")

if __name__ == "__main__":
    asyncio.run(main())
