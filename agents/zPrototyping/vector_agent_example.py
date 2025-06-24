#!/usr/bin/env python3
"""
Enhanced Vector Agent Example with Proper Decryption
===================================================

This example demonstrates a working vector-aware agent that:
1. Properly retrieves encrypted vector content
2. Shows the realistic behavior when content can't be decrypted
3. Provides genuine document-based responses when possible
4. Uses real content from retrieved vectors

Usage:
    python vector_agent_example.py
"""

import sys
import os
import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from agents.common.vector_retrieval_tool import VectorRetrievalTool, VectorFilter
from db.services.encryption_service import EncryptionServiceFactory
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentAwareResponse(BaseModel):
    """Response model for document-aware agent"""
    response: str
    has_documents: bool
    confidence: float
    context_quality: str  # excellent, good, limited, none
    citations: List[str]
    suggestions: List[str]

class EnhancedVectorAgent:
    """
    Enhanced agent that properly processes encrypted vector content
    """
    
    def __init__(self):
        self.vector_tool = VectorRetrievalTool(force_supabase=True)
        self.encryption_service = EncryptionServiceFactory.create_service('mock')
        
    async def _decrypt_chunk_content(self, encrypted_content: bytes, key_id: UUID) -> str:
        """Decrypt chunk content using the encryption service"""
        try:
            if not encrypted_content or not key_id:
                return ""
            
            # Handle if encrypted_content is already a string
            if isinstance(encrypted_content, str):
                encrypted_content = encrypted_content.encode('utf-8')
                
            decrypted_bytes = await self.encryption_service.decrypt(encrypted_content, key_id)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.warning(f"Failed to decrypt content: {e}")
            return "[Content unavailable]"
    
    async def _get_document_context(self, user_id: str) -> tuple[str, List[str], str]:
        """
        Retrieve and decrypt document content for the user
        
        Returns:
            Tuple of (combined_text, citations, context_quality)
        """
        try:
            # Get vectors for user
            filter_criteria = VectorFilter(
                user_id=user_id,
                is_active=True,
                limit=20  # Reasonable limit for demo
            )
            
            vectors = await self.vector_tool.get_vectors_by_filter(filter_criteria)
            
            if not vectors:
                return "", [], "none"
            
            logger.info(f"Retrieved {len(vectors)} vector chunks from database")
            
            # Try to decrypt chunks
            decrypted_chunks = []
            citations = []
            
            for i, vector in enumerate(vectors[:5]):  # Process first 5 for demo
                try:
                    # Check if we have the raw encrypted data
                    encrypted_content = getattr(vector, 'encrypted_chunk_text', None)
                    if encrypted_content and vector.encryption_key_id:
                        logger.info(f"Attempting to decrypt chunk {vector.chunk_index}")
                        decrypted_text = await self._decrypt_chunk_content(
                            encrypted_content, 
                            vector.encryption_key_id
                        )
                        if decrypted_text and decrypted_text != "[Content unavailable]":
                            decrypted_chunks.append(decrypted_text)
                            citations.append(f"Document chunk {vector.chunk_index}")
                            logger.info(f"Successfully decrypted chunk {vector.chunk_index}")
                        else:
                            logger.warning(f"Could not decrypt chunk {vector.chunk_index}")
                    else:
                        logger.warning(f"Missing encrypted content or key for chunk {vector.chunk_index}")
                    
                except Exception as e:
                    logger.warning(f"Error processing vector {i}: {e}")
                    continue
            
            # Combine text
            combined_text = "\n\n".join(decrypted_chunks)
            
            # Determine context quality
            if len(decrypted_chunks) >= 3:
                context_quality = "excellent"
            elif len(decrypted_chunks) >= 2:
                context_quality = "good"
            elif len(decrypted_chunks) >= 1:
                context_quality = "limited"
            else:
                context_quality = "none"
            
            logger.info(f"Successfully decrypted {len(decrypted_chunks)} chunks, quality: {context_quality}")
            return combined_text, citations[:3], context_quality
            
        except Exception as e:
            logger.error(f"Error getting document context: {e}")
            return "", [], "none"
    
    async def process_query(self, query: str, user_id: str) -> DocumentAwareResponse:
        """
        Process a user query with document context
        
        Args:
            query: User's question
            user_id: User ID for document retrieval
            
        Returns:
            DocumentAwareResponse with processed result
        """
        logger.info(f"Processing query: {query}")
        
        # Get document context
        document_text, citations, context_quality = await self._get_document_context(user_id)
        
        has_documents = bool(document_text.strip())
        
        if has_documents:
            # Generate document-based response
            response = await self._generate_document_response(query, document_text)
            confidence = 0.9 if context_quality in ["excellent", "good"] else 0.7
            suggestions = ["Review the specific sections mentioned in your documents"]
        else:
            # Generate general response
            response = await self._generate_general_response(query)
            confidence = 0.6
            citations = []
            suggestions = ["Consider uploading your insurance documents for personalized guidance"]
        
        return DocumentAwareResponse(
            response=response,
            has_documents=has_documents,
            confidence=confidence,
            context_quality=context_quality,
            citations=citations,
            suggestions=suggestions
        )
    
    async def _generate_document_response(self, query: str, document_text: str) -> str:
        """Generate response based on actual document content"""
        text_snippet = document_text[:300] + "..." if len(document_text) > 300 else document_text
        
        return f"""Based on your uploaded insurance documents, here's what I found regarding: "{query}"

From your policy documents:
{text_snippet}

This information directly relates to your specific coverage and can help answer your question. I recommend reviewing the complete section for full details."""
    
    async def _generate_general_response(self, query: str) -> str:
        """Generate general response when no documents are available"""
        return f"""I'd be happy to help with: "{query}"

However, I don't currently have access to your specific insurance documents. For the most accurate and personalized information, I recommend:

1. Uploading your insurance policy documents
2. Contacting your insurance provider directly
3. Checking your member portal for specific coverage details

Once you upload your documents, I can provide specific guidance based on your actual policy terms."""

async def main():
    """Main demonstration function"""
    print("=== 🔧 Enhanced Vector Agent Demo (Fixed Version) ===\n")
    
    agent = EnhancedVectorAgent()
    
    # Test user ID (replace with actual user ID that has documents)
    test_user_id = "d64bfbbe-ff7f-4b51-b220-a0fa20756d9d"
    
    test_queries = [
        "I need to find a cardiologist. What does my insurance cover?",
        "What are my prescription drug benefits?", 
        "Do I need a referral to see a specialist?"
    ]
    
    print("🔍 Testing Enhanced Document-Aware Agent:\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"--- Test {i}: {query} ---")
        
        try:
            response = await agent.process_query(query, test_user_id)
            
            print(f"📝 Response: {response.response}")
            print(f"📚 Has Documents: {response.has_documents}")
            print(f"📚 Citations: {response.citations}")
            print(f"🎯 Confidence: {response.confidence}")
            print(f"📊 Context Quality: {response.context_quality}")
            print(f"💡 Suggestions: {response.suggestions[0] if response.suggestions else 'None'}")
            print()
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            print()
    
    print("=== 📊 Demonstration Summary ===")
    print()
    print("This demo shows the realistic behavior of the vector system:")
    print("✅ Successfully retrieves vector metadata from Supabase")
    print("⚠️  Encryption makes actual content unavailable in this demo")
    print("🔧 Agent gracefully handles missing content")
    print("📈 Provides appropriate confidence scores based on available data")
    print()
    print("In production with proper encryption keys:")
    print("🔓 Content would be properly decrypted")
    print("📚 Real document text would be used for responses")
    print("🎯 Citations would reference actual content")

if __name__ == "__main__":
    asyncio.run(main()) 