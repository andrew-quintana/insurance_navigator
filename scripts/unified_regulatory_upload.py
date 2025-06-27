#!/usr/bin/env python3
"""
Unified Regulatory Document Processor

This is the core regulatory upload processor that handles both single and bulk uploads.
- Single documents: Direct upload via process_single_regulatory_document()
- Bulk uploads: Calls single document processor in batches

Extracted from the working bulk_regulatory_processor.py logic to create a unified system.
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
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from urllib.parse import urlparse
import uuid

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from agents.regulatory.regulatory_isolated import create_isolated_regulatory_agent
    from db.services.db_pool import get_db_pool
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedRegulatoryUploadProcessor:
    """
    Unified processor for regulatory documents that handles both single and bulk uploads.
    Uses the same doc-parser Edge Function as user document uploads for consistent PDF processing.
    """
    
    def __init__(self):
        self.regulatory_agent = create_isolated_regulatory_agent()
        # Get Supabase configuration for Edge Function calls
        self.supabase_url = self.regulatory_agent.supabase_url
        self.service_role_key = self.regulatory_agent.supabase_key
        
    async def process_single_regulatory_document(
        self, 
        source_url: str,
        metadata_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a single regulatory document using the same pipeline as user uploads.
        
        For PDFs: Uses doc-parser Edge Function (same as user uploads)
        For HTML: Uses regulatory agent's HTML extraction
        """
        try:
            # Step 1: Extract content using appropriate method
            content_text, content_data, file_data, filename, content_type = await self._extract_content(source_url)
            
            # Step 2: Generate content hash for deduplication
            content_hash = hashlib.sha256(content_text.encode()).hexdigest()
            
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                # Check for existing document
                existing_doc = await conn.fetchrow("""
                    SELECT id, original_filename as title FROM documents 
                    WHERE file_hash = $1 AND document_type = 'regulatory'
                """, content_hash)
                
                if existing_doc:
                    logger.info(f"Duplicate document found: {existing_doc['title']}")
                    return {
                        'status': 'duplicate',
                        'url': source_url,
                        'existing_document_id': str(existing_doc['id']),
                        'title': existing_doc['title'],
                        'message': 'Document already exists with same content'
                    }
                
                # Step 3: Store raw file if it's a PDF/document
                storage_path = None
                if file_data and content_type and any(ct in content_type.lower() for ct in ['pdf', 'doc', 'docx']):
                    storage_path = await self._store_raw_file(file_data, filename, content_type)
                    if not storage_path:
                        logger.warning(f"Failed to store raw file for {source_url}, continuing with text-only")
                
                # Step 4: Prepare document metadata  
                title = content_data.get('title', filename or urlparse(source_url).path.split('/')[-1])
                jurisdiction = metadata_override.get('jurisdiction', 'United States') if metadata_override else 'United States'
                programs = metadata_override.get('programs', ['Healthcare', 'General']) if metadata_override else ['Healthcare', 'General']
                doc_type = 'regulatory'  # Always regulatory in this processor
                
                # Step 5: Insert into unified documents table
                doc_id = await conn.fetchval("""
                    INSERT INTO documents (
                        storage_path, original_filename, document_type, jurisdiction,
                        program, effective_date, expiration_date, source_url,
                        source_last_checked, file_hash, priority_score, metadata,
                        tags, status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    RETURNING id
                """,
                    storage_path or source_url,  # storage_path
                    title,  # original_filename
                    doc_type,  # document_type
                    jurisdiction,  # jurisdiction
                    programs,  # program
                    content_data.get('effective_date'),  # effective_date
                    content_data.get('expiration_date'),  # expiration_date
                    source_url,  # source_url
                    datetime.now(),  # source_last_checked
                    content_hash,  # file_hash
                    content_data.get('priority_score', 1.0),  # priority_score
                    json.dumps({  # metadata
                        'processing_timestamp': datetime.now().isoformat(),
                        'source_method': 'unified_regulatory_processor',
                        'content_length': len(content_text),
                        'file_size': len(file_data) if file_data else None,
                        'original_filename': filename,
                        'content_type': content_type,
                        'storage_path': storage_path,
                        'extraction_method': content_data.get('extraction_method', 'unknown'),
                        'metadata_override': metadata_override or {}
                    }),
                    content_data.get('tags', ['healthcare', 'regulatory']),  # tags
                    'completed',  # status
                    datetime.now(),  # created_at
                    datetime.now()  # updated_at
                )
                
                logger.info(f"Created document {doc_id} for {source_url}")
                
                # Step 6: Generate vectors
                try:
                    vector_ids = await self._create_document_vectors(
                        None,  # No longer need local embedding service
                        str(doc_id), 
                        content_text,
                        {
                            'title': title,
                            'url': source_url,
                            'document_type': doc_type,
                            'jurisdiction': jurisdiction,
                            'programs': programs,
                            'extraction_method': content_data.get('extraction_method', 'unknown')
                        }
                    )
                    
                    logger.info(f"Created {len(vector_ids)} vectors for document {doc_id}")
                    
                    return {
                        'status': 'success',
                        'url': source_url,
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
                        'content_type': content_type,
                        'extraction_method': content_data.get('extraction_method', 'unknown')
                    }
                    
                except Exception as vector_error:
                    logger.error(f"Vector creation failed for {doc_id}: {vector_error}")
                    return {
                        'status': 'processed_no_vectors',
                        'url': source_url,
                        'document_id': str(doc_id),
                        'vector_count': 0,
                        'vector_ids': [],
                        'title': title,
                        'content_length': len(content_text),
                        'jurisdiction': jurisdiction,
                        'programs': programs,
                        'storage_path': storage_path,
                        'file_size': len(file_data) if file_data else None,
                        'filename': filename,
                        'content_type': content_type,
                        'vector_error': str(vector_error),
                        'extraction_method': content_data.get('extraction_method', 'unknown')
                    }
                    
        except Exception as e:
            logger.error(f"Failed to process {source_url}: {e}")
            return {
                'status': 'failed',
                'url': source_url,
                'error': str(e)
            }
            
    async def _create_document_vectors(
        self, 
        embedding_service,  # Kept for compatibility but not used
        document_id: str, 
        content_text: str,
        metadata: Dict[str, Any]
    ) -> List[str]:
        """
        Create and store vectors for document content using OpenAI embeddings.
        Uses the same embedding model as the Edge Functions for consistency.
        """
        try:
            # Create text chunks (same as Edge Functions)
            chunk_size = 1000
            chunk_overlap = 200
            
            # Simple text chunking (consistent with Edge Function approach)
            chunks = []
            start = 0
            while start < len(content_text):
                end = start + chunk_size
                chunk = content_text[start:end]
                chunks.append(chunk)
                start = end - chunk_overlap
                if start >= len(content_text):
                    break
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            
            # Generate embeddings using OpenAI (same as Edge Functions)
            embeddings_list = []
            for i, chunk in enumerate(chunks):
                try:
                    # Use OpenAI text-embedding-3-small with 1536 dimensions (same as Edge Functions)
                    embedding = await self._generate_openai_embedding(chunk)
                    embeddings_list.append(embedding)
                    logger.debug(f"Generated embedding for chunk {i}: {len(embedding)} dimensions")
                except Exception as e:
                    logger.error(f"Failed to generate embedding for chunk {i}: {e}")
                    # Use zero vector as fallback (same as Edge Functions do)
                    embeddings_list.append([0.0] * 1536)
            
            # Store in unified document_vectors table
            pool = await get_db_pool()
            vector_ids = []
            
            async with pool.get_connection() as conn:
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
                    try:
                        chunk_metadata = {
                            **metadata, 
                            'chunk_index': i, 
                            'total_chunks': len(chunks),
                            'chunk_length': len(chunk),
                            'processed_at': datetime.now().isoformat(),
                            'extraction_method': metadata.get('extraction_method', 'unified_processor'),
                            'embedding_method': 'openai'  # Same as Edge Functions
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

    async def _extract_content_using_doc_parser(
        self, 
        file_data: bytes, 
        filename: str, 
        content_type: str,
        source_url: str
    ) -> Dict[str, Any]:
        """
        Extract content from PDF using the same doc-parser Edge Function as user uploads.
        
        This creates a temporary regulatory document record, uploads the file to storage,
        calls doc-parser, extracts the content, then cleans up.
        """
        temp_doc_id = None
        storage_path = None
        
        try:
            logger.info(f"Using doc-parser Edge Function for PDF extraction: {filename}")
            
            # Step 1: Store file in storage temporarily
            storage_path = await self._store_raw_file(file_data, filename, content_type)
            if not storage_path:
                raise Exception("Failed to upload file to storage for doc-parser processing")
            
            # Step 2: Create temporary regulatory document record for doc-parser
            pool = await get_db_pool()
            async with pool.get_connection() as conn:
                temp_doc_id = await conn.fetchval("""
                    INSERT INTO regulatory_documents (
                        raw_document_path, title, jurisdiction, program, document_type,
                        structured_contents, source_url, content_hash, 
                        extraction_method, priority_score, search_metadata,
                        tags, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    RETURNING document_id
                """,
                    storage_path,
                    f"temp_doc_parser_{filename}",
                    "United States",
                    ["Healthcare"],
                    "temporary_for_extraction",
                    json.dumps({"status": "temporary_for_doc_parser"}),
                    source_url,
                    hashlib.sha256(file_data).hexdigest(),
                    'doc_parser_temp',
                    1.0,
                    json.dumps({"temporary": True, "created_for": "doc_parser_extraction"}),
                    ["temporary"],
                    datetime.now(),
                    datetime.now()
                )
            
            logger.info(f"Created temporary regulatory document {temp_doc_id} for doc-parser")
            
            # Step 3: Call doc-parser Edge Function
            doc_parser_payload = {
                "documentId": str(temp_doc_id),
                "path": storage_path,
                "filename": filename,
                "contentType": content_type,
                "fileSize": len(file_data),
                "documentType": "regulatory"  # Tell doc-parser this is a regulatory document
            }
            
            extracted_text = await self._call_doc_parser_edge_function(doc_parser_payload)
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                raise Exception(f"Doc-parser returned insufficient content: {len(extracted_text) if extracted_text else 0} chars")
            
            logger.info(f"Doc-parser extracted {len(extracted_text)} characters from {filename}")
            
            return {
                'content': extracted_text,
                'title': filename.replace('.pdf', '').replace('_', ' ').title(),
                'content_type': 'pdf_extracted',
                'extraction_method': 'doc_parser_edge_function',
                'content_length': len(extracted_text),
                'source_url': source_url,
                'priority_score': 1.0,
                'metadata': {
                    'original_filename': filename,
                    'file_size': len(file_data),
                    'storage_path': storage_path,
                    'processed_by': 'doc_parser_edge_function'
                }
            }
            
        except Exception as e:
            logger.error(f"Doc-parser extraction failed for {filename}: {e}")
            raise Exception(f"Doc-parser extraction failed: {str(e)}")
            
        finally:
            # Step 4: Clean up temporary document record
            if temp_doc_id:
                try:
                    async with pool.get_connection() as conn:
                        await conn.execute("""
                            DELETE FROM regulatory_documents WHERE document_id = $1
                        """, temp_doc_id)
                    logger.info(f"Cleaned up temporary document {temp_doc_id}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary document {temp_doc_id}: {cleanup_error}")

    async def _call_doc_parser_edge_function(self, payload: Dict[str, Any]) -> str:
        """Call the doc-parser Edge Function and return extracted text."""
        try:
            headers = {
                'Authorization': f'Bearer {self.service_role_key}',
                'Content-Type': 'application/json',
                'apikey': self.service_role_key
            }
            
            url = f"{self.supabase_url}/functions/v1/doc-parser"
            
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout for processing
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('success'):
                            # Doc-parser returns extracted text directly in response
                            extracted_text = result.get('extractedText', '')
                            if extracted_text and len(extracted_text.strip()) > 50:
                                logger.info(f"Successfully extracted {len(extracted_text)} characters via doc-parser")
                                return extracted_text
                            else:
                                logger.error(f"Doc-parser returned insufficient content: {len(extracted_text)} chars")
                                raise Exception(f"Insufficient content from doc-parser: {len(extracted_text)} chars")
                        else:
                            logger.error(f"Doc-parser processing failed: {result}")
                            raise Exception(f"Doc-parser failed: {result.get('error', 'Unknown error')}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Doc-parser Edge Function failed: {response.status} - {error_text}")
                        raise Exception(f"Doc-parser HTTP error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error calling doc-parser Edge Function: {e}")
            raise

    async def process_bulk_regulatory_documents(
        self, 
        source_urls: List[str], 
        batch_size: int = 3,
        metadata_overrides: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process multiple regulatory documents by calling the single processor for each.
        
        Args:
            source_urls: List of document URLs to process
            batch_size: Number of documents to process concurrently
            metadata_overrides: Optional dict mapping URLs to metadata overrides
            
        Returns:
            Dict with aggregated results from all documents
        """
        results = {
            'processed': [],
            'failed': [],
            'duplicates': [],
            'total_vectors_created': 0,
            'processing_time': None,
            'start_time': datetime.now()
        }
        
        logger.info(f"Starting bulk processing of {len(source_urls)} regulatory documents")
        
        # Process in batches to avoid overwhelming servers
        for i in range(0, len(source_urls), batch_size):
            batch = source_urls[i:i + batch_size]
            batch_num = i//batch_size + 1
            logger.info(f"Processing batch {batch_num}: {len(batch)} URLs")
            
            # Create tasks for this batch
            batch_tasks = []
            for url in batch:
                metadata_override = metadata_overrides.get(url) if metadata_overrides else None
                task = self.process_single_regulatory_document(url, metadata_override)
                batch_tasks.append(task)
            
            # Execute batch
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Process results
            for url, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to process {url}: {result}")
                    results['failed'].append({'url': url, 'error': str(result)})
                else:
                    if result['status'] == 'duplicate':
                        results['duplicates'].append(result)
                        logger.info(f"Duplicate found: {url}")
                    elif result['status'] == 'success':
                        results['processed'].append(result)
                        results['total_vectors_created'] += result.get('vector_count', 0)
                        logger.info(f"Successfully processed: {url} ({result.get('vector_count', 0)} vectors)")
                    else:  # failed
                        results['failed'].append(result)
                        logger.error(f"Failed to process: {url} - {result.get('error')}")
            
            # Small delay between batches to be respectful to servers
            if i + batch_size < len(source_urls):
                await asyncio.sleep(2)
        
        results['processing_time'] = (datetime.now() - results['start_time']).total_seconds()
        return results
    
    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API (same as Edge Functions)."""
        import os
        
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise Exception("OPENAI_API_KEY environment variable not set")
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {openai_api_key}'
            }
            
            payload = {
                'input': text,
                'model': 'text-embedding-3-small',  # Same model as Edge Functions
                'dimensions': 1536  # Same dimensions as Edge Functions
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    'https://api.openai.com/v1/embeddings',
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['data'][0]['embedding']
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenAI API error: {response.status} - {error_text}")
                        raise Exception(f"OpenAI API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {e}")
            raise

    async def _download_file_from_url(self, url: str) -> tuple[Optional[bytes], Optional[str], Optional[str]]:
        """Download file content from URL."""
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
        """Store raw file in Supabase storage."""
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


# Global instance
_unified_processor = None

async def get_unified_regulatory_processor() -> UnifiedRegulatoryUploadProcessor:
    """Get or create the global unified processor instance."""
    global _unified_processor
    if _unified_processor is None:
        _unified_processor = UnifiedRegulatoryUploadProcessor()
    return _unified_processor


# CLI Interface for backwards compatibility
async def main():
    """Main execution function for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage: python unified_regulatory_upload.py <single_url_or_urls_file>")
        print("Examples:")
        print("  python unified_regulatory_upload.py https://example.com/doc.pdf")
        print("  python unified_regulatory_upload.py regulatory_urls.txt")
        sys.exit(1)
    
    input_arg = sys.argv[1]
    processor = await get_unified_regulatory_processor()
    
    # Check if it's a single URL or file
    if input_arg.startswith('http'):
        # Single URL
        print(f"Processing single regulatory document: {input_arg}")
        result = await processor.process_single_regulatory_document(input_arg)
        
        if result['status'] == 'success':
            print(f"✅ Success: {result['title']} ({result['vector_count']} vectors)")
        elif result['status'] == 'duplicate':
            print(f"🔄 Duplicate: {input_arg}")
        else:
            print(f"❌ Failed: {result['error']}")
    else:
        # File with URLs
        if not Path(input_arg).exists():
            print(f"Error: File {input_arg} not found")
            sys.exit(1)
        
        with open(input_arg, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"Processing {len(urls)} regulatory documents from {input_arg}")
        results = await processor.process_bulk_regulatory_documents(urls)
        
        # Print summary
        print("\n" + "="*70)
        print("UNIFIED REGULATORY PROCESSING RESULTS")
        print("="*70)
        print(f"✅ Successfully processed: {len(results['processed'])}")
        print(f"🔄 Duplicates skipped: {len(results['duplicates'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        print(f"📊 Total vectors created: {results['total_vectors_created']}")
        print(f"⏱️  Processing time: {results['processing_time']:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main()) 