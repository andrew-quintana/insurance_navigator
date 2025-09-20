#!/usr/bin/env python3
"""
Test RAG system with the newly uploaded document from the worker logs.
This tests if the document was properly processed and stored in the database.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from agents.tooling.rag.core import RAGTool, RetrievalConfig
from agents.patient_navigator.information_retrieval.agent import InformationRetrievalAgent
from agents.patient_navigator.information_retrieval.models import InformationRetrievalInput

async def test_uploaded_document_rag():
    """Test RAG system with the document that was just uploaded and processed."""
    
    print("🔍 Testing RAG System with Newly Uploaded Document")
    print("=" * 60)
    
    # Set production database URL
    os.environ["DATABASE_URL"] = "postgresql://postgres.znvwzkdblknkkztqyfnu:InsuranceNavigator2024!@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    os.environ["DATABASE_SCHEMA"] = "upload_pipeline"
    
    # Document ID from worker logs
    document_id = "4053d006-2fca-4be0-bb5c-ef70b945c143"
    user_id = "936551b6-b7a4-4d3d-9fe0-a491794fd66b"  # From worker logs
    
    print(f"📄 Document ID: {document_id}")
    print(f"👤 User ID: {user_id}")
    print()
    
    try:
        # Initialize RAG system
        config = RetrievalConfig(
            max_chunks=5,
            similarity_threshold=0.4
        )
        
        rag_tool = RAGTool(user_id, config)
        agent = InformationRetrievalAgent()
        agent.rag_tool = rag_tool  # Set the RAG tool
        
        # Test queries
        test_queries = [
            "What is my deductible?",
            "What are the coverage details?",
            "What is covered under this policy?",
            "What are the exclusions?",
            "How much will I pay out of pocket?"
        ]
        
        results = {}
        
        for query in test_queries:
            print(f"🔍 Query: {query}")
            
            try:
                # Create input for the agent
                input_data = InformationRetrievalInput(
                    user_query=query,
                    user_id=user_id
                )
                
                # Use the agent to process the query
                response = await agent.retrieve_information(input_data)
                
                print(f"✅ Response: {response.direct_answer[:200]}...")
                
                # Get chunks directly from RAG tool
                chunks = await rag_tool.retrieve_chunks_from_text(query)
                print(f"📊 Retrieved {len(chunks)} chunks")
                
                for i, chunk in enumerate(chunks):
                    print(f"  Chunk {i+1}: {chunk.content[:100]}... (similarity: {chunk.similarity:.3f})")
                
                results[query] = {
                    "response": response.direct_answer,
                    "chunks_count": len(chunks),
                    "chunks": [
                        {
                            "content": chunk.content[:200],
                            "similarity": chunk.similarity,
                            "document_id": chunk.document_id,
                            "chunk_id": chunk.chunk_id
                        }
                        for chunk in chunks
                    ]
                }
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                results[query] = {"error": str(e)}
            
            print()
        
        # Save results
        timestamp = int(datetime.now().timestamp())
        results_file = f"uploaded_document_rag_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {results_file}")
        
        # Summary
        successful_queries = sum(1 for r in results.values() if "error" not in r)
        total_queries = len(test_queries)
        
        print(f"\n📊 Summary:")
        print(f"  Successful queries: {successful_queries}/{total_queries}")
        print(f"  Success rate: {successful_queries/total_queries*100:.1f}%")
        
        if successful_queries > 0:
            print("✅ RAG system is working with the uploaded document!")
        else:
            print("❌ RAG system is not finding relevant chunks")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(test_uploaded_document_rag())
