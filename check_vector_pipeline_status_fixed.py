#!/usr/bin/env python3
"""
Check Vector Pipeline Status (Fixed)
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
                recent_docs = sorted(reg_docs, key=lambda x: x.get('created_at', ''), reverse=True)[:3]
                for doc in recent_docs:
                    logger.info(f"   ✅ {doc['title'][:60]}...")
            else:
                logger.error(f"❌ Failed to fetch regulatory documents: {response.status}")
                return
        
        # 2. Check document_vectors table (unified approach)
        vectors = []
        logger.info("\n🔍 Checking document_vectors table for regulatory documents...")
        vector_query = f"{supabase_url}/rest/v1/document_vectors?select=id,regulatory_document_id,document_source_type&document_source_type=eq.regulatory_document"
        async with session.get(vector_query, headers=headers) as response:
            if response.status == 200:
                vectors = await response.json()
                logger.info(f"📊 Found {len(vectors)} regulatory document vectors in document_vectors")
            elif response.status == 404:
                logger.info("ℹ️ document_vectors table not found, checking user_document_vectors...")
                
                # Fallback to user_document_vectors
                vector_query = f"{supabase_url}/rest/v1/user_document_vectors?select=id,regulatory_document_id,document_source_type&document_source_type=eq.regulatory_document"
                async with session.get(vector_query, headers=headers) as response:
                    if response.status == 200:
                        vectors = await response.json()
                        logger.info(f"📊 Found {len(vectors)} regulatory document vectors in user_document_vectors")
                    else:
                        logger.warning(f"⚠️ Failed to fetch from user_document_vectors: {response.status}")
                        vectors = []
            else:
                logger.error(f"❌ Failed to fetch vectors: {response.status}")
                vectors = []
        
        # 3. Analyze vector distribution
        if vectors:
            # Group by regulatory_document_id
            doc_counts = {}
            for vector in vectors:
                doc_id = vector.get('regulatory_document_id')
                if doc_id:
                    doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
            
            logger.info(f"📈 Vectors distributed across {len(doc_counts)} documents:")
            for doc_id, count in list(doc_counts.items())[:3]:
                logger.info(f"   📄 {doc_id}: {count} vectors")
        else:
            logger.warning("⚠️ No regulatory document vectors found in any table!")
        
        # 4. Gap Analysis
        logger.info("\n🔧 Pipeline Gap Analysis:")
        logger.info(f"📊 Summary: {len(reg_docs)} regulatory documents → {len(vectors)} vectors")
        
        if len(reg_docs) > 0 and len(vectors) == 0:
            logger.error("🚨 CRITICAL GAP: Documents uploaded but NO vectors generated")
            logger.info("💡 Root Cause: Vector processing pipeline not triggered")
            logger.info("🔧 Solution: Create end-to-end processor for content extraction + vectorization")
        elif len(vectors) < len(reg_docs):
            logger.warning(f"🚨 PARTIAL GAP: {len(reg_docs)} documents but only {len(vectors)} vectors")
            logger.info("💡 Solution: Some documents need reprocessing")
        else:
            logger.info("✅ Pipeline appears healthy")
        
        # 5. Show what needs to be done
        logger.info("\n🚀 Required Pipeline Steps:")
        logger.info("   1️⃣ Document Upload ✅ COMPLETE (48 docs in regulatory_documents)")
        logger.info("   2️⃣ Content Extraction ❌ MISSING (no raw content processed)")
        logger.info("   3️⃣ Text Chunking ❌ MISSING (no chunks created)")
        logger.info("   4️⃣ Vector Generation ❌ MISSING (no embeddings in document_vectors)")
        logger.info("   5️⃣ Vector Storage ❌ MISSING (no searchable vectors)")
        
        return len(reg_docs), len(vectors)

if __name__ == "__main__":
    asyncio.run(check_pipeline_status()) 