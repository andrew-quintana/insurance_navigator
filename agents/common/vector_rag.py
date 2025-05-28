"""
Unified RAG interface for agents using the new vector system.
Provides simple, consistent access to policy and document vectors.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from db.services.encryption_aware_embedding_service import get_encryption_aware_embedding_service

logger = logging.getLogger(__name__)

class VectorRAG:
    """Unified RAG interface for agent vector search."""
    
    def __init__(self):
        self.embedding_service = None
    
    async def _get_service(self):
        """Lazy load the embedding service."""
        if not self.embedding_service:
            self.embedding_service = await get_encryption_aware_embedding_service()
        return self.embedding_service
    
    async def search_policy_context(
        self,
        query: str,
        user_id: str,
        policy_filters: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search policy content for RAG context.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            policy_filters: Additional filters for policy_metadata
            limit: Maximum number of results
            
        Returns:
            List of policy context with similarity scores
        """
        try:
            service = await self._get_service()
            results = await service.search_policy_content(
                query=query,
                user_id=user_id,
                policy_filters=policy_filters,
                limit=limit
            )
            
            # Enhance results with RAG-specific formatting
            enhanced_results = []
            for result in results:
                enhanced_results.append({
                    **result,
                    'context_type': 'policy',
                    'relevance_score': 1.0 - result['similarity_score'],  # Convert distance to relevance
                    'summary': self._create_context_summary(result, 'policy')
                })
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error searching policy context: {str(e)}")
            return []
    
    async def search_user_documents(
        self,
        query: str,
        user_id: str,
        document_filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search user documents for RAG context.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            document_filters: Additional filters for chunk_metadata
            limit: Maximum number of results
            
        Returns:
            List of document context with similarity scores
        """
        try:
            service = await self._get_service()
            results = await service.search_user_documents(
                query=query,
                user_id=user_id,
                document_filters=document_filters,
                limit=limit
            )
            
            # Enhance results with RAG-specific formatting
            enhanced_results = []
            for result in results:
                enhanced_results.append({
                    **result,
                    'context_type': 'user_document',
                    'relevance_score': 1.0 - result['similarity_score'],  # Convert distance to relevance
                    'summary': self._create_context_summary(result, 'user_document')
                })
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error searching user documents: {str(e)}")
            return []
    
    async def get_combined_context(
        self,
        query: str,
        user_id: str,
        policy_limit: int = 3,
        document_limit: int = 5,
        relevance_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Get combined context from both policy and user documents.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            policy_limit: Maximum policy results
            document_limit: Maximum document results
            relevance_threshold: Minimum relevance score to include
            
        Returns:
            Combined context with both policy and document information
        """
        try:
            # Search both sources
            policy_results = await self.search_policy_context(
                query=query,
                user_id=user_id,
                limit=policy_limit
            )
            
            document_results = await self.search_user_documents(
                query=query,
                user_id=user_id,
                limit=document_limit
            )
            
            # Filter by relevance threshold
            filtered_policy = [r for r in policy_results if r['relevance_score'] >= relevance_threshold]
            filtered_documents = [r for r in document_results if r['relevance_score'] >= relevance_threshold]
            
            # Create combined context
            combined_context = {
                "query": query,
                "user_id": user_id,
                "policy_context": filtered_policy,
                "document_context": filtered_documents,
                "context_summary": self._create_combined_summary(filtered_policy, filtered_documents),
                "total_results": len(filtered_policy) + len(filtered_documents),
                "max_relevance": max(
                    [r['relevance_score'] for r in filtered_policy + filtered_documents] or [0]
                )
            }
            
            return combined_context
            
        except Exception as e:
            logger.error(f"Error getting combined context: {str(e)}")
            return {
                "query": query,
                "user_id": user_id,
                "policy_context": [],
                "document_context": [],
                "context_summary": "Error retrieving context",
                "total_results": 0,
                "max_relevance": 0.0,
                "error": str(e)
            }
    
    async def get_policy_specific_context(
        self,
        query: str,
        user_id: str,
        policy_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get context specifically for a policy.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            policy_id: Specific policy ID to search within
            limit: Maximum number of results
            
        Returns:
            List of policy-specific context
        """
        try:
            policy_filters = {"policy_number": policy_id}
            return await self.search_policy_context(
                query=query,
                user_id=user_id,
                policy_filters=policy_filters,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting policy-specific context: {str(e)}")
            return []
    
    async def get_document_type_context(
        self,
        query: str,
        user_id: str,
        document_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get context for a specific document type.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            document_type: Specific document type to search
            limit: Maximum number of results
            
        Returns:
            List of document type specific context
        """
        try:
            document_filters = {"document_type": document_type}
            return await self.search_user_documents(
                query=query,
                user_id=user_id,
                document_filters=document_filters,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting document type context: {str(e)}")
            return []
    
    def _create_context_summary(self, result: Dict[str, Any], context_type: str) -> str:
        """Create a brief summary of the context for RAG prompts."""
        try:
            if context_type == 'policy':
                metadata = result.get('policy_metadata', {})
                doc_metadata = result.get('document_metadata', {})
                
                summary_parts = []
                
                # Add policy information
                if metadata.get('policy_number'):
                    summary_parts.append(f"Policy {metadata['policy_number']}")
                
                if metadata.get('coverage_type'):
                    summary_parts.append(f"Coverage: {metadata['coverage_type']}")
                
                if doc_metadata.get('document_type'):
                    summary_parts.append(f"Type: {doc_metadata['document_type']}")
                
                # Add content preview
                content = result.get('content_text', '')
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    summary_parts.append(f"Content: {preview}")
                
                return " | ".join(summary_parts)
                
            elif context_type == 'user_document':
                metadata = result.get('chunk_metadata', {})
                
                summary_parts = []
                
                if metadata.get('original_filename'):
                    summary_parts.append(f"File: {metadata['original_filename']}")
                
                if metadata.get('document_type'):
                    summary_parts.append(f"Type: {metadata['document_type']}")
                
                if metadata.get('page_number'):
                    summary_parts.append(f"Page: {metadata['page_number']}")
                
                # Add content preview
                content = result.get('chunk_text', '')
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    summary_parts.append(f"Content: {preview}")
                
                return " | ".join(summary_parts)
            
            return "Context available"
            
        except Exception as e:
            logger.warning(f"Error creating context summary: {str(e)}")
            return "Context summary unavailable"
    
    def _create_combined_summary(
        self, 
        policy_results: List[Dict[str, Any]], 
        document_results: List[Dict[str, Any]]
    ) -> str:
        """Create a summary of the combined context."""
        try:
            summary_parts = []
            
            if policy_results:
                policy_count = len(policy_results)
                summary_parts.append(f"{policy_count} policy context(s)")
                
                # Extract unique policy numbers
                policy_numbers = set()
                for result in policy_results:
                    metadata = result.get('policy_metadata', {})
                    if metadata.get('policy_number'):
                        policy_numbers.add(metadata['policy_number'])
                
                if policy_numbers:
                    summary_parts.append(f"Policies: {', '.join(list(policy_numbers)[:3])}")
            
            if document_results:
                doc_count = len(document_results)
                summary_parts.append(f"{doc_count} document chunk(s)")
                
                # Extract unique document types
                doc_types = set()
                for result in document_results:
                    metadata = result.get('chunk_metadata', {})
                    if metadata.get('document_type'):
                        doc_types.add(metadata['document_type'])
                
                if doc_types:
                    summary_parts.append(f"Types: {', '.join(list(doc_types)[:3])}")
            
            if not summary_parts:
                return "No relevant context found"
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logger.warning(f"Error creating combined summary: {str(e)}")
            return "Context summary unavailable"
    
    async def get_rag_prompt_context(
        self,
        query: str,
        user_id: str,
        max_context_length: int = 4000,
        include_metadata: bool = True
    ) -> str:
        """
        Get formatted context for RAG prompts.
        
        Args:
            query: Search query
            user_id: User ID for filtering
            max_context_length: Maximum length of context to return
            include_metadata: Whether to include metadata in context
            
        Returns:
            Formatted context string for RAG prompts
        """
        try:
            combined_context = await self.get_combined_context(query, user_id)
            
            context_parts = []
            current_length = 0
            
            # Add policy context
            for result in combined_context.get('policy_context', []):
                if current_length >= max_context_length:
                    break
                    
                part = f"[POLICY CONTEXT]\n"
                if include_metadata:
                    part += f"Summary: {result.get('summary', '')}\n"
                    part += f"Relevance: {result.get('relevance_score', 0):.2f}\n"
                part += f"Content: {result.get('content_text', '')}\n\n"
                
                if current_length + len(part) <= max_context_length:
                    context_parts.append(part)
                    current_length += len(part)
                else:
                    # Add truncated version
                    remaining = max_context_length - current_length
                    if remaining > 100:  # Only add if meaningful space left
                        truncated = part[:remaining-20] + "...\n\n"
                        context_parts.append(truncated)
                    break
            
            # Add document context
            for result in combined_context.get('document_context', []):
                if current_length >= max_context_length:
                    break
                    
                part = f"[DOCUMENT CONTEXT]\n"
                if include_metadata:
                    part += f"Summary: {result.get('summary', '')}\n"
                    part += f"Relevance: {result.get('relevance_score', 0):.2f}\n"
                part += f"Content: {result.get('chunk_text', '')}\n\n"
                
                if current_length + len(part) <= max_context_length:
                    context_parts.append(part)
                    current_length += len(part)
                else:
                    # Add truncated version
                    remaining = max_context_length - current_length
                    if remaining > 100:  # Only add if meaningful space left
                        truncated = part[:remaining-20] + "...\n\n"
                        context_parts.append(truncated)
                    break
            
            if not context_parts:
                return "No relevant context found for this query."
            
            context_str = "".join(context_parts)
            
            # Add summary header
            summary = combined_context.get('context_summary', '')
            header = f"[CONTEXT SUMMARY: {summary}]\n\n"
            
            return header + context_str
            
        except Exception as e:
            logger.error(f"Error creating RAG prompt context: {str(e)}")
            return f"Error retrieving context: {str(e)}"

# Global instance
_vector_rag = None

async def get_vector_rag() -> VectorRAG:
    """Get or create the global VectorRAG instance."""
    global _vector_rag
    if _vector_rag is None:
        _vector_rag = VectorRAG()
    return _vector_rag 