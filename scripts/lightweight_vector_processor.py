#!/usr/bin/env python3
"""
Lightweight vector processor for regulatory documents.
Processes documents in smaller chunks to avoid Edge Function timeouts.
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

class LightweightVectorProcessor:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.db_url = os.getenv('DATABASE_URL')
        
        if not all([self.supabase_url, self.service_role_key, self.db_url]):
            raise ValueError("Missing required environment variables")
    
    async def process_regulatory_documents(self, max_chunk_size: int = 1000) -> Dict[str, Any]:
        """Process regulatory documents with smaller text chunks."""
        results = {
            'processed': [],
            'failed': [],
            'start_time': datetime.now()
        }
        
        logger.info("Starting lightweight vector processing for regulatory documents")
        
        async with asyncpg.create_pool(self.db_url, statement_cache_size=0) as pool:
            async with pool.acquire() as conn:
                # Get all regulatory documents that need vector processing
                docs = await conn.fetch("""
                    SELECT rd.document_id, rd.title, rd.structured_contents, rd.source_url
                    FROM regulatory_documents rd
                    LEFT JOIN document_vectors dv ON dv.regulatory_document_id = rd.document_id
                    WHERE dv.regulatory_document_id IS NULL
                    ORDER BY rd.created_at DESC
                """)
                
                logger.info(f"Found {len(docs)} regulatory documents needing vector processing")
                
                for i, doc in enumerate(docs, 1):
                    logger.info(f"[{i}/{len(docs)}] Processing vectors for: {doc['title']}")
                    
                    try:
                        result = await self._process_document_vectors(doc, max_chunk_size, pool)
                        if result['status'] == 'success':
                            results['processed'].append(result)
                        else:
                            results['failed'].append(result)
                            
                    except Exception as e:
                        logger.error(f"Failed to process {doc['title']}: {e}")
                        results['failed'].append({
                            'document_id': str(doc['document_id']),
                            'title': doc['title'],
                            'error': str(e),
                            'status': 'failed'
                        })
                    
                    # Add delay between documents
                    if i < len(docs):
                        await asyncio.sleep(1)
        
        results['processing_time'] = (datetime.now() - results['start_time']).total_seconds()
        logger.info(f"Vector processing complete: {len(results['processed'])} processed, {len(results['failed'])} failed")
        
        return results
    
    async def _process_document_vectors(self, doc: dict, max_chunk_size: int, pool) -> Dict[str, Any]:
        """Process vectors for a single document."""
        
        # Update status to processing
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE regulatory_documents 
                SET processing_status = 'processing', 
                    status = 'processing',
                    progress_percentage = 20
                WHERE document_id = $1
            """, doc['document_id'])
        
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
            # Update status to failed
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE regulatory_documents 
                    SET processing_status = 'failed', 
                        status = 'failed',
                        error_message = 'Insufficient content for vector generation'
                    WHERE document_id = $1
                """, doc['document_id'])
            
            return {
                'document_id': str(doc['document_id']),
                'title': doc['title'],
                'status': 'failed',
                'error': 'Insufficient content'
            }
        
        # Split content into smaller chunks
        chunks = self._split_content(content_text, max_chunk_size)
        logger.info(f"Split {doc['title']} into {len(chunks)} chunks")
        
        vectors_created = 0
        
        async with pool.acquire() as conn:
            for chunk_index, chunk_text in enumerate(chunks):
                try:
                    # Update progress
                    progress = 30 + int((chunk_index / len(chunks)) * 60)  # 30% to 90%
                    await conn.execute("""
                        UPDATE regulatory_documents 
                        SET progress_percentage = $1
                        WHERE document_id = $2
                    """, progress, doc['document_id'])
                    
                    # Generate embedding via OpenAI (direct API call to avoid Edge Function limits)
                    embedding = await self._generate_embedding(chunk_text)
                    
                    if embedding:
                        # Store vector in database
                        await conn.execute("""
                            INSERT INTO document_vectors (
                                regulatory_document_id, chunk_index, content_embedding, 
                                document_source_type, encrypted_chunk_text, 
                                encrypted_chunk_metadata, created_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                            doc['document_id'],  # regulatory_document_id
                            chunk_index,  # chunk_index
                            embedding,  # content_embedding
                            'regulatory_document',  # document_source_type
                            chunk_text,  # encrypted_chunk_text (storing as plaintext for now)
                            json.dumps({
                                'chunk_size': len(chunk_text),
                                'processing_method': 'lightweight_processor',
                                'openai_model': 'text-embedding-ada-002',
                                'timestamp': datetime.now().isoformat()
                            }),  # encrypted_chunk_metadata
                            datetime.now()  # created_at
                        )
                        vectors_created += 1
                        logger.info(f"  ✅ Created vector {chunk_index + 1}/{len(chunks)} for {doc['title']}")
                        
                    # Small delay between chunks
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Failed to process chunk {chunk_index} for {doc['title']}: {e}")
                    continue
        
        # Update final status based on success
        final_status = 'completed' if vectors_created > 0 else 'failed'
        final_error = None if vectors_created > 0 else 'No vectors were successfully generated'
        
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE regulatory_documents 
                SET processing_status = $1, 
                    status = $1,
                    progress_percentage = $2,
                    vectors_generated = $3,
                    vector_count = $4,
                    error_message = $5
                WHERE document_id = $6
            """, 
                final_status,  # processing_status and status
                100 if vectors_created > 0 else 50,  # progress_percentage  
                vectors_created > 0,  # vectors_generated
                vectors_created,  # vector_count
                final_error,  # error_message
                doc['document_id']  # document_id
            )
        
        return {
            'document_id': str(doc['document_id']),
            'title': doc['title'],
            'status': 'success' if vectors_created > 0 else 'failed',
            'chunks_processed': len(chunks),
            'vectors_created': vectors_created
        }
    
    def _split_content(self, content: str, max_chunk_size: int) -> List[str]:
        """Split content into overlapping chunks."""
        chunks = []
        overlap = max_chunk_size // 5  # 20% overlap
        
        for i in range(0, len(content), max_chunk_size - overlap):
            chunk = content[i:i + max_chunk_size]
            if len(chunk.strip()) > 50:  # Only include substantial chunks
                chunks.append(chunk.strip())
        
        return chunks
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API directly."""
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            logger.error("OPENAI_API_KEY not found")
            return None
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    'https://api.openai.com/v1/embeddings',
                    headers={
                        'Authorization': f'Bearer {openai_api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'input': text,
                        'model': 'text-embedding-ada-002'
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['data'][0]['embedding']
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None

async def main():
    """Main function to run the lightweight vector processor."""
    try:
        processor = LightweightVectorProcessor()
        results = await processor.process_regulatory_documents(max_chunk_size=1000)
        
        # Print summary
        print("\n" + "="*80)
        print("LIGHTWEIGHT VECTOR PROCESSING RESULTS")
        print("="*80)
        print(f"✅ Successfully processed: {len(results['processed'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        print(f"⏱️  Processing time: {results['processing_time']:.2f} seconds")
        
        if results['processed']:
            print("\nSuccessfully processed documents:")
            for result in results['processed']:
                print(f"  📄 {result['title']}")
                print(f"      ✅ Chunks: {result['chunks_processed']}, Vectors: {result['vectors_created']}")
        
        if results['failed']:
            print("\nFailed documents:")
            for result in results['failed']:
                print(f"  ❌ {result['title']}: {result['error']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Main process failed: {e}")
        return {'error': str(e)}

if __name__ == '__main__':
    asyncio.run(main()) 