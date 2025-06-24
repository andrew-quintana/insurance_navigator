"""
Vector Agent Tutorial

This file demonstrates step by step how to build a vector-enabled agent,
with clear print statements and explanations at each stage.

Run this file directly to see the output of each step.
"""

import asyncio
import os
import sys
from typing import List, Dict, Any
from dataclasses import dataclass

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.common.vector_retrieval_tool import VectorRetrievalTool, VectorFilter
from db.services.encryption_service import EncryptionServiceFactory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def step1_test_supabase_connection():
    """Step 1: Test basic Supabase connection"""
    print("\n=== Step 1: Testing Supabase Connection ===")
    
    # Get Supabase credentials
    supabase_url = "https://jhrespvvhbnloxrieycf.supabase.co"
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_key:
        print("❌ Error: SUPABASE_SERVICE_ROLE_KEY not found in environment")
        return False
    
    print("✓ Found Supabase service role key")
    
    # Set up database URL for direct connection
    os.environ['DATABASE_URL'] = f"postgresql://postgres.jhrespvvhbnloxrieycf:{supabase_key}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    print("✓ Set up database connection URL using connection pooler")
    
    return True

async def step2_test_vector_tool():
    """Step 2: Test VectorRetrievalTool"""
    print("\n=== Step 2: Testing VectorRetrievalTool ===")
    
    try:
        # Initialize vector tool
        vector_tool = VectorRetrievalTool(force_supabase=True)
        print("✓ VectorRetrievalTool initialized")
        
        # Test user ID
        user_id = "27b30e9d-0d06-4325-910f-20fe9d686f14"
        
        # Create filter criteria
        filter_criteria = VectorFilter(
            user_id=user_id,
            is_active=True,
            limit=5
        )
        
        # Get vectors
        vectors = await vector_tool.get_vectors_by_filter(filter_criteria)
        print(f"✓ Retrieved {len(vectors)} vectors")
        
        if vectors:
            vector = vectors[0]
            print("\nFirst vector details:")
            print(f"- Has encrypted text: {bool(vector.encrypted_chunk_text)}")
            print(f"- Has encryption key: {bool(vector.encryption_key_id)}")
            print(f"- Document source: {vector.document_source_type}")
            return vector_tool, vectors
            
    except Exception as e:
        print(f"❌ Error with VectorRetrievalTool: {str(e)}")
    
    return None, []

async def step3_test_encryption_service():
    """Step 3: Test encryption service with mock implementation"""
    print("\n=== Step 3: Testing Encryption Service ===")
    
    try:
        encryption_service = EncryptionServiceFactory.create_service('mock')
        print("✓ Mock encryption service initialized")
        return encryption_service
    except Exception as e:
        print(f"❌ Error initializing encryption service: {str(e)}")
        return None

async def step4_decrypt_content(vector, encryption_service):
    """Step 4: Test content decryption"""
    print("\n=== Step 4: Testing Content Decryption ===")
    
    if not vector or not encryption_service:
        print("❌ Missing vector or encryption service")
        return None
    
    try:
        if vector.encrypted_chunk_text and vector.encryption_key_id:
            # Prepare content for decryption
            encrypted_content = vector.encrypted_chunk_text
            if isinstance(encrypted_content, str):
                encrypted_content = encrypted_content.encode('utf-8')
            
            # Try decryption
            decrypted = await encryption_service.decrypt(
                encrypted_content,
                vector.encryption_key_id
            )
            
            print("✓ Decryption successful")
            print(f"- Decrypted content length: {len(decrypted)}")
            print("- Preview:", decrypted[:200].decode('utf-8'))
            return decrypted
            
    except Exception as e:
        print(f"❌ Decryption failed: {str(e)}")
        print("\nVector details:")
        print(f"- Encryption key ID: {vector.encryption_key_id}")
        print(f"- Content type: {type(vector.encrypted_chunk_text)}")
        print(f"- Content length: {len(vector.encrypted_chunk_text)}")
    
    return None

class BasicVectorAgent:
    """Step 5: Basic vector-enabled agent"""
    def __init__(self, vector_tool, encryption_service):
        self.vector_tool = vector_tool
        self.encryption_service = encryption_service
    
    async def get_context(self, user_id: str, limit: int = 5) -> List[str]:
        """Get decrypted context for a user"""
        print(f"\nGetting context for user {user_id}...")
        
        # Get vectors
        filter_criteria = VectorFilter(
            user_id=user_id,
            is_active=True,
            limit=limit
        )
        vectors = await self.vector_tool.get_vectors_by_filter(filter_criteria)
        print(f"Found {len(vectors)} vectors")
        
        # Decrypt content
        context = []
        for vector in vectors:
            if vector.encrypted_chunk_text and vector.encryption_key_id:
                try:
                    encrypted_content = vector.encrypted_chunk_text
                    if isinstance(encrypted_content, str):
                        encrypted_content = encrypted_content.encode('utf-8')
                    
                    decrypted = await self.encryption_service.decrypt(
                        encrypted_content,
                        vector.encryption_key_id
                    )
                    
                    if decrypted:
                        context.append(decrypted.decode('utf-8'))
                        print(f"✓ Successfully decrypted chunk {vector.chunk_index}")
                except Exception as e:
                    print(f"❌ Failed to decrypt chunk {vector.chunk_index}: {str(e)}")
        
        return context
    
    async def answer_question(self, user_id: str, question: str) -> Dict[str, Any]:
        """Answer a question using vector context"""
        print(f"\nProcessing question: {question}")
        
        # Get context
        context = await self.get_context(user_id)
        
        # Prepare response
        if context:
            # In a real agent, you would:
            # 1. Use an LLM to process the context
            # 2. Generate a response based on the context
            # 3. Include citations and confidence scores
            # For this demo, we'll just show the first bit of context
            response = {
                'answer': f"Based on your documents, I found this information: {context[0][:200]}...",
                'context_chunks': len(context),
                'has_content': True
            }
        else:
            response = {
                'answer': "I couldn't find any relevant information in your documents.",
                'context_chunks': 0,
                'has_content': False
            }
        
        return response

async def main():
    """Run the tutorial steps"""
    print("\n🚀 Starting Vector Agent Tutorial")
    print("=================================")
    
    # Step 1: Test Supabase connection
    if not await step1_test_supabase_connection():
        print("❌ Failed to set up Supabase connection")
        return
    
    # Step 2: Test vector tool
    vector_tool, vectors = await step2_test_vector_tool()
    if not vector_tool:
        print("❌ Failed to initialize vector tool")
        return
    
    # Step 3: Test encryption service
    encryption_service = await step3_test_encryption_service()
    if not encryption_service:
        print("❌ Failed to initialize encryption service")
        return
    
    # Step 4: Test decryption
    if vectors:
        decrypted = await step4_decrypt_content(vectors[0], encryption_service)
        if not decrypted:
            print("❌ Failed to decrypt content")
    
    # Step 5: Test basic agent
    print("\n=== Step 5: Testing Basic Vector Agent ===")
    agent = BasicVectorAgent(vector_tool, encryption_service)
    
    # Test user ID and question
    user_id = "27b30e9d-0d06-4325-910f-20fe9d686f14"
    question = "What does my insurance cover?"
    
    result = await agent.answer_question(user_id, question)
    
    print("\nAgent Response:")
    print(f"Q: {question}")
    print(f"A: {result['answer']}")
    print(f"Context chunks: {result['context_chunks']}")
    print(f"Has content: {result['has_content']}")
    
    print("\n✨ Tutorial Complete!")
    print("Now you can build your own vector-enabled agent by following these steps.")

if __name__ == "__main__":
    asyncio.run(main()) 
 