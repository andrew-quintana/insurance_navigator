#!/usr/bin/env python3
"""
Supabase-native regulatory document processor.
Uses Supabase Edge Functions for proper vector generation.
"""

import asyncio
import aiohttp
import os
import json
import asyncpg
import hashlib
from datetime import datetime
from typing import List, Dict, Any
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseRegulatoryProcessor:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.db_url = os.getenv('DATABASE_URL')
        
        if not all([self.supabase_url, self.service_role_key, self.db_url]):
            raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DATABASE_URL")
    
    async def process_regulatory_urls(self, urls: List[str]) -> Dict[str, Any]:
        """Process regulatory documents using Supabase infrastructure."""
        results = {
            'processed': [],
            'failed': [],
            'duplicates': [],
            'start_time': datetime.now()
        }
        
        logger.info(f"Starting Supabase-native processing of {len(urls)} regulatory documents")
        
        async with asyncpg.create_pool(self.db_url, statement_cache_size=0) as pool:
            for i, url in enumerate(urls, 1):
                logger.info(f"[{i}/{len(urls)}] Processing: {url}")
                
                try:
                    result = await self._process_single_url(url, pool)
                    if result['status'] == 'processed':
                        results['processed'].append(result)
                    elif result['status'] == 'duplicate':
                        results['duplicates'].append(result)
                    elif result['status'] == 'failed':
                        results['failed'].append(result)
                        
                except Exception as e:
                    logger.error(f"Failed to process {url}: {e}")
                    results['failed'].append({
                        'url': url,
                        'error': str(e),
                        'status': 'failed'
                    })
                
                # Add delay between requests
                if i < len(urls):
                    await asyncio.sleep(2)
        
        results['processing_time'] = (datetime.now() - results['start_time']).total_seconds()
        logger.info(f"Processing complete: {len(results['processed'])} processed, {len(results['duplicates'])} duplicates, {len(results['failed'])} failed")
        
        return results
    
    async def _process_single_url(self, url: str, pool) -> Dict[str, Any]:
        """Process a single regulatory document through Supabase."""
        
        async with pool.acquire() as conn:
            # 1. Download and extract content
            content_data = await self._extract_content(url)
            if not content_data:
                return {'url': url, 'status': 'failed', 'error': 'Content extraction failed'}
            
            content_text = content_data.get('content', '')
            if len(content_text.strip()) < 50:
                return {'url': url, 'status': 'failed', 'error': 'Content too short'}
            
            # 2. Check for duplicates using content hash
            content_hash = hashlib.md5(content_text.encode()).hexdigest()
            existing = await conn.fetchval(
                "SELECT document_id FROM regulatory_documents WHERE content_hash = $1",
                content_hash
            )
            
            if existing:
                logger.info(f"Duplicate content detected for {url}")
                return {'url': url, 'status': 'duplicate', 'existing_id': str(existing)}
            
            # 3. Store raw file if it's a binary document
            storage_path = None
            if content_data.get('file_data'):
                storage_path = await self._store_raw_file(
                    content_data['file_data'],
                    content_data.get('filename', 'document'),
                    content_data.get('content_type', 'application/octet-stream')
                )
            
            # 4. Create regulatory document record
            doc_id = await conn.fetchval("""
                INSERT INTO regulatory_documents (
                    raw_document_path, title, jurisdiction, program, document_type,
                    structured_contents, source_url, content_hash, 
                    extraction_method, priority_score, search_metadata,
                    tags, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING document_id
            """,
                storage_path or url,  # raw_document_path
                content_data.get('title', 'Untitled Document'),  # title
                'United States',  # jurisdiction
                ['Healthcare', 'Insurance'],  # program
                'regulatory',  # document_type
                json.dumps(content_data),  # structured_contents
                url,  # source_url
                content_hash,  # content_hash
                'bulk_supabase_processing',  # extraction_method
                content_data.get('priority_score', 1.0),  # priority_score
                json.dumps({
                    'processing_timestamp': datetime.now().isoformat(),
                    'source_method': 'supabase_bulk_processor',
                    'content_length': len(content_text),
                    'file_size': len(content_data.get('file_data', b'')),
                    'storage_path': storage_path,
                    'extraction_metadata': content_data.get('metadata', {})
                }),  # search_metadata
                content_data.get('tags', ['healthcare', 'regulatory']),  # tags
                datetime.now(),  # created_at
                datetime.now()   # updated_at
            )
            
            logger.info(f"Created regulatory document {doc_id} for {url}")
            
            # 5. Trigger vector processing via Edge Function
            vector_result = await self._trigger_vector_processing(doc_id, content_text)
            
            return {
                'url': url,
                'status': 'processed',
                'document_id': str(doc_id),
                'title': content_data.get('title', 'Untitled Document'),
                'content_length': len(content_text),
                'storage_path': storage_path,
                'vector_processing': vector_result
            }
    
    async def _extract_content(self, url: str) -> Dict[str, Any]:
        """Extract content from URL."""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"HTTP {response.status} for {url}")
                        return None
                    
                    content_type = response.headers.get('content-type', '').lower()
                    content_data = await response.read()
                    
                    # Determine filename
                    filename = Path(url).name or 'document'
                    if not Path(filename).suffix and 'pdf' in content_type:
                        filename += '.pdf'
                    
                    result = {
                        'content_type': content_type,
                        'filename': filename,
                        'metadata': {
                            'url': url,
                            'content_length': len(content_data),
                            'headers': dict(response.headers)
                        }
                    }
                    
                    # Handle different content types
                    if 'pdf' in content_type:
                        # For PDFs, store raw data and extract text later via Edge Functions
                        result['file_data'] = content_data
                        result['content'] = f"PDF Document: {filename}\nSource: {url}\nSize: {len(content_data)} bytes"
                        result['title'] = filename.replace('.pdf', '').replace('_', ' ').title()
                        
                    elif 'html' in content_type or 'text' in content_type:
                        # For HTML/text, extract content immediately
                        content_text = content_data.decode('utf-8', errors='ignore')
                        
                        # Basic HTML cleaning
                        if 'html' in content_type:
                            import re
                            # Remove script and style elements
                            content_text = re.sub(r'<script[^>]*>.*?</script>', '', content_text, flags=re.DOTALL)
                            content_text = re.sub(r'<style[^>]*>.*?</style>', '', content_text, flags=re.DOTALL)
                            # Remove HTML tags
                            content_text = re.sub(r'<[^>]+>', ' ', content_text)
                            # Clean up whitespace
                            content_text = ' '.join(content_text.split())
                            
                            # Extract title from HTML
                            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content_data.decode('utf-8', errors='ignore'), re.IGNORECASE)
                            result['title'] = title_match.group(1).strip() if title_match else filename
                        else:
                            result['title'] = filename
                        
                        result['content'] = content_text
                        
                    else:
                        # Unknown content type
                        result['content'] = f"Document: {filename}\nSource: {url}\nContent-Type: {content_type}"
                        result['title'] = filename
                    
                    return result
                    
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            return None
    
    async def _store_raw_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Store raw file in Supabase storage."""
        try:
            import uuid
            
            # Generate secure storage path
            file_id = str(uuid.uuid4())
            storage_path = f"regulatory/{datetime.now().strftime('%Y/%m')}/{file_id}_{filename}"
            
            # Prepare headers for storage upload
            headers = {
                'Authorization': f'Bearer {self.service_role_key}',
                'Content-Type': content_type,
                'apikey': self.service_role_key
            }
            
            # Upload to raw_documents bucket
            upload_url = f"{self.supabase_url}/storage/v1/object/raw_documents/{storage_path}"
            
            timeout = aiohttp.ClientTimeout(total=120)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(upload_url, data=file_data, headers=headers) as response:
                    if response.status in [200, 201]:
                        logger.info(f"Successfully uploaded file to storage: {storage_path}")
                        return storage_path
                    else:
                        error_text = await response.text()
                        logger.error(f"Storage upload failed: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error storing raw file: {e}")
            return None
    
    async def _trigger_vector_processing(self, document_id: str, content_text: str) -> Dict[str, Any]:
        """Trigger vector processing via Supabase Edge Function."""
        try:
            # Call the vector-processor Edge Function
            headers = {
                'Authorization': f'Bearer {self.service_role_key}',
                'Content-Type': 'application/json',
                'apikey': self.service_role_key
            }
            
            payload = {
                'documentId': str(document_id),
                'extractedText': content_text
            }
            
            function_url = f"{self.supabase_url}/functions/v1/regulatory-vector-processor"
            
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout for vector processing
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(function_url, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        result = json.loads(response_text)
                        logger.info(f"✅ Vector processing completed for document {document_id}")
                        return {
                            'status': 'success',
                            'chunks_processed': result.get('chunksProcessed', 0),
                            'total_chunks': result.get('totalChunks', 0),
                            'embedding_method': result.get('embeddingMethod', 'unknown')
                        }
                    else:
                        logger.error(f"❌ Vector processing failed: {response.status} - {response_text}")
                        return {
                            'status': 'failed',
                            'error': f"HTTP {response.status}: {response_text}"
                        }
                        
        except Exception as e:
            logger.error(f"❌ Vector processing error for document {document_id}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

# CLI Interface
async def main():
    processor = SupabaseRegulatoryProcessor()
    
    import sys
    if len(sys.argv) < 2:
        print("Usage: python supabase_regulatory_bulk_processor.py <urls_file_or_url>")
        return
    
    # Parse input
    input_arg = sys.argv[1]
    
    if input_arg.startswith('http'):
        # Single URL
        urls = [input_arg]
    else:
        # File with URLs
        try:
            with open(input_arg, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            print(f"File not found: {input_arg}")
            return
    
    # Process URLs
    results = await processor.process_regulatory_urls(urls)
    
    # Print results summary
    print("\n" + "="*80)
    print("SUPABASE REGULATORY PROCESSING RESULTS")
    print("="*80)
    print(f"✅ Successfully processed: {len(results['processed'])}")
    print(f"🔄 Duplicates skipped: {len(results['duplicates'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"⏱️  Processing time: {results['processing_time']:.2f} seconds")
    
    if results['processed']:
        print(f"\nSuccessfully processed documents:")
        for doc in results['processed']:
            print(f"  📄 {doc['title']}")
            if doc.get('vector_processing', {}).get('status') == 'success':
                chunks = doc['vector_processing'].get('chunks_processed', 0)
                print(f"      Vectors: {chunks} chunks | 📁 {doc.get('storage_path', 'Text only')}")
            else:
                print(f"      ⚠️ Vector processing: {doc.get('vector_processing', {}).get('status', 'unknown')}")
    
    if results['failed']:
        print(f"\nFailed documents:")
        for doc in results['failed']:
            print(f"  ❌ {doc['url']}: {doc.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main()) 