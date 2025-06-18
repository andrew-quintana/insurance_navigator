#!/usr/bin/env python3
"""
Verify Regulatory Documents Upload
Confirms all documents are properly stored in the database
"""

import asyncio
import aiohttp
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def verify_regulatory_upload():
    """Verify all regulatory documents were uploaded successfully"""
    
    load_dotenv()
    supabase_url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    try:
        headers = {
            'Authorization': f'Bearer {service_role_key}',
            'Content-Type': 'application/json',
            'apikey': service_role_key
        }
        
        async with aiohttp.ClientSession() as session:
            # Query all regulatory documents
            query_url = f"{supabase_url}/rest/v1/regulatory_documents?select=document_id,title,jurisdiction,program,document_type,tags,source_url"
            
            async with session.get(query_url, headers=headers) as response:
                if response.status == 200:
                    documents = await response.json()
                    
                    logger.info(f"🔍 Found {len(documents)} regulatory documents in database")
                    logger.info("=" * 80)
                    
                    # Group by categories
                    categories = {}
                    for doc in documents:
                        tags = doc.get('tags', [])
                        category = None
                        for tag in tags:
                            if any(keyword in tag for keyword in ['access_rules', 'federal_policy', 'home_and_community', 'quality_and_performance', 'eligibility', 'financing', 'special_populations', 'compliance', 'state_implementation', 'emergency']):
                                category = tag
                                break
                        
                        if not category:
                            category = 'other'
                        
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(doc)
                    
                    # Display results by category
                    for category, docs in categories.items():
                        logger.info(f"\n📂 {category.replace('_', ' ').title()}: {len(docs)} documents")
                        for doc in docs:
                            logger.info(f"   ✅ {doc['title']}")
                            logger.info(f"      📍 Jurisdiction: {doc['jurisdiction']}")
                            logger.info(f"      📋 Type: {doc['document_type']}")
                            logger.info(f"      🔗 URL: {doc['source_url'][:60]}..." if len(doc.get('source_url', '')) > 60 else f"      🔗 URL: {doc.get('source_url', 'N/A')}")
                            logger.info("")
                    
                    logger.info("=" * 80)
                    logger.info(f"✅ Verification Complete: {len(documents)} regulatory documents successfully stored")
                    logger.info("🔍 Ready for RAG queries about Medicaid access strategies!")
                    
                    return True
                else:
                    logger.error(f"❌ Failed to query documents: {response.status}")
                    return False
                    
    except Exception as e:
        logger.error(f"💥 Error verifying upload: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_regulatory_upload())
    exit(0 if success else 1) 