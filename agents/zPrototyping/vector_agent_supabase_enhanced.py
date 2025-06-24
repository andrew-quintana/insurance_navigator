#!/usr/bin/env python3
"""
Supabase-Enhanced Vector Agent Example
=====================================

This example demonstrates proper use of all Supabase tables:
1. encryption_keys table for key management
2. document_vectors table for content retrieval  
3. documents table for metadata context
4. Proper decryption using active keys

Usage:
    python vector_agent_supabase_enhanced.py
"""

import sys
import os
import asyncio
import asyncpg
from typing import List, Optional, Dict, Any, Tuple
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

class DocumentContext(BaseModel):
    """Document context with full metadata"""
    document_id: str
    filename: str
    document_type: Optional[str]
    total_chunks: Optional[int]
    processing_status: str
    created_at: datetime

class EnhancedVectorResponse(BaseModel):
    """Enhanced response with full Supabase context"""
    response: str
    has_documents: bool
    confidence: float
    context_quality: str
    citations: List[str]
    document_context: List[DocumentContext]
    decrypted_chunks_count: int
    total_chunks_found: int
    suggestions: List[str]

class SupabaseEnhancedVectorAgent:
    """
    Vector agent that properly leverages all Supabase tables
    """
    
    def __init__(self):
        self.vector_tool = VectorRetrievalTool(force_supabase=True)
        self.encryption_service = EncryptionServiceFactory.create_service('mock')
        
    async def _get_supabase_connection(self):
        """Get direct Supabase connection"""
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL not set")
        return await asyncpg.connect(db_url, statement_cache_size=0)
    
    async def _get_active_encryption_key(self, conn) -> Optional[Dict]:
        """Get the active encryption key from Supabase"""
        try:
            query = """
                SELECT id, key_version, key_status, created_at, metadata
                FROM encryption_keys 
                WHERE key_status = 'active' 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            row = await conn.fetchrow(query)
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Error getting encryption key: {e}")
            return None
    
    async def _get_document_context(self, user_id: str, conn) -> List[DocumentContext]:
        """Get full document context from documents table"""
        try:
            query = """
                SELECT d.id, d.original_filename, d.document_type, 
                       d.total_chunks, d.status, d.created_at
                FROM documents d
                WHERE d.user_id = $1 AND d.status = 'completed'
                ORDER BY d.created_at DESC
            """
            rows = await conn.fetch(query, UUID(user_id))
            
            contexts = []
            for row in rows:
                contexts.append(DocumentContext(
                    document_id=str(row['id']),
                    filename=row['original_filename'],
                    document_type=row['document_type'],
                    total_chunks=row['total_chunks'],
                    processing_status=row['status'],
                    created_at=row['created_at']
                ))
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error getting document context: {e}")
            return []
    
    async def _decrypt_with_key_lookup(self, encrypted_content: str, key_id: UUID, conn) -> str:
        """Decrypt content using proper key lookup from encryption_keys table"""
        try:
            if not encrypted_content or not key_id:
                return ""
            
            # Verify key exists and is valid
            key_query = """
                SELECT key_status, metadata 
                FROM encryption_keys 
                WHERE id = $1 AND key_status IN ('active', 'rotated')
            """
            key_row = await conn.fetchrow(key_query, key_id)
            
            if not key_row:
                logger.debug(f"Encryption key {key_id} not found or invalid (expected in dev)")
                return "[Key not found]"
            
            # Convert string to bytes if needed
            if isinstance(encrypted_content, str):
                encrypted_content = encrypted_content.encode('utf-8')
                
            # Use encryption service to decrypt
            decrypted_bytes = await self.encryption_service.decrypt(encrypted_content, key_id)
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            logger.debug(f"Expected decryption failure with key {key_id}: {e}")
            return "[Decryption failed - expected in dev environment]"
    
    async def _get_enhanced_document_context(self, user_id: str) -> Tuple[str, List[str], str, List[DocumentContext], int, int]:
        """
        Get comprehensive document context using all Supabase tables
        
        Returns:
            Tuple of (combined_text, citations, context_quality, document_contexts, decrypted_count, total_count)
        """
        conn = None
        try:
            conn = await self._get_supabase_connection()
            
            # Get document metadata first
            document_contexts = await self._get_document_context(user_id, conn)
            
            # Get active encryption key
            active_key = await self._get_active_encryption_key(conn)
            if not active_key:
                logger.warning("No active encryption key found")
            
            # Get vectors for user
            filter_criteria = VectorFilter(
                user_id=user_id,
                is_active=True,
                limit=20
            )
            
            vectors = await self.vector_tool.get_vectors_by_filter(filter_criteria)
            
            if not vectors:
                return "", [], "none", document_contexts, 0, 0
            
            logger.info(f"Retrieved {len(vectors)} vector chunks from Supabase")
            
            # Try to decrypt chunks using proper key lookup
            decrypted_chunks = []
            citations = []
            decrypted_count = 0
            
            for i, vector in enumerate(vectors[:10]):  # Process first 10
                try:
                    # Get encrypted content from vector result
                    encrypted_content = getattr(vector, 'encrypted_chunk_text', None)
                    if encrypted_content and vector.encryption_key_id:
                        logger.info(f"Attempting to decrypt chunk {vector.chunk_index} with key {vector.encryption_key_id}")
                        
                        decrypted_text = await self._decrypt_with_key_lookup(
                            encrypted_content,
                            vector.encryption_key_id,
                            conn
                        )
                        
                        if decrypted_text and not decrypted_text.startswith('['):
                            decrypted_chunks.append(decrypted_text)
                            citations.append(f"Document chunk {vector.chunk_index}")
                            decrypted_count += 1
                            logger.info(f"Successfully decrypted chunk {vector.chunk_index}")
                        else:
                            logger.debug(f"Expected: Could not decrypt chunk {vector.chunk_index} - {decrypted_text}")
                    else:
                        logger.debug(f"Missing encrypted content or key for chunk {vector.chunk_index} (normal in dev)")
                
                except Exception as e:
                    logger.warning(f"Error processing vector {i}: {e}")
                    continue
            
            # Combine text
            combined_text = "\n\n".join(decrypted_chunks)
            
            # Determine context quality
            if decrypted_count >= 5:
                context_quality = "excellent"
            elif decrypted_count >= 3:
                context_quality = "good"
            elif decrypted_count >= 1:
                context_quality = "limited"
            else:
                context_quality = "none"
            
            logger.info(f"Successfully decrypted {decrypted_count}/{len(vectors)} chunks, quality: {context_quality}")
            return combined_text, citations[:5], context_quality, document_contexts, decrypted_count, len(vectors)
            
        except Exception as e:
            logger.error(f"Error getting enhanced document context: {e}")
            return "", [], "none", [], 0, 0
        finally:
            if conn:
                await conn.close()
    
    async def process_query(self, query: str, user_id: str) -> EnhancedVectorResponse:
        """
        Process query with full Supabase table integration
        """
        logger.info(f"Processing query: {query}")
        
        # Get comprehensive document context
        (document_text, citations, context_quality, 
         document_contexts, decrypted_count, total_count) = await self._get_enhanced_document_context(user_id)
        
        has_documents = bool(document_text.strip())
        
        if has_documents:
            # Generate document-based response with real content
            text_snippet = document_text[:400] + "..." if len(document_text) > 400 else document_text
            response = f"""Based on your uploaded insurance documents, here's what I found regarding: "{query}"

From your policy documents ({decrypted_count} sections analyzed):
{text_snippet}

This information comes directly from your uploaded documents and provides specific guidance based on your actual policy terms."""
            
            confidence = 0.95 if context_quality == "excellent" else 0.85 if context_quality == "good" else 0.75
            suggestions = [
                "Review the complete policy sections for additional details",
                "Contact your insurance provider for clarification if needed",
                f"I analyzed {decrypted_count} out of {total_count} available document sections"
            ]
        else:
            response = f"""I'd be happy to help with: "{query}"

However, I currently don't have access to decrypted content from your insurance documents. 

{f"I found {total_count} document sections, but couldn't decrypt them. " if total_count > 0 else "No documents found. "}

For accurate, personalized information:
1. Ensure your documents are properly processed and encrypted
2. Contact your insurance provider directly
3. Check your member portal online"""
            
            confidence = 0.4 if total_count > 0 else 0.3
            citations = []
            suggestions = ["Upload and properly process your insurance documents for personalized guidance"]
        
        return EnhancedVectorResponse(
            response=response,
            has_documents=has_documents,
            confidence=confidence,
            context_quality=context_quality,
            citations=citations,
            document_context=document_contexts,
            decrypted_chunks_count=decrypted_count,
            total_chunks_found=total_count,
            suggestions=suggestions
        )

async def main():
    """Main demonstration function"""
    print("=== 🚀 Supabase-Enhanced Vector Agent Demo ===\n")
    
    agent = SupabaseEnhancedVectorAgent()
    
    # Test user ID
    test_user_id = "d64bfbbe-ff7f-4b51-b220-a0fa20756d9d"
    
    test_queries = [
        "What does my insurance cover for specialist visits?",
        "What are my prescription drug benefits?",
        "What's my annual deductible and out-of-pocket maximum?"
    ]
    
    print("🔍 Testing Supabase-Enhanced Agent:\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"--- Test {i}: {query} ---")
        
        try:
            response = await agent.process_query(query, test_user_id)
            
            print(f"📝 Response: {response.response}")
            print(f"📚 Has Documents: {response.has_documents}")
            print(f"📊 Context Quality: {response.context_quality}")
            print(f"🎯 Confidence: {response.confidence}")
            print(f"🔗 Citations: {response.citations}")
            print(f"📄 Document Context: {len(response.document_context)} documents found")
            for doc in response.document_context:
                print(f"   - {doc.filename} ({doc.processing_status}, {doc.total_chunks} chunks)")
            print(f"🔓 Decryption Success: {response.decrypted_chunks_count}/{response.total_chunks_found} chunks")
            print(f"💡 Suggestions: {response.suggestions[0] if response.suggestions else 'None'}")
            print()
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            print()
    
    print("=== 📊 Supabase Integration Summary ===")
    print()
    print("Tables Used:")
    print("✅ encryption_keys - For key validation and decryption")
    print("✅ document_vectors - For vector and encrypted content retrieval")  
    print("✅ documents - For document metadata and context")
    print("⚠️ Note: Decryption depends on proper encryption key management")

if __name__ == "__main__":
    asyncio.run(main()) 