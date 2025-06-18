#!/usr/bin/env python3
"""
Test vector processing for a single regulatory document.
"""

import asyncio
import sys
import os

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from lightweight_vector_processor import LightweightVectorProcessor

async def test_single_document():
    """Test vector processing for one document."""
    try:
        processor = LightweightVectorProcessor()
        
        # Just process one document for testing
        import asyncpg
        
        async with asyncpg.create_pool(processor.db_url, statement_cache_size=0) as pool:
            async with pool.acquire() as conn:
                # Get one regulatory document that needs processing
                doc = await conn.fetchrow("""
                    SELECT rd.document_id, rd.title, rd.structured_contents, rd.source_url
                    FROM regulatory_documents rd
                    WHERE rd.vectors_generated = FALSE
                    ORDER BY rd.created_at DESC
                    LIMIT 1
                """)
                
                if not doc:
                    print("No regulatory documents found that need vector processing.")
                    return
                
                print(f"Testing vector processing for: {doc['title']}")
                
                # Process this one document
                result = await processor._process_document_vectors(doc, max_chunk_size=1000, pool=pool)
                
                print(f"Result: {result}")
                
                # Check final status
                final_status = await conn.fetchrow("""
                    SELECT status, processing_status, vectors_generated, vector_count, progress_percentage
                    FROM regulatory_documents 
                    WHERE document_id = $1
                """, doc['document_id'])
                
                print(f"Final status: {dict(final_status)}")
                
                # Check vectors created
                vector_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM document_vectors 
                    WHERE regulatory_document_id = $1
                """, doc['document_id'])
                
                print(f"Vectors in database: {vector_count}")
                
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_single_document()) 