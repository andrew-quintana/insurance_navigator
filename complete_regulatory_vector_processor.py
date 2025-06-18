#!/usr/bin/env python3
"""
Complete Regulatory Vector Processor
End-to-end pipeline: regulatory_documents → content extraction → chunking → vectorization → document_vectors
"""

import asyncio
import aiohttp
import json
import os
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import openai
import re
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegulatoryVectorProcessor:
    def __init__(self):
        load_dotenv()
        
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not all([self.supabase_url, self.service_role_key, self.openai_api_key]):
            raise ValueError("Missing required environment variables")
        
        # Initialize OpenAI client
        openai.api_key = self.openai_api_key
        
        self.headers = {
            'Authorization': f'Bearer {self.service_role_key}',
            'Content-Type': 'application/json',
            'apikey': self.service_role_key
        }
        
        # Processing statistics
        self.stats = {
            'documents_processed': 0,
            'chunks_created': 0,
            'vectors_generated': 0,
            'errors': []
        }
    
    async def extract_content_from_url(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Extract text content from a regulatory document URL"""
        
        try:
            # For CMS and Medicaid.gov URLs, we'll extract the main content
            if any(domain in url for domain in ['cms.gov', 'medicaid.gov', 'federalregister.gov']):
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Basic HTML text extraction (remove tags)
                        import re
                        text = re.sub(r'<[^>]+>', ' ', html_content)
                        text = re.sub(r'\s+', ' ', text).strip()
                        
                        # Extract meaningful content (skip navigation, headers, footers)
                        # Look for content indicators
                        content_markers = [
                            'summary', 'background', 'final rule', 'requirements', 
                            'provisions', 'implementation', 'guidance', 'policy'
                        ]
                        
                        paragraphs = text.split('\n')
                        relevant_content = []
                        
                        for paragraph in paragraphs:
                            if len(paragraph.strip()) > 100:  # Substantial paragraphs
                                if any(marker in paragraph.lower() for marker in content_markers):
                                    relevant_content.append(paragraph.strip())
                                elif len(relevant_content) > 0:  # Context after finding relevant content
                                    relevant_content.append(paragraph.strip())
                        
                        if relevant_content:
                            return '\n'.join(relevant_content[:20])  # Limit to first 20 relevant paragraphs
                        else:
                            # Fallback: get substantial text content
                            substantial_text = [p.strip() for p in paragraphs if len(p.strip()) > 100]
                            return '\n'.join(substantial_text[:10])
                    else:
                        logger.warning(f"⚠️ Failed to fetch URL {url}: HTTP {response.status}")
                        return None
            else:
                # For other URLs, create placeholder content based on the document metadata
                return f"Regulatory document content for: {url}"
                
        except Exception as e:
            logger.error(f"❌ Error extracting content from {url}: {e}")
            return None
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks for vector processing"""
        
        if not text or len(text) < chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundaries
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:  # Good break point found
                    chunk = text[start:break_point + 1]
                    end = break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
        
        return [chunk for chunk in chunks if len(chunk.strip()) > 50]
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate OpenAI embedding for text"""
        
        try:
            response = await asyncio.to_thread(
                openai.embeddings.create,
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            return None
    
    async def store_document_vectors(self, session: aiohttp.ClientSession, 
                                   regulatory_doc_id: str, chunks: List[str], 
                                   embeddings: List[List[float]]) -> int:
        """Store document vectors in the document_vectors table"""
        
        vectors_stored = 0
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                         vector_data = {
                 'regulatory_document_id': regulatory_doc_id,
                 'document_source_type': 'regulatory_document', 
                 'chunk_embedding': embedding,
                 'chunk_text': chunk,
                 'chunk_index': i,
                 'chunk_hash': hashlib.md5(chunk.encode()).hexdigest(),
                 'is_active': True,
                 'created_at': datetime.now().isoformat(),
                 'chunk_metadata': {
                     'chunk_size': len(chunk),
                     'chunk_index': i,
                     'processing_method': 'automated_regulatory_processor',
                     'embedding_model': 'text-embedding-ada-002'
                 }
             }
            
            try:
                # Insert into document_vectors table
                insert_url = f"{self.supabase_url}/rest/v1/document_vectors"
                async with session.post(insert_url, headers=self.headers, json=vector_data) as response:
                    if response.status in [200, 201]:
                        vectors_stored += 1
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to store vector {i}: {response.status} - {error_text}")
                        
            except Exception as e:
                logger.error(f"❌ Exception storing vector {i}: {e}")
        
        return vectors_stored
    
    async def process_regulatory_document(self, session: aiohttp.ClientSession, doc_info: Dict) -> bool:
        """Process a single regulatory document through the complete pipeline"""
        
        doc_id = doc_info['document_id']
        title = doc_info['title']
        source_url = doc_info.get('source_url', '')
        
        logger.info(f"🔄 Processing: {title[:60]}...")
        
        try:
            # Step 1: Content Extraction
            if source_url:
                content = await self.extract_content_from_url(session, source_url)
            else:
                # Use summary as content for documents without URLs
                summary = doc_info.get('summary', {})
                content = summary.get('text', f"Regulatory guidance document: {title}")
            
            if not content:
                logger.warning(f"⚠️ No content extracted for {title}")
                return False
            
            # Step 2: Text Chunking
            chunks = self.chunk_text(content)
            if not chunks:
                logger.warning(f"⚠️ No chunks created for {title}")
                return False
            
            logger.info(f"   📝 Created {len(chunks)} chunks")
            
            # Step 3: Generate Embeddings
            embeddings = []
            for i, chunk in enumerate(chunks):
                embedding = await self.generate_embedding(chunk)
                if embedding:
                    embeddings.append(embedding)
                else:
                    logger.warning(f"   ⚠️ Failed to generate embedding for chunk {i}")
            
            if not embeddings:
                logger.error(f"❌ No embeddings generated for {title}")
                return False
            
            logger.info(f"   🧮 Generated {len(embeddings)} embeddings")
            
            # Step 4: Store Vectors
            vectors_stored = await self.store_document_vectors(session, doc_id, chunks[:len(embeddings)], embeddings)
            
            if vectors_stored > 0:
                logger.info(f"   ✅ Stored {vectors_stored} vectors for {title}")
                
                # Update document processing status
                await self.update_document_status(session, doc_id, 'completed', vectors_stored)
                
                # Update stats
                self.stats['documents_processed'] += 1
                self.stats['chunks_created'] += len(chunks)
                self.stats['vectors_generated'] += vectors_stored
                
                return True
            else:
                logger.error(f"❌ Failed to store any vectors for {title}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing {title}: {e}")
            self.stats['errors'].append({'document': title, 'error': str(e)})
            return False
    
    async def update_document_status(self, session: aiohttp.ClientSession, doc_id: str, 
                                   status: str, vector_count: int):
        """Update regulatory document processing status"""
        
        try:
            update_data = {
                'vectors_generated': True,
                'vector_count': vector_count,
                'processing_status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            update_url = f"{self.supabase_url}/rest/v1/regulatory_documents?document_id=eq.{doc_id}"
            async with session.patch(update_url, headers=self.headers, json=update_data) as response:
                if response.status not in [200, 204]:
                    logger.warning(f"⚠️ Failed to update document status: {response.status}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Error updating document status: {e}")
    
    async def process_all_regulatory_documents(self, limit: Optional[int] = None):
        """Process all regulatory documents through the vector pipeline"""
        
        logger.info("🚀 Starting Complete Regulatory Vector Processing Pipeline")
        logger.info("=" * 80)
        
        timeout = aiohttp.ClientTimeout(total=300)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # Get all regulatory documents that need processing
            query_url = f"{self.supabase_url}/rest/v1/regulatory_documents?select=document_id,title,source_url,summary"
            if limit:
                query_url += f"&limit={limit}"
            
            async with session.get(query_url, headers=self.headers) as response:
                if response.status != 200:
                    logger.error(f"❌ Failed to fetch regulatory documents: {response.status}")
                    return
                
                documents = await response.json()
                logger.info(f"📋 Found {len(documents)} regulatory documents to process")
            
            # Process documents in batches to avoid overwhelming the system
            batch_size = 5
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i+batch_size]
                logger.info(f"\n🔄 Processing batch {i//batch_size + 1} ({len(batch)} documents)")
                
                # Process batch concurrently
                tasks = [self.process_regulatory_document(session, doc) for doc in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Report batch results
                successful = sum(1 for result in results if result is True)
                logger.info(f"   ✅ Batch {i//batch_size + 1}: {successful}/{len(batch)} successful")
                
                # Small delay between batches
                if i + batch_size < len(documents):
                    await asyncio.sleep(2)
        
        # Final report
        logger.info("\n" + "=" * 80)
        logger.info("🎉 Regulatory Vector Processing Complete!")
        logger.info(f"📊 Documents Processed: {self.stats['documents_processed']}")
        logger.info(f"📝 Chunks Created: {self.stats['chunks_created']}")
        logger.info(f"🧮 Vectors Generated: {self.stats['vectors_generated']}")
        logger.info(f"❌ Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            logger.info("\n⚠️ Errors encountered:")
            for error in self.stats['errors'][:5]:
                logger.info(f"   • {error['document']}: {error['error']}")
        
        return self.stats

async def main():
    """Main execution function"""
    
    processor = RegulatoryVectorProcessor()
    
    try:
        # Process first 10 documents as a test
        stats = await processor.process_all_regulatory_documents(limit=10)
        
        if stats['vectors_generated'] > 0:
            logger.info(f"\n🎯 SUCCESS: Generated {stats['vectors_generated']} vectors!")
            logger.info("🔍 Your RAG system now has regulatory document vectors for semantic search!")
        else:
            logger.error("\n❌ No vectors were generated. Check the logs for issues.")
            
    except Exception as e:
        logger.error(f"💥 Pipeline failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 