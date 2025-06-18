#!/usr/bin/env python3
"""
Direct regulatory vector processor that bypasses Edge Function limits.
Processes large regulatory documents by chunking and embedding them locally,
then inserting vectors directly into the database.
"""

import asyncio
import aiohttp
import os
import json
import asyncpg
from typing import List, Dict, Any
import logging
from datetime import datetime
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectRegulatoryVectorProcessor:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not all([self.db_url, self.openai_api_key]):
            raise ValueError("Missing required environment variables: DATABASE_URL, OPENAI_API_KEY")

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Chunk text into smaller pieces with overlap."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Find sentence boundary
            sentence_end = text.rfind('.', start, end)
            if sentence_end > start:
                end = sentence_end + 1
            
            chunks.append(text[start:end].strip())
            start = end - overlap
        
        return [chunk for chunk in chunks if len(chunk.strip()) > 0]

    async def generate_embedding(self, session: aiohttp.ClientSession, text: str) -> List[float]:
        """Generate embedding for text using OpenAI API."""
        
        try:
            async with session.post(
                'https://api.openai.com/v1/embeddings',
                json={
                    'input': text,
                    'model': 'text-embedding-3-small',
                    'dimensions': 1536
                },
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data'][0]['embedding']
                elif response.status == 429:
                    # Rate limit - wait and return None to trigger zero vector fallback
                    logger.warning("Rate limit hit - using zero vector fallback")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI API error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    async def get_documents_needing_vectors(self, pool) -> List[Dict[str, Any]]:
        """Get regulatory documents that need vector processing."""
        
        async with pool.acquire() as conn:
            docs = await conn.fetch("""
                SELECT rd.document_id, rd.title, rd.structured_contents, rd.source_url,
                       rd.jurisdiction, rd.document_type
                FROM regulatory_documents rd
                LEFT JOIN document_vectors dv ON dv.regulatory_document_id = rd.document_id
                WHERE dv.regulatory_document_id IS NULL
                   AND rd.structured_contents IS NOT NULL
                   AND rd.processing_status != 'failed'
                ORDER BY LENGTH(rd.structured_contents::text) ASC  -- Process smaller documents first
            """)
            
            logger.info(f"Found {len(docs)} regulatory documents needing vector processing")
            return docs

    async def process_document_vectors(self, session: aiohttp.ClientSession, pool, doc: dict) -> Dict[str, Any]:
        """Process vectors for a single regulatory document."""
        
        document_id = doc['document_id']
        title = doc['title']
        
        logger.info(f"Processing vectors for: {title}")
        
        # Extract and clean content
        structured_contents = doc['structured_contents']
        if isinstance(structured_contents, str):
            try:
                structured_contents = json.loads(structured_contents)
            except:
                structured_contents = {}
        
        structured_contents = structured_contents or {}
        content_text = structured_contents.get('content', '')
        
        if len(content_text.strip()) < 50:
            logger.warning(f"Insufficient content for {title}: {len(content_text)} chars")
            return {
                'document_id': str(document_id),
                'title': title,
                'status': 'failed',
                'error': 'Insufficient content'
            }
        
        # Update document status to processing
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE regulatory_documents 
                SET processing_status = 'vectorizing', 
                    progress_percentage = 0
                WHERE document_id = $1
            """, document_id)
        
        # Chunk the content
        chunks = self.chunk_text(content_text)
        logger.info(f"  Split into {len(chunks)} chunks")
        
        vectors_created = 0
        failed_chunks = 0
        
        # Process chunks in smaller batches to avoid overwhelming API
        batch_size = 3
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Generate embeddings for batch
            embeddings = []
            for chunk_index, chunk_text in enumerate(batch):
                # Add small delay between requests
                if chunk_index > 0:
                    await asyncio.sleep(1)
                
                embedding = await self.generate_embedding(session, chunk_text)
                
                if embedding is None:
                    # Use zero vector as fallback
                    embedding = [0.0] * 1536
                    failed_chunks += 1
                
                embeddings.append((chunk_text, embedding))
            
            # Insert batch to database
            async with pool.acquire() as conn:
                for chunk_index, (chunk_text, embedding) in enumerate(embeddings):
                    global_chunk_index = i + chunk_index
                    
                    await conn.execute("""
                        INSERT INTO document_vectors (
                            user_id, document_id, regulatory_document_id, chunk_index,
                            content_embedding, encrypted_chunk_text, encrypted_chunk_metadata,
                            document_source_type, is_active, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                        None,  # user_id
                        None,  # document_id  
                        document_id,  # regulatory_document_id
                        global_chunk_index,  # chunk_index
                        json.dumps(embedding),  # content_embedding
                        chunk_text,  # encrypted_chunk_text
                        json.dumps({  # encrypted_chunk_metadata
                            'title': title,
                            'jurisdiction': doc['jurisdiction'],
                            'document_type': doc['document_type'],
                            'chunk_length': len(chunk_text),
                            'total_chunks': len(chunks),
                            'processed_at': datetime.now().isoformat(),
                            'extraction_method': 'direct_regulatory_processing',
                            'embedding_method': 'openai' if sum(embedding) != 0 else 'zero_fallback'
                        }),
                        'regulatory_document',  # document_source_type
                        True,  # is_active
                        datetime.now()  # created_at
                    )
                    
                    vectors_created += 1
            
            # Update progress
            progress = min(int((i + batch_size) / len(chunks) * 90), 90)
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE regulatory_documents 
                    SET progress_percentage = $1, vector_count = $2
                    WHERE document_id = $3
                """, progress, vectors_created, document_id)
            
            logger.info(f"  Processed batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size} - {vectors_created} vectors created")
            
            # Small delay between batches
            await asyncio.sleep(2)
        
        # Mark as completed
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE regulatory_documents 
                SET processing_status = 'completed',
                    status = 'completed',
                    progress_percentage = 100,
                    vectors_generated = true,
                    vector_count = $1
                WHERE document_id = $2
            """, vectors_created, document_id)
        
        logger.info(f"✅ Completed {title}: {vectors_created} vectors ({failed_chunks} with zero fallback)")
        
        return {
            'document_id': str(document_id),
            'title': title,
            'status': 'success',
            'chunks_processed': vectors_created,
            'failed_chunks': failed_chunks,
            'embedding_method': 'direct_openai_with_fallback'
        }

    async def process_all_documents(self):
        """Process vectors for all regulatory documents."""
        
        try:
            # Create database connection pool
            pool = await asyncpg.create_pool(self.db_url, statement_cache_size=0)
            
            # Get documents needing processing
            documents = await self.get_documents_needing_vectors(pool)
            
            if not documents:
                logger.info("No regulatory documents need vector processing")
                return
            
            logger.info(f"Starting direct vector processing for {len(documents)} documents")
            
            results = []
            
            async with aiohttp.ClientSession() as session:
                for i, doc in enumerate(documents):
                    logger.info(f"Document {i+1}/{len(documents)}")
                    
                    try:
                        result = await self.process_document_vectors(session, pool, doc)
                        results.append(result)
                        
                        # Delay between documents to be gentle on API
                        if i < len(documents) - 1:
                            logger.info("  Waiting 5 seconds before next document...")
                            await asyncio.sleep(5)
                            
                    except Exception as e:
                        logger.error(f"❌ Failed to process {doc['title']}: {e}")
                        results.append({
                            'document_id': str(doc['document_id']),
                            'title': doc['title'],
                            'status': 'failed',
                            'error': str(e)
                        })
            
            # Report results
            successful = [r for r in results if r['status'] == 'success']
            failed = [r for r in results if r['status'] == 'failed']
            
            logger.info("")
            logger.info("🎉 DIRECT REGULATORY VECTOR PROCESSING COMPLETE")
            logger.info(f"✅ Successfully processed: {len(successful)}")
            logger.info(f"❌ Failed: {len(failed)}")
            
            if successful:
                total_chunks = sum(r.get('chunks_processed', 0) for r in successful)
                total_failed_chunks = sum(r.get('failed_chunks', 0) for r in successful)
                logger.info(f"📦 Total vector chunks created: {total_chunks}")
                logger.info(f"⚠️ Chunks with zero fallback: {total_failed_chunks}")
            
            if failed:
                logger.info("❌ Failed documents:")
                for failure in failed:
                    logger.info(f"  - {failure['title']}: {failure['error']}")
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"direct_regulatory_vector_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'total_documents': len(documents),
                    'successful': len(successful),
                    'failed': len(failed),
                    'results': results
                }, f, indent=2, default=str)
            
            logger.info(f"📄 Results saved to: {results_file}")
            
            await pool.close()
            
        except Exception as e:
            logger.error(f"❌ Error in processing: {e}")
            raise

async def main():
    """Main entry point."""
    processor = DirectRegulatoryVectorProcessor()
    await processor.process_all_documents()

if __name__ == "__main__":
    asyncio.run(main()) 