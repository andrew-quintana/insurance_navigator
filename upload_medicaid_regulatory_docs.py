#!/usr/bin/env python3
"""
Upload Medicaid Regulatory Documents
Processes and uploads the comprehensive list of Medicaid and medical access regulatory documents
"""

import asyncio
import aiohttp
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MedicaidRegulatoryUploader:
    def __init__(self):
        load_dotenv()
        
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not all([self.supabase_url, self.service_role_key]):
            raise ValueError("Missing required environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        
        self.upload_results = []
        self.errors = []
        
    async def upload_regulatory_document(self, session: aiohttp.ClientSession, doc_info: Dict[str, Any], category: str) -> bool:
        """Upload a single regulatory document to the database"""
        
        try:
            # Prepare document data for insertion matching actual schema
            doc_data = {
                'raw_document_path': '',  # Required field, empty for web sources
                'title': doc_info['title'],
                'jurisdiction': doc_info.get('jurisdiction', 'federal').lower(),
                'program': ['Medicaid', 'CHIP'],  # Array field
                'document_type': doc_info.get('document_type', 'federal_guidance'),
                'effective_date': doc_info.get('effective_date'),
                'source_url': doc_info.get('url', ''),
                'tags': doc_info.get('key_areas', []) + [category, doc_info.get('priority', 'medium')],
                'summary': {
                    'text': f"Regulatory guidance covering: {', '.join(doc_info.get('key_areas', []))}",
                    'category': category,
                    'priority': doc_info.get('priority', 'medium'),
                    'key_areas': doc_info.get('key_areas', [])
                },
                'search_metadata': {
                    'upload_source': 'medicaid_regulatory_compilation',
                    'upload_date': datetime.now().isoformat(),
                    'document_category': category,
                    'priority': doc_info.get('priority', 'medium'),
                    'key_areas': doc_info.get('key_areas', [])
                },
                'extraction_method': 'automated_upload',
                'priority_score': 1.0 if doc_info.get('priority') == 'critical' else 0.8 if doc_info.get('priority') == 'high' else 0.5,
                'version': 1
            }
            
            # Insert into regulatory_documents table
            headers = {
                'Authorization': f'Bearer {self.service_role_key}',
                'Content-Type': 'application/json',
                'apikey': self.service_role_key
            }
            
            insert_url = f"{self.supabase_url}/rest/v1/regulatory_documents"
            
            async with session.post(insert_url, headers=headers, json=doc_data) as response:
                if response.status in [200, 201]:
                    response_data = await response.json()
                    # Extract document_id from response if available
                    doc_id = None
                    if isinstance(response_data, list) and len(response_data) > 0:
                        doc_id = response_data[0].get('document_id')
                    elif isinstance(response_data, dict):
                        doc_id = response_data.get('document_id')
                    
                    logger.info(f"✅ Successfully uploaded: {doc_info['title']}")
                    self.upload_results.append({
                        'document': doc_info['title'],
                        'status': 'success',
                        'category': category,
                        'document_id': doc_id
                    })
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to upload {doc_info['title']}: {response.status} - {error_text}")
                    self.errors.append({
                        'document': doc_info['title'],
                        'error': f"HTTP {response.status}: {error_text}",
                        'category': category
                    })
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Exception uploading {doc_info['title']}: {e}")
            self.errors.append({
                'document': doc_info['title'],
                'error': str(e),
                'category': category
            })
            return False

    async def load_and_upload_documents(self):
        """Load the regulatory documents JSON and upload all documents"""
        
        logger.info("🚀 Starting Medicaid Regulatory Documents Upload")
        logger.info("=" * 60)
        
        try:
            # Load the documents list
            with open('regulatory_documents_medicaid_access.json', 'r') as f:
                data = json.load(f)
            
            documents_data = data['regulatory_documents_medicaid_access']
            categories = documents_data['categories']
            
            logger.info(f"📋 Found {len(categories)} categories with {documents_data['metadata']['total_documents']} total documents")
            
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                upload_tasks = []
                
                # Process each category
                for category_name, documents in categories.items():
                    logger.info(f"\n📂 Processing category: {category_name}")
                    logger.info(f"   Documents in category: {len(documents)}")
                    
                    for doc_info in documents:
                        # Create upload task
                        task = self.upload_regulatory_document(session, doc_info, category_name)
                        upload_tasks.append(task)
                
                # Execute all uploads concurrently
                logger.info(f"\n🔄 Uploading {len(upload_tasks)} documents concurrently...")
                results = await asyncio.gather(*upload_tasks, return_exceptions=True)
                
                # Process results
                successful_uploads = sum(1 for result in results if result is True)
                failed_uploads = len(upload_tasks) - successful_uploads
                
                logger.info(f"\n📊 Upload Summary:")
                logger.info(f"   ✅ Successful uploads: {successful_uploads}")
                logger.info(f"   ❌ Failed uploads: {failed_uploads}")
                logger.info(f"   📈 Success rate: {(successful_uploads/len(upload_tasks)*100):.1f}%")
                
                return successful_uploads, failed_uploads
                
        except Exception as e:
            logger.error(f"💥 Critical error during upload process: {e}")
            return 0, 0

    async def trigger_vector_processing(self):
        """Trigger vector processing for uploaded regulatory documents"""
        
        logger.info("\n🔗 Triggering vector processing for uploaded documents...")
        
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            headers = {
                'Authorization': f'Bearer {self.service_role_key}',
                'Content-Type': 'application/json',
                'apikey': self.service_role_key
            }
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Trigger bulk regulatory vector processing
                vector_url = f"{self.supabase_url}/functions/v1/vector-processor"
                
                payload = {
                    'action': 'bulk_regulatory_processing',
                    'source': 'medicaid_regulatory_compilation',
                    'timestamp': datetime.now().isoformat()
                }
                
                async with session.post(vector_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        logger.info("✅ Vector processing triggered successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.warning(f"⚠️ Vector processing trigger failed: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.warning(f"⚠️ Could not trigger vector processing: {e}")
            return False

    def generate_upload_report(self, successful_uploads: int, failed_uploads: int):
        """Generate a comprehensive upload report"""
        
        report = {
            'upload_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_documents': successful_uploads + failed_uploads,
                'successful_uploads': successful_uploads,
                'failed_uploads': failed_uploads,
                'success_rate': (successful_uploads / (successful_uploads + failed_uploads) * 100) if (successful_uploads + failed_uploads) > 0 else 0
            },
            'successful_documents': self.upload_results,
            'errors': self.errors,
            'categories_processed': list(set([result['category'] for result in self.upload_results])),
            'next_steps': [
                "Vector processing will generate embeddings for uploaded documents",
                "Documents are now available for RAG agent queries",
                "Monitor vector generation progress in Supabase logs",
                "Test regulatory query capabilities with sample questions"
            ]
        }
        
        # Save report
        report_file = f"medicaid_regulatory_upload_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Upload report saved to: {report_file}")
        return report

async def main():
    """Main upload orchestrator"""
    
    uploader = MedicaidRegulatoryUploader()
    
    try:
        # Upload documents
        successful, failed = await uploader.load_and_upload_documents()
        
        # Trigger vector processing
        if successful > 0:
            await uploader.trigger_vector_processing()
        
        # Generate report
        report = uploader.generate_upload_report(successful, failed)
        
        # Final summary
        if successful > 0:
            logger.info(f"\n🎉 Upload completed successfully!")
            logger.info(f"📊 {successful} documents uploaded and ready for RAG processing")
            logger.info(f"🔍 Your system can now answer questions about:")
            logger.info(f"   • Medicaid Access Requirements")
            logger.info(f"   • HCBS Payment Standards")
            logger.info(f"   • Network Adequacy Rules")
            logger.info(f"   • Federal Policy Guidance")
            logger.info(f"   • Quality Measures and Compliance")
            
            if failed > 0:
                logger.warning(f"⚠️ {failed} documents failed to upload - check report for details")
        else:
            logger.error("❌ No documents were uploaded successfully")
            
        return successful > 0
        
    except Exception as e:
        logger.error(f"💥 Upload process failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 