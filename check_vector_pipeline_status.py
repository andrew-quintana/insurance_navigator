#!/usr/bin/env python3
"""
Check Vector Pipeline Status
Analyzes the current state of regulatory documents and their vector processing
"""

import asyncio
import aiohttp
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_pipeline_status():
    """Check the complete vector pipeline status"""
    
    load_dotenv()
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    headers = {
        'Authorization': f'Bearer {service_role_key}',
        'Content-Type': 'application/json',
        'apikey': service_role_key
    }
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Check regulatory documents
        logger.info("🔍 Checking regulatory_documents table...")
        async with session.get(f"{supabase_url}/rest/v1/regulatory_documents?select=document_id,title,source_url,created_at", headers=headers) as response:
            if response.status == 200:
                reg_docs = await response.json()
                logger.info(f"📋 Found {len(reg_docs)} regulatory documents")
                
                # Show recent uploads
                recent_docs = sorted(reg_docs, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
                for doc in recent_docs:
                    logger.info(f"   ✅ {doc['title'][:60]}...")
            else:
                logger.error(f"❌ Failed to fetch regulatory documents: {response.status}")
                return
        
        # 2. Check user_document_vectors for regulatory documents
        logger.info("\n🔍 Checking user_document_vectors for regulatory documents...")
        vector_query = f"{supabase_url}/rest/v1/user_document_vectors?select=id,regulatory_document_id,document_source_type&document_source_type=eq.regulatory_document"
        async with session.get(vector_query, headers=headers) as response:
            if response.status == 200:
                vectors = await response.json()
                logger.info(f"📊 Found {len(vectors)} regulatory document vectors")
                
                if vectors:
                    # Group by regulatory_document_id
                    doc_counts = {}
                    for vector in vectors:
                        doc_id = vector.get('regulatory_document_id')
                        if doc_id:
                            doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
                    
                    logger.info(f"📈 Vectors distributed across {len(doc_counts)} documents:")
                    for doc_id, count in list(doc_counts.items())[:5]:
                        logger.info(f"   📄 {doc_id}: {count} vectors")
                else:
                    logger.warning("⚠️ No regulatory document vectors found!")
            else:
                logger.error(f"❌ Failed to fetch vectors: {response.status}")
        
        # 3. Check if we have the right table structure
        logger.info("\n🔍 Checking table schema compatibility...")
        
        # Check for document_vectors table (unified approach)
        try:
            async with session.get(f"{supabase_url}/rest/v1/document_vectors?select=id&limit=1", headers=headers) as response:
                if response.status == 200:
                    logger.info("✅ document_vectors table exists (unified approach)")
                elif response.status == 404:
                    logger.info("ℹ️ document_vectors table not found, using user_document_vectors")
        except:
            logger.info("ℹ️ Using user_document_vectors table approach")
        
        # 4. Identify gaps
        logger.info("\n🔧 Pipeline Gap Analysis:")
        
        if len(reg_docs) > 0 and len(vectors) == 0:
            logger.warning("🚨 GAP IDENTIFIED: Regulatory documents exist but no vectors generated")
            logger.info("💡 Solution: Need to trigger content extraction and vector processing")
        elif len(vectors) < len(reg_docs):
            logger.warning(f"🚨 PARTIAL GAP: {len(reg_docs)} documents but only {len(vectors)} vectors")
            logger.info("💡 Solution: Some documents may need reprocessing")
        else:
            logger.info("✅ Pipeline appears healthy")
        
        return len(reg_docs), len(vectors)

if __name__ == "__main__":
    asyncio.run(check_pipeline_status()) 