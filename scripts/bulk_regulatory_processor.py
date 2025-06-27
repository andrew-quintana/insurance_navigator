#!/usr/bin/env python3
"""
Bulk Regulatory Document Processor - Unified Vector Storage

Uses the existing document_vectors table for both user and regulatory documents.
Processes regulatory documents from URLs or files, extracting content and creating vectors.
"""

import asyncio
import sys
import json
import hashlib
import aiohttp
import logging
import os
import mimetypes
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import urlparse
import uuid

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from agents.regulatory.regulatory_isolated import IsolatedRegulatoryAgent
    from db.services.db_pool import get_db_pool
    from db.services.encryption_aware_embedding_service import get_encryption_aware_embedding_service
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedRegulatoryProcessor:
    def __init__(self):
        self.regulatory_agent = IsolatedRegulatoryAgent()
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.service_role_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
        
    async def process_regulatory_urls(self, urls: List[str], batch_size: int = 3) -> Dict[str, Any]:
        """Process regulatory documents from URLs using unified vector storage."""
        results = {
            'processed': [],
            'failed': [],
            'duplicates': [],
            'total_vectors_created': 0,
            'processing_time': None,
            'start_time': datetime.now()
        }
        
        logger.info(f"Starting processing of {len(urls)} regulatory documents")
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self._process_single_url(url) for url in batch],
                return_exceptions=True
            )
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                    continue
                    
                if result['status'] == 'processed':
                    results['processed'].append(result)
                    results['total_vectors_created'] += result.get('vector_count', 0)
                elif result['status'] == 'duplicate':
                    results['duplicates'].append(result)
                else:
                    results['failed'].append(result)
            
            await asyncio.sleep(1)  # Rate limiting
            
        results['processing_time'] = (datetime.now() - results['start_time']).total_seconds()
        return results

    async def _process_single_url(self, url: str) -> Dict[str, Any]:
        """Process a single regulatory document URL."""
        try:
            content_text, content_data, file_data, filename, content_type = await self._extract_content(url)
            
            # Generate content hash for deduplication
            content_hash = hashlib.sha256(content_text.encode()).hexdigest()
            
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                # Check for existing document
                existing_doc = await conn.fetchrow(
                    "SELECT id FROM documents WHERE file_hash = $1 AND document_type = 'regulatory'",
                    content_hash
                )
                
                if existing_doc:
                    return {
                        'status': 'duplicate',
                        'url': url,
                        'existing_document_id': str(existing_doc['id']),
                        'message': 'Document already exists with same content hash'
                    }
                
                # Store raw file in storage if we have file data
                storage_path = None
                if file_data:
                    storage_path = await self._store_raw_file(file_data, filename, content_type)
                    logger.info(f"Stored raw file at: {storage_path}")
                
                # Extract metadata for structured storage
                title = content_data.get('title', filename or url.split('/')[-1] or 'Regulatory Document')
                jurisdiction = content_data.get('jurisdiction', 'United States')
                programs = content_data.get('programs', ['Healthcare', 'General'])
                doc_type = 'regulatory'  # Always regulatory in this processor
                
                # Insert into unified documents table
                doc_id = await conn.fetchval("""
                    INSERT INTO documents (
                        storage_path, original_filename, document_type, jurisdiction,
                        program, effective_date, expiration_date, source_url,
                        source_last_checked, file_hash, priority_score, metadata,
                        tags, status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    RETURNING id
                """,
                    storage_path or url,  # storage_path
                    title,  # original_filename
                    doc_type,  # document_type
                    jurisdiction,  # jurisdiction
                    programs,  # program
                    content_data.get('effective_date'),  # effective_date
                    content_data.get('expiration_date'),  # expiration_date
                    url,  # source_url
                    datetime.now(),  # source_last_checked
                    content_hash,  # file_hash
                    content_data.get('priority_score', 1.0),  # priority_score
                    json.dumps({  # metadata
                        'processing_timestamp': datetime.now().isoformat(),
                        'source_method': 'bulk_processor',
                        'content_length': len(content_text),
                        'file_size': len(file_data) if file_data else None,
                        'original_filename': filename,
                        'content_type': content_type,
                        'storage_path': storage_path,
                        'extraction_metadata': content_data.get('metadata', {})
                    }),
                    content_data.get('tags', ['healthcare', 'regulatory']),  # tags
                    'completed',  # status
                    datetime.now(),  # created_at
                    datetime.now()  # updated_at
                )
                
                logger.info(f"Created document {doc_id} for {url}")
                
                # Generate vectors using the unified system
                embedding_service = await get_encryption_aware_embedding_service()
                vector_ids = await self._create_document_vectors(
                    embedding_service, str(doc_id), content_text, {
                        'document_id': str(doc_id),
                        'source_url': url,
                        'document_type': doc_type,
                        'jurisdiction': jurisdiction,
                        'programs': programs
                    }
                )
                
                return {
                    'status': 'processed',
                    'url': url,
                    'document_id': str(doc_id),
                    'vector_count': len(vector_ids),
                    'vector_ids': vector_ids,
                    'title': title,
                    'content_length': len(content_text),
                    'jurisdiction': jurisdiction,
                    'programs': programs,
                    'storage_path': storage_path,
                    'file_size': len(file_data) if file_data else None,
                    'filename': filename,
                    'content_type': content_type
                }
                
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            raise Exception(f"Failed to process {url}: {str(e)}")
    
    async def _create_document_vectors(
        self, 
        embedding_service, 
        document_id: str, 
        content_text: str,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Create vectors for document using unified table."""
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            # Chunk the content appropriately for regulatory documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1200,  # Slightly larger chunks for regulatory content
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            chunks = text_splitter.split_text(content_text)
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            
            # Generate embeddings for all chunks
            embeddings_list = []
            for i, chunk in enumerate(chunks):
                try:
                    embedding = await embedding_service._generate_embedding(chunk)
                    # Normalize embedding dimension to match database schema
                    embedding = await embedding_service._normalize_embedding_dimension(embedding)
                    embeddings_list.append(embedding)
                except Exception as e:
                    logger.error(f"Failed to generate embedding for chunk {i}: {e}")
                    # Use zero vector as fallback
                    embeddings_list.append([0.0] * 384)
            
            # Store in unified document_vectors table
            pool = await get_db_pool()
            vector_ids = []
            
            async with pool.get_connection() as conn:
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
                    try:
                        chunk_metadata = {
                            **metadata, 
                            'chunk_index': i, 
                            'total_chunks': len(chunks)
                        }
                        
                        vector_id = await conn.fetchval("""
                            INSERT INTO document_vectors (
                                document_id, chunk_index, content_embedding, 
                                chunk_text, chunk_metadata, document_source_type,
                                is_active, created_at
                            ) VALUES ($1, $2, $3::vector, $4, $5, $6, $7, $8)
                            RETURNING id
                        """,
                            document_id,  # document_id
                            i,  # chunk_index
                            str(embedding),  # content_embedding
                            chunk,  # chunk_text
                            json.dumps(chunk_metadata),  # chunk_metadata
                            'regulatory',  # document_source_type
                            True,  # is_active
                            datetime.now()  # created_at
                        )
                        
                        vector_ids.append(str(vector_id))
                        
                    except Exception as e:
                        logger.error(f"Failed to store vector {i} for document {document_id}: {e}")
                        continue
            
            logger.info(f"Stored {len(vector_ids)} vectors for document {document_id}")
            return vector_ids
            
        except Exception as e:
            logger.error(f"Failed to create vectors for document {document_id}: {e}")
            raise Exception(f"Failed to create vectors: {str(e)}")

    async def _download_file_from_url(self, url: str) -> tuple[Optional[bytes], Optional[str], Optional[str]]:
        """
        Download file content from URL.
        
        Returns:
            Tuple of (file_data, filename, content_type)
        """
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        file_data = await response.read()
                        
                        # Extract filename from URL or Content-Disposition header
                        filename = self._extract_filename_from_response(response, url)
                        
                        # Get content type
                        content_type = response.headers.get('Content-Type', 'application/octet-stream')
                        
                        # For PDFs and documents, we want to store the raw file
                        if any(ct in content_type.lower() for ct in ['pdf', 'doc', 'docx', 'txt', 'rtf']):
                            logger.info(f"Downloaded file: {filename} ({len(file_data)} bytes, {content_type})")
                            return file_data, filename, content_type
                        else:
                            # For HTML pages, we don't store the raw HTML but extract text
                            logger.info(f"HTML content detected, will extract text only: {content_type}")
                            return None, filename, content_type
                    else:
                        logger.warning(f"Failed to download {url}: HTTP {response.status}")
                        return None, None, None
                        
        except Exception as e:
            logger.warning(f"Error downloading file from {url}: {e}")
            return None, None, None

    def _extract_filename_from_response(self, response, url: str) -> str:
        """Extract filename from response headers or URL."""
        # Try Content-Disposition header first
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            try:
                filename = content_disposition.split('filename=')[1].strip('"')
                return filename
            except:
                pass
        
        # Fall back to URL path
        parsed_url = urlparse(url)
        path = parsed_url.path
        if path and '/' in path:
            filename = path.split('/')[-1]
            if filename and '.' in filename:
                return filename
        
        # Generate a filename based on URL
        domain = parsed_url.netloc.replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"regulatory_doc_{domain}_{timestamp}.pdf"

    async def _store_raw_file(self, file_data: bytes, filename: str, content_type: str) -> str:
        """
        Store raw file in Supabase storage.
        
        Returns:
            Storage path of the uploaded file
        """
        try:
            # Generate secure storage path
            file_id = str(uuid.uuid4())
            storage_path = f"regulatory/{datetime.now().strftime('%Y/%m')}/{file_id}_{filename}"
            
            # Prepare headers for storage upload
            headers = {
                'Authorization': f'Bearer {self.service_role_key}',
                'Content-Type': content_type,
                'apikey': self.service_role_key
            }
            
            # Upload to raw-documents bucket
            upload_url = f"{self.supabase_url}/storage/v1/object/raw-documents/{storage_path}"
            
            timeout = aiohttp.ClientTimeout(total=120)  # Longer timeout for file uploads
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

    async def process_document_list(self, document_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a structured list of documents with metadata."""
        urls = []
        for doc in document_list:
            if 'url' in doc:
                urls.append(doc['url'])
        
        return await self.process_regulatory_urls(urls)

async def main():
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python bulk_regulatory_processor.py <urls_file_or_single_url>")
        print("Examples:")
        print("  python bulk_regulatory_processor.py https://example.com/doc.pdf")
        print("  python bulk_regulatory_processor.py regulatory_urls.txt")
        print("  python bulk_regulatory_processor.py --healthcare-documents")
        sys.exit(1)
    
    input_arg = sys.argv[1]
    
    # Special flag to process curated healthcare documents
    if input_arg == '--healthcare-documents':
        from data.healthcare_regulatory_documents import get_healthcare_document_urls
        urls = get_healthcare_document_urls()
        print(f"Processing {len(urls)} curated healthcare regulatory documents...")
    elif input_arg.startswith(('http://', 'https://')):
        urls = [input_arg]
    else:
        # Read URLs from file
        urls_file = Path(input_arg)
        if not urls_file.exists():
            print(f"File not found: {urls_file}")
            sys.exit(1)
        
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"Processing {len(urls)} regulatory document URLs...")
    
    processor = UnifiedRegulatoryProcessor()
    results = await processor.process_regulatory_urls(urls)
    
    # Print results
    print("\n" + "="*70)
    print("BULK REGULATORY PROCESSING RESULTS")
    print("="*70)
    print(f"✅ Successfully processed: {len(results['processed'])}")
    print(f"🔄 Duplicates skipped: {len(results['duplicates'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"📊 Total vectors created: {results['total_vectors_created']}")
    print(f"⏱️  Processing time: {results['processing_time']:.2f} seconds")
    
    if results['processed']:
        print("\nSuccessfully processed documents:")
        for doc in results['processed']:
            storage_info = f"📁 {doc.get('filename', 'N/A')}" if doc.get('storage_path') else "🌐 Text only"
            print(f"  📄 {doc['title'][:50]}...")
            print(f"      Vectors: {doc['vector_count']} | {storage_info} | Size: {doc.get('file_size', 'N/A')} bytes")
    
    if results['failed']:
        print("\nFailed URLs:")
        for failed in results['failed']:
            print(f"  ❌ {failed['url']}: {failed['error']}")
    
    # Save detailed results
    results_file = f"regulatory_processing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main()) 