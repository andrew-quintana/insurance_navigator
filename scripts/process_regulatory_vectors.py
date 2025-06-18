#!/usr/bin/env python3
"""
Process vectors for regulatory documents using the agnostic Edge Function.
This script finds regulatory documents without vectors and triggers the Edge Function
to generate embeddings.
"""

import asyncio
import aiohttp
import os
import json
import asyncpg
from typing import List, Dict, Any
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegulatoryVectorProcessor:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.db_url = os.getenv('DATABASE_URL')
        
        if not all([self.supabase_url, self.service_role_key, self.db_url]):
            raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL")
        
        self.edge_function_url = f"{self.supabase_url}/functions/v1/vector-processor"

    async def get_documents_needing_vectors(self, pool) -> List[Dict[str, Any]]:
        """Get regulatory documents that need vector processing."""
        
        async with pool.acquire() as conn:
            # Get all regulatory documents that don't have vectors yet
            docs = await conn.fetch("""
                SELECT rd.document_id, rd.title, rd.structured_contents, rd.source_url,
                       rd.processing_status, rd.vectors_generated
                FROM regulatory_documents rd
                LEFT JOIN document_vectors dv ON dv.regulatory_document_id = rd.document_id
                WHERE dv.regulatory_document_id IS NULL
                   AND rd.structured_contents IS NOT NULL
                   AND rd.processing_status != 'failed'
                ORDER BY rd.created_at DESC
            """)
            
            logger.info(f"Found {len(docs)} regulatory documents needing vector processing")
            return docs

    async def process_document_vector(self, session: aiohttp.ClientSession, doc: dict) -> Dict[str, Any]:
        """Process vectors for a single regulatory document via Edge Function."""
        
        document_id = str(doc['document_id'])
        logger.info(f"Processing vectors for document: {doc['title'][:50]}...")
        
        # Extract content from structured_contents
        structured_contents = doc['structured_contents']
        if isinstance(structured_contents, str):
            try:
                structured_contents = json.loads(structured_contents)
            except:
                structured_contents = {}
        
        structured_contents = structured_contents or {}
        content_text = structured_contents.get('content', '')
        
        if len(content_text.strip()) < 50:
            logger.warning(f"Insufficient content for document {document_id}: {len(content_text)} chars")
            return {
                'document_id': document_id,
                'title': doc['title'],
                'status': 'failed',
                'error': 'Insufficient content'
            }
        
        # Prepare request for agnostic Edge Function
        request_payload = {
            'documentId': document_id,
            'extractedText': content_text,
            'documentType': 'regulatory'  # Specify regulatory document type
        }
        
        try:
            async with session.post(
                self.edge_function_url,
                json=request_payload,
                headers={
                    'Authorization': f'Bearer {self.service_role_key}',
                    'Content-Type': 'application/json'
                },
                timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
            ) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    result = json.loads(response_text)
                    logger.info(f"✅ Successfully processed {result.get('chunksProcessed', 0)} chunks for {doc['title'][:50]}")
                    return {
                        'document_id': document_id,
                        'title': doc['title'],
                        'status': 'success',
                        'chunks_processed': result.get('chunksProcessed', 0),
                        'total_chunks': result.get('totalChunks', 0),
                        'embedding_method': result.get('embeddingMethod', 'unknown'),
                        'warning': result.get('warning')
                    }
                else:
                    logger.error(f"❌ Edge Function failed for {document_id}: {response.status} - {response_text}")
                    return {
                        'document_id': document_id,
                        'title': doc['title'],
                        'status': 'failed',
                        'error': f"Edge Function error: {response.status}"
                    }
                    
        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout processing document {document_id}")
            return {
                'document_id': document_id,
                'title': doc['title'],
                'status': 'failed',
                'error': 'Processing timeout'
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error processing document {document_id}: {e}")
            return {
                'document_id': document_id,
                'title': doc['title'],
                'status': 'failed',
                'error': str(e)
            }

    async def process_all_documents(self):
        """Process vectors for all regulatory documents that need them."""
        
        try:
            # Create database connection pool
            pool = await asyncpg.create_pool(self.db_url, statement_cache_size=0)
            
            # Get documents needing processing
            documents = await self.get_documents_needing_vectors(pool)
            
            if not documents:
                logger.info("No regulatory documents need vector processing")
                return
            
            # Process documents in smaller batches to avoid overwhelming the Edge Function
            batch_size = 3  # Small batch size to avoid timeout issues
            results = []
            
            async with aiohttp.ClientSession() as session:
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
                    
                    # Process batch with some delay between documents
                    for doc in batch:
                        result = await self.process_document_vector(session, doc)
                        results.append(result)
                        
                        # Small delay between documents to be gentle on the API
                        await asyncio.sleep(2)
                    
                    # Longer delay between batches
                    if i + batch_size < len(documents):
                        logger.info("Waiting 10 seconds before next batch...")
                        await asyncio.sleep(10)
            
            # Report results
            successful = [r for r in results if r['status'] == 'success']
            failed = [r for r in results if r['status'] == 'failed']
            
            logger.info(f"")
            logger.info(f"🎉 REGULATORY VECTOR PROCESSING COMPLETE")
            logger.info(f"✅ Successfully processed: {len(successful)}")
            logger.info(f"❌ Failed: {len(failed)}")
            
            if successful:
                total_chunks = sum(r.get('chunks_processed', 0) for r in successful)
                logger.info(f"📦 Total vector chunks created: {total_chunks}")
            
            if failed:
                logger.info(f"❌ Failed documents:")
                for failure in failed:
                    logger.info(f"  - {failure['title'][:50]}: {failure['error']}")
            
            # Save detailed results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"regulatory_vector_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'total_documents': len(documents),
                    'successful': len(successful),
                    'failed': len(failed),
                    'results': results
                }, f, indent=2, default=str)
            
            logger.info(f"📄 Detailed results saved to: {results_file}")
            
            await pool.close()
            
        except Exception as e:
            logger.error(f"❌ Error in processing: {e}")
            raise

async def main():
    """Main entry point."""
    processor = RegulatoryVectorProcessor()
    await processor.process_all_documents()

if __name__ == "__main__":
    asyncio.run(main()) 