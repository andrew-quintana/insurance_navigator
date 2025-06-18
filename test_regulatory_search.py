#!/usr/bin/env python3
"""
Test script to verify regulatory document search functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from db.services.db_pool import get_db_pool
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

async def test_regulatory_search():
    """Test the regulatory document search functionality."""
    
    pool = await get_db_pool()
    
    async with pool.get_connection() as conn:
        # Test 1: Count regulatory documents
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM regulatory_documents
        """)
        print(f"Total regulatory documents: {count}")
        
        # Test 2: Count regulatory vectors
        vector_count = await conn.fetchval("""
            SELECT COUNT(*) FROM document_vectors 
            WHERE document_source_type = 'regulatory_document'
        """)
        print(f"Total regulatory vectors: {vector_count}")
        
        # Test 3: Sample documents
        docs = await conn.fetch("""
            SELECT document_id, title, source_url, jurisdiction, 
                   LENGTH(structured_contents::text) as content_length
            FROM regulatory_documents 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        print("\nRecent regulatory documents:")
        for doc in docs:
            print(f"- {doc['title']} ({doc['content_length']} chars)")
            print(f"  URL: {doc['source_url']}")
            print(f"  Jurisdiction: {doc['jurisdiction']}")
        
        # Test 4: Search function
        search_results = await conn.fetch("""
            SELECT * FROM search_regulatory_documents('Medicare', NULL, 3)
        """)
        
        print(f"\nSearch results for 'Medicare': {len(search_results)} found")
        for result in search_results:
            print(f"- {result['title']}")
            print(f"  Similarity: {result['similarity_score']}")

if __name__ == "__main__":
    asyncio.run(test_regulatory_search()) 