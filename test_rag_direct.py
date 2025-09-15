#!/usr/bin/env python3
"""
Direct RAG system test to check document retrieval.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.production')

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_rag_system():
    """Test RAG system directly."""
    try:
        from agents.tooling.rag.core import RAGTool
        from agents.patient_navigator.information_retrieval import InformationRetrievalAgent
        
        print("🔍 Testing RAG System Directly")
        print("=" * 50)
        
        # Test user ID
        user_id = "b4b0c962-fd49-49b8-993b-4b14c8edc37b"
        
        # Initialize RAG tool with lower similarity threshold
        from agents.tooling.rag.core import RetrievalConfig
        config = RetrievalConfig(similarity_threshold=0.1, max_chunks=10, token_budget=4000)
        rag_tool = RAGTool(user_id, config)
        
        # Test document retrieval
        print(f"📄 Testing document retrieval for user: {user_id}")
        
        # Query for deductible information
        query = "What is my deductible?"
        
        print(f"🔍 Query: {query}")
        
        # Test retrieval
        result = await rag_tool.retrieve_chunks_from_text(query)
        
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Number of chunks: {len(result)}")
        
        if result:
            print(f"📄 First chunk: {result[0].content[:200]}...")
            print(f"📊 Similarity: {result[0].similarity}")
            print(f"📄 Document ID: {result[0].doc_id}")
        else:
            print("❌ No chunks found")
            
        # Test Information Retrieval Agent
        print("\n🤖 Testing Information Retrieval Agent")
        print("-" * 30)
        
        retrieval_agent = InformationRetrievalAgent()
        
        # Test agent processing - need to create proper input
        from agents.patient_navigator.information_retrieval.models import InformationRetrievalInput
        
        input_data = InformationRetrievalInput(
            user_query=query,
            user_id=user_id,
            workflow_context={},
            document_requirements=[]
        )
        
        agent_result = await retrieval_agent.retrieve_information(input_data)
        
        print(f"📊 Agent result type: {type(agent_result)}")
        print(f"📊 Agent result: {agent_result}")
        
        if hasattr(agent_result, 'direct_answer'):
            print(f"✅ Agent direct answer: {agent_result.direct_answer}")
        if hasattr(agent_result, 'sources'):
            print(f"📚 Agent sources: {agent_result.sources}")
            
    except Exception as e:
        print(f"❌ Error testing RAG system: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_system())
