#!/usr/bin/env python3
"""
Unified Regulatory Document Uploader
Uses the new unified backend API to upload regulatory documents through the existing processing pipeline
"""

import asyncio
import aiohttp
import json
import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedRegulatoryUploader:
    def __init__(self):
        load_dotenv()
        
        # Backend API configuration
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        self.admin_email = os.getenv('ADMIN_EMAIL', 'admin@insurancenavigator.com')
        self.admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        self.session = None
        self.auth_token = None
        
        # Statistics
        self.stats = {
            'documents_uploaded': 0,
            'documents_failed': 0,
            'total_vectors_generated': 0,
            'errors': []
        }
    
    async def authenticate(self):
        """Authenticate with the backend API"""
        
        auth_payload = {
            "email": self.admin_email,
            "password": self.admin_password
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        try:
            async with self.session.post(f"{self.backend_url}/login", json=auth_payload) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    self.auth_token = auth_data['access_token']
                    logger.info("✅ Successfully authenticated with backend API")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Authentication failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    async def upload_regulatory_document(self, doc_info: Dict[str, Any]) -> bool:
        """Upload a single regulatory document via the unified API"""
        
        if not self.auth_token:
            logger.error("❌ No authentication token available")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        
        # Prepare request payload
        payload = {
            "source_url": doc_info['source_url'],
            "title": doc_info['title'],
            "document_type": "regulatory_document",
            "jurisdiction": doc_info.get('jurisdiction', 'federal'),
            "program": doc_info.get('program', ['medicaid']),
            "metadata": {
                "category": doc_info.get('category', 'general'),
                "effective_date": doc_info.get('effective_date'),
                "document_type": doc_info.get('document_type', 'guidance'),
                "tags": doc_info.get('tags', []),
                "summary": doc_info.get('summary', {}),
                "uploaded_via": "unified_api_script",
                "upload_timestamp": datetime.now().isoformat()
            }
        }
        
        try:
            logger.info(f"🔄 Uploading: {doc_info['title'][:60]}...")
            
            async with self.session.post(
                f"{self.backend_url}/api/documents/upload-regulatory", 
                json=payload, 
                headers=headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    logger.info(f"   ✅ Success: {result['document_id']}")
                    logger.info(f"   📊 Vectors: {result.get('estimated_vectors', 0)}")
                    logger.info(f"   📋 Status: {result.get('vector_processing_status', 'unknown')}")
                    
                    self.stats['documents_uploaded'] += 1
                    self.stats['total_vectors_generated'] += result.get('estimated_vectors', 0)
                    
                    return True
                    
                else:
                    error_text = await response.text()
                    logger.error(f"   ❌ Failed: {response.status} - {error_text}")
                    self.stats['documents_failed'] += 1
                    self.stats['errors'].append({
                        'title': doc_info['title'],
                        'url': doc_info['source_url'],
                        'error': f"HTTP {response.status}: {error_text}"
                    })
                    return False
                    
        except Exception as e:
            logger.error(f"   ❌ Exception: {e}")
            self.stats['documents_failed'] += 1
            self.stats['errors'].append({
                'title': doc_info['title'],
                'url': doc_info['source_url'],
                'error': str(e)
            })
            return False
    
    async def upload_regulatory_documents_batch(self, documents: List[Dict[str, Any]], batch_size: int = 3):
        """Upload regulatory documents in batches through the unified API"""
        
        logger.info("🚀 Starting Unified Regulatory Document Upload")
        logger.info("=" * 70)
        logger.info(f"📋 Total documents to process: {len(documents)}")
        logger.info(f"🔗 Backend URL: {self.backend_url}")
        logger.info(f"📦 Batch size: {batch_size}")
        
        # Authenticate first
        if not await self.authenticate():
            logger.error("❌ Authentication failed, cannot proceed")
            return False
        
        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(documents) + batch_size - 1) // batch_size
            
            logger.info(f"\n🔄 Processing Batch {batch_num}/{total_batches} ({len(batch)} documents)")
            logger.info("-" * 50)
            
            # Process batch concurrently
            tasks = [self.upload_regulatory_document(doc) for doc in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Report batch results
            successful = sum(1 for result in results if result is True)
            logger.info(f"   ✅ Batch {batch_num}: {successful}/{len(batch)} successful")
            
            # Small delay between batches to avoid overwhelming the backend
            if i + batch_size < len(documents):
                await asyncio.sleep(2)
        
        # Final report
        await self.print_final_report()
        
        # Cleanup
        if self.session:
            await self.session.close()
        
        return self.stats['documents_uploaded'] > 0
    
    async def print_final_report(self):
        """Print final upload statistics"""
        
        logger.info("\n" + "=" * 70)
        logger.info("🎉 Unified Regulatory Upload Complete!")
        logger.info(f"📊 Documents Uploaded: {self.stats['documents_uploaded']}")
        logger.info(f"📊 Documents Failed: {self.stats['documents_failed']}")
        logger.info(f"🧮 Total Vectors Generated: {self.stats['total_vectors_generated']}")
        logger.info(f"❌ Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            logger.info("\n⚠️ Upload Errors:")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                logger.info(f"   • {error['title'][:50]}...: {error['error']}")
        
        if self.stats['documents_uploaded'] > 0:
            logger.info(f"\n🎯 SUCCESS: {self.stats['documents_uploaded']} regulatory documents processed!")
            logger.info("🔍 Your RAG system now has regulatory vectors for semantic search!")

async def main():
    """Main execution function"""
    
    # Load the regulatory documents from our JSON file
    try:
        with open('regulatory_documents_medicaid_access.json', 'r') as f:
            regulatory_documents = json.load(f)
    except FileNotFoundError:
        logger.error("❌ regulatory_documents_medicaid_access.json not found")
        logger.info("💡 Please ensure the regulatory documents JSON file exists")
        return False
    except Exception as e:
        logger.error(f"❌ Error loading regulatory documents: {e}")
        return False
    
    # Initialize uploader
    uploader = UnifiedRegulatoryUploader()
    
    # Test with first 5 documents
    test_documents = regulatory_documents[:5]
    
    logger.info(f"📋 Testing with {len(test_documents)} documents")
    
    # Upload documents through unified API
    success = await uploader.upload_regulatory_documents_batch(test_documents)
    
    if success:
        logger.info("\n✅ Test upload completed successfully!")
        logger.info("🔧 To upload all documents, modify the script to use the full list")
        
        # Show how to verify results
        logger.info("\n🔍 To verify the upload, you can:")
        logger.info("   1. Check the regulatory_documents table in your database")
        logger.info("   2. Check the user_document_vectors table for regulatory vectors")
        logger.info("   3. Test semantic search through your chat interface")
        
    else:
        logger.error("\n❌ Upload failed. Check the logs for details.")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 