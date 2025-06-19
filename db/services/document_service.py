"""
Document Service for MVP Refactoring
Handles policy basics extraction, hybrid search (facts + vectors), and simplified document operations
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

from .db_pool import get_db_pool
from .encryption_service import EncryptionServiceFactory

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Simplified document service focused on policy basics and hybrid search.
    Replaces complex processing job system with direct LLM-based policy extraction.
    """
    
    def __init__(self):
        self.encryption_service = EncryptionServiceFactory.create_service('mock')
        
    async def extract_policy_basics(self, document_id: str, text: str) -> Dict[str, Any]:
        """
        Extract policy basics from document text using LLM.
        
        Args:
            document_id: Document UUID
            text: Extracted document text
            
        Returns:
            Dict containing policy facts like deductible, copay, annual_max, etc.
        """
        try:
            logger.info(f"Extracting policy basics for document {document_id}")
            
            # Determine if this is an insurance policy document
            if not self._is_insurance_document(text):
                logger.info(f"Document {document_id} doesn't appear to be an insurance policy")
                return {}
            
            # Extract policy facts using pattern matching and heuristics
            # In production, this would use an LLM API call
            policy_facts = await self._extract_insurance_facts(text)
            
            # Update the database with extracted facts
            await self.update_policy_basics(document_id, policy_facts)
            
            logger.info(f"Extracted policy basics for {document_id}: {len(policy_facts)} facts")
            return policy_facts
            
        except Exception as e:
            logger.error(f"Failed to extract policy basics for {document_id}: {e}")
            raise
    
    def _is_insurance_document(self, text: str) -> bool:
        """Check if document appears to be an insurance policy."""
        insurance_keywords = [
            'deductible', 'copay', 'coinsurance', 'premium', 'coverage',
            'policy', 'benefit', 'out-of-pocket', 'network', 'medicare',
            'medicaid', 'insurance', 'plan', 'member', 'subscriber'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in insurance_keywords if keyword in text_lower)
        
        # If we find at least 3 insurance-related keywords, consider it an insurance document
        return keyword_count >= 3
    
    async def _extract_insurance_facts(self, text: str) -> Dict[str, Any]:
        """
        Extract insurance facts using pattern matching.
        In production, this would be replaced with LLM API calls.
        """
        facts = {}
        text_lower = text.lower()
        
        # Extract deductible
        deductible_patterns = [
            r'deductible[:\s]*\$?(\d{1,3}(?:,\d{3})*)',
            r'annual deductible[:\s]*\$?(\d{1,3}(?:,\d{3})*)',
            r'\$?(\d{1,3}(?:,\d{3})*)\s*deductible'
        ]
        
        for pattern in deductible_patterns:
            match = re.search(pattern, text_lower)
            if match:
                facts['deductible'] = int(match.group(1).replace(',', ''))
                break
        
        # Extract copay
        copay_patterns = [
            r'copay[:\s]*\$?(\d{1,3})',
            r'co-pay[:\s]*\$?(\d{1,3})',
            r'primary care[:\s]*\$?(\d{1,3})',
            r'\$?(\d{1,3})\s*copay'
        ]
        
        for pattern in copay_patterns:
            match = re.search(pattern, text_lower)
            if match:
                facts['copay_primary'] = int(match.group(1))
                break
        
        # Extract out-of-pocket maximum
        oop_patterns = [
            r'out-of-pocket maximum[:\s]*\$?(\d{1,3}(?:,\d{3})*)',
            r'annual out-of-pocket[:\s]*\$?(\d{1,3}(?:,\d{3})*)',
            r'maximum out-of-pocket[:\s]*\$?(\d{1,3}(?:,\d{3})*)'
        ]
        
        for pattern in oop_patterns:
            match = re.search(pattern, text_lower)
            if match:
                facts['annual_max'] = int(match.group(1).replace(',', ''))
                break
        
        # Extract coinsurance
        coinsurance_patterns = [
            r'coinsurance[:\s]*(\d{1,2})%',
            r'(\d{1,2})%\s*coinsurance'
        ]
        
        for pattern in coinsurance_patterns:
            match = re.search(pattern, text_lower)
            if match:
                facts['coinsurance_percentage'] = int(match.group(1))
                break
        
        # Extract plan type
        if 'hmo' in text_lower:
            facts['plan_type'] = 'HMO'
        elif 'ppo' in text_lower:
            facts['plan_type'] = 'PPO'
        elif 'epo' in text_lower:
            facts['plan_type'] = 'EPO'
        elif 'pos' in text_lower:
            facts['plan_type'] = 'POS'
        
        # Extract network information
        if 'in-network' in text_lower or 'in network' in text_lower:
            facts['has_network_restrictions'] = True
        
        # Add extraction metadata
        facts['_extraction_metadata'] = {
            'extracted_at': datetime.utcnow().isoformat(),
            'extraction_method': 'pattern_matching',
            'document_length': len(text),
            'facts_found': len([k for k in facts.keys() if not k.startswith('_')])
        }
        
        return facts
    
    async def get_policy_facts(self, document_id: str) -> Dict[str, Any]:
        """
        Get policy facts for a document quickly using JSONB query.
        Target: <50ms response time.
        """
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                # Use the database function for fast JSONB lookup
                facts = await conn.fetchval(
                    "SELECT get_policy_facts($1)",
                    uuid.UUID(document_id)
                )
                
                return facts or {}
                
        except Exception as e:
            logger.error(f"Failed to get policy facts for {document_id}: {e}")
            return {}
    
    async def update_policy_basics(self, document_id: str, facts: Dict[str, Any]) -> bool:
        """Update policy_basics JSONB column for a document."""
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                # Use the database function to update policy basics
                success = await conn.fetchval(
                    "SELECT update_policy_basics($1, $2)",
                    uuid.UUID(document_id),
                    json.dumps(facts)
                )
                
                if success:
                    logger.info(f"Updated policy basics for document {document_id}")
                else:
                    logger.warning(f"Document {document_id} not found for policy basics update")
                
                return success
                
        except Exception as e:
            logger.error(f"Failed to update policy basics for {document_id}: {e}")
            return False
    
    async def search_hybrid(self, user_id: str, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Hybrid search combining structured policy facts lookup + vector semantic search.
        Target: <600ms response time.
        """
        try:
            logger.info(f"Performing hybrid search for user {user_id}: '{query}'")
            
            # Parse query for structured facts
            structured_criteria = self._parse_query_for_facts(query)
            
            # Perform both searches concurrently
            tasks = [
                self._search_policy_facts(user_id, structured_criteria, limit),
                self._search_semantic_vectors(user_id, query, limit)
            ]
            
            policy_results, vector_results = await asyncio.gather(*tasks)
            
            # Combine and rank results
            combined_results = self._combine_search_results(policy_results, vector_results, query)
            
            return {
                'query': query,
                'total_results': len(combined_results),
                'results': combined_results[:limit],
                'search_metadata': {
                    'structured_criteria': structured_criteria,
                    'policy_facts_found': len(policy_results),
                    'vector_results_found': len(vector_results),
                    'search_timestamp': datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Hybrid search failed for user {user_id}: {e}")
            return {
                'query': query,
                'total_results': 0,
                'results': [],
                'error': str(e)
            }
    
    def _parse_query_for_facts(self, query: str) -> Dict[str, Any]:
        """Parse natural language query for structured policy criteria."""
        criteria = {}
        query_lower = query.lower()
        
        # Parse deductible queries
        deductible_match = re.search(r'deductible.*?(\d{1,3}(?:,\d{3})*)', query_lower)
        if deductible_match:
            deductible_value = int(deductible_match.group(1).replace(',', ''))
            
            if 'under' in query_lower or 'less than' in query_lower or 'below' in query_lower:
                criteria['deductible_max'] = deductible_value
            elif 'over' in query_lower or 'more than' in query_lower or 'above' in query_lower:
                criteria['deductible_min'] = deductible_value
            else:
                criteria['deductible'] = deductible_value
        
        # Parse copay queries
        copay_match = re.search(r'copay.*?(\d{1,3})', query_lower)
        if copay_match:
            copay_value = int(copay_match.group(1))
            criteria['copay_primary'] = copay_value
        
        # Parse plan type queries
        if 'hmo' in query_lower:
            criteria['plan_type'] = 'HMO'
        elif 'ppo' in query_lower:
            criteria['plan_type'] = 'PPO'
        elif 'epo' in query_lower:
            criteria['plan_type'] = 'EPO'
        
        return criteria
    
    async def _search_policy_facts(self, user_id: str, criteria: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Search documents by policy criteria using JSONB queries."""
        if not criteria:
            return []
        
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                # Build dynamic JSONB query based on criteria
                jsonb_criteria = {}
                
                for key, value in criteria.items():
                    if not key.endswith('_min') and not key.endswith('_max'):
                        jsonb_criteria[key] = value
                
                # Use the database function for policy criteria search
                if jsonb_criteria:
                    results = await conn.fetch(
                        "SELECT * FROM search_by_policy_criteria($1, $2) LIMIT $3",
                        uuid.UUID(user_id),
                        json.dumps(jsonb_criteria),
                        limit
                    )
                    
                    return [{
                        'document_id': str(row['id']),
                        'filename': row['original_filename'],
                        'policy_facts': row['policy_basics'],
                        'created_at': row['created_at'],
                        'search_type': 'policy_facts',
                        'relevance_score': 0.9  # High relevance for exact fact matches
                    } for row in results]
                
                return []
                
        except Exception as e:
            logger.error(f"Policy facts search failed: {e}")
            return []
    
    async def _search_semantic_vectors(self, user_id: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search documents using vector similarity."""
        try:
            # This would typically use the embedding service to convert query to vector
            # For now, we'll simulate vector search with a basic text search
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                
                # Get documents that might contain the query terms
                results = await conn.fetch("""
                    SELECT DISTINCT 
                        d.id as document_id,
                        d.original_filename,
                        d.created_at,
                        d.policy_basics
                    FROM document_vectors dv
                    JOIN documents d ON dv.document_record_id = d.id
                    WHERE dv.user_id = $1 
                    AND dv.is_active = true
                    AND d.status = 'completed'
                    ORDER BY d.created_at DESC
                    LIMIT $2
                """, uuid.UUID(user_id), limit)
                
                return [{
                    'document_id': str(row['document_id']),
                    'filename': row['original_filename'],
                    'policy_facts': row['policy_basics'],
                    'created_at': row['created_at'],
                    'search_type': 'vector_semantic',
                    'relevance_score': 0.7  # Moderate relevance for semantic matches
                } for row in results]
                
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def _combine_search_results(self, policy_results: List[Dict], vector_results: List[Dict], query: str) -> List[Dict]:
        """Combine and rank results from both search methods."""
        # Create a map to deduplicate by document_id
        results_map = {}
        
        # Add policy results (higher priority)
        for result in policy_results:
            doc_id = result['document_id']
            results_map[doc_id] = result
        
        # Add vector results (but don't override policy results)
        for result in vector_results:
            doc_id = result['document_id']
            if doc_id not in results_map:
                results_map[doc_id] = result
            else:
                # Combine search types if document found in both
                existing = results_map[doc_id]
                existing['search_type'] = 'hybrid'
                existing['relevance_score'] = max(existing['relevance_score'], result['relevance_score'])
        
        # Sort by relevance score (descending) and creation date (descending)
        combined_results = list(results_map.values())
        combined_results.sort(
            key=lambda x: (x['relevance_score'], x['created_at']),
            reverse=True
        )
        
        return combined_results
    
    async def get_document_status(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """Get simplified document status (replaces complex progress tracking)."""
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                doc = await conn.fetchrow("""
                    SELECT 
                        id, original_filename, status, document_type,
                        file_size, content_type, policy_basics,
                        created_at, updated_at
                    FROM documents
                    WHERE id = $1 AND user_id = $2
                """, uuid.UUID(document_id), uuid.UUID(user_id))
                
                if not doc:
                    return {'error': 'Document not found'}
                
                return {
                    'document_id': str(doc['id']),
                    'filename': doc['original_filename'],
                    'status': doc['status'],
                    'document_type': doc['document_type'],
                    'file_size': doc['file_size'],
                    'content_type': doc['content_type'],
                    'has_policy_facts': doc['policy_basics'] is not None,
                    'policy_facts_count': len(doc['policy_basics'] or {}) if doc['policy_basics'] else 0,
                    'created_at': doc['created_at'],
                    'updated_at': doc['updated_at']
                }
                
        except Exception as e:
            logger.error(f"Failed to get document status for {document_id}: {e}")
            return {'error': str(e)}
    
    async def list_user_documents(self, user_id: str, limit: int = 50, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List user documents with policy facts summary."""
        try:
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                where_clause = "WHERE user_id = $1"
                params = [uuid.UUID(user_id)]
                
                if document_type:
                    where_clause += " AND document_type = $2"
                    params.append(document_type)
                
                docs = await conn.fetch(f"""
                    SELECT 
                        id, original_filename, status, document_type,
                        file_size, policy_basics, created_at
                    FROM documents
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ${'2' if not document_type else '3'}
                """, *params, limit)
                
                return [{
                    'document_id': str(doc['id']),
                    'filename': doc['original_filename'],
                    'status': doc['status'],
                    'document_type': doc['document_type'],
                    'file_size': doc['file_size'],
                    'has_policy_facts': doc['policy_basics'] is not None,
                    'policy_summary': self._create_policy_summary(doc['policy_basics']),
                    'created_at': doc['created_at']
                } for doc in docs]
                
        except Exception as e:
            logger.error(f"Failed to list documents for user {user_id}: {e}")
            return []
    
    def _create_policy_summary(self, policy_basics: Optional[Dict]) -> Dict[str, Any]:
        """Create a brief summary of policy facts for display."""
        if not policy_basics:
            return {}
        
        summary = {}
        
        if 'deductible' in policy_basics:
            summary['deductible'] = f"${policy_basics['deductible']:,}"
        
        if 'copay_primary' in policy_basics:
            summary['copay'] = f"${policy_basics['copay_primary']}"
        
        if 'annual_max' in policy_basics:
            summary['out_of_pocket_max'] = f"${policy_basics['annual_max']:,}"
        
        if 'plan_type' in policy_basics:
            summary['plan_type'] = policy_basics['plan_type']
        
        return summary

# Service factory function
async def get_document_service() -> DocumentService:
    """Get document service instance."""
    return DocumentService()