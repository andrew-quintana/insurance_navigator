#!/usr/bin/env python3
"""
Trigger Regulatory Vector Processing
Processes vectors for all uploaded regulatory documents
"""

import asyncio
import aiohttp
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def trigger_regulatory_vector_processing():
    """Trigger vector processing for all regulatory documents"""
    
    load_dotenv()
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    logger.info("🔗 Starting regulatory document vector processing...")
    
    try:
        headers = {
            'Authorization': f'Bearer {service_role_key}',
            'Content-Type': 'application/json',
            'apikey': service_role_key
        }
        
        timeout = aiohttp.ClientTimeout(total=120)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            
            # First, get all regulatory documents that need vector processing
            query_url = f"{supabase_url}/rest/v1/regulatory_documents?select=document_id,title,source_url,summary&upload_status=eq.completed"
            
            async with session.get(query_url, headers=headers) as response:
                if response.status == 200:
                    documents = await response.json()
                    logger.info(f"📋 Found {len(documents)} regulatory documents to process")
                else:
                    logger.error(f"❌ Failed to fetch documents: {response.status}")
                    return False
            
            # Process each document for vector generation
            vector_tasks = []
            for doc in documents:
                if doc.get('source_url'):
                    # Trigger vector processing via bulk regulatory processor
                    vector_payload = {
                        'document_ids': [doc['document_id']],
                        'action': 'process_regulatory_vectors',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    vector_url = f"{supabase_url}/functions/v1/bulk-regulatory-processor"
                    task = session.post(vector_url, headers=headers, json=vector_payload)
                    vector_tasks.append(task)
            
            # Execute vector processing requests
            if vector_tasks:
                logger.info(f"🔄 Triggering vector processing for {len(vector_tasks)} documents...")
                
                # Process in smaller batches to avoid overwhelming the system
                batch_size = 5
                for i in range(0, len(vector_tasks), batch_size):
                    batch = vector_tasks[i:i+batch_size]
                    
                    responses = await asyncio.gather(*batch, return_exceptions=True)
                    
                    for j, response in enumerate(responses):
                        if isinstance(response, Exception):
                            logger.error(f"❌ Exception processing batch {i+j}: {response}")
                        else:
                            async with response:
                                if response.status == 200:
                                    logger.info(f"✅ Vector processing triggered for batch {i//batch_size + 1}")
                                else:
                                    error_text = await response.text()
                                    logger.warning(f"⚠️ Batch {i//batch_size + 1} failed: {response.status} - {error_text}")
                    
                    # Small delay between batches
                    if i + batch_size < len(vector_tasks):
                        await asyncio.sleep(2)
                
                logger.info("✅ Vector processing triggers completed")
                return True
            else:
                logger.warning("⚠️ No documents found that need vector processing")
                return False
                
    except Exception as e:
        logger.error(f"💥 Error triggering vector processing: {e}")
        return False

async def main():
    success = await trigger_regulatory_vector_processing()
    
    if success:
        logger.info("\n🎉 Regulatory vector processing initiated!")
        logger.info("📊 Monitor Supabase logs for processing progress")
        logger.info("🔍 Vectors will be available for RAG queries once processing completes")
    else:
        logger.error("\n❌ Failed to trigger vector processing")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 