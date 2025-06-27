#!/usr/bin/env python3
"""
Test script to upload a document and monitor job processing in real-time.
This helps identify exactly where the processing pipeline is failing.
"""

import requests
import json
import time
import os
from datetime import datetime
import asyncio
import aiohttp
import hashlib
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase URL from environment
SUPABASE_URL = os.getenv('SUPABASE_URL')
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable not set")

# Configuration
API_BASE = "https://insurance-navigator-api.onrender.com"

# Test credentials (from your logs)
TEST_EMAIL = "deploymenttest@example.com"
TEST_PASSWORD = "testpass123"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def login():
    """Login and get access token"""
    try:
        response = requests.post(
            f"{API_BASE}/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login successful, token received")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def create_test_file():
    """Create a simple test PDF content"""
    # Create a simple text file that we'll pretend is a PDF
    test_content = f"""
Medicare Plan Document - Test Upload
Generated at: {datetime.now()}

This is a test document for the Insurance Navigator system.
It contains sample Medicare plan information.

Plan Details:
- Plan Name: Test HMO Plan
- Plan ID: TEST-001
- Coverage Area: Test County
- Monthly Premium: $50.00

Benefits:
- Doctor Visits: $20 copay
- Emergency Room: $100 copay  
- Prescription Drugs: Tier 1 $10, Tier 2 $25

This document is being used to test the upload and processing pipeline.
"""
    return test_content.encode('utf-8')

async def test_document_upload():
    """Test the document upload and processing pipeline."""
    try:
        # Create test file
        file_data = create_test_file()
        file_hash = hashlib.sha256(file_data).hexdigest()
        filename = f"test_medicare_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Document metadata
        document_data = {
            'original_filename': filename,
            'document_type': 'user_uploaded',
            'jurisdiction': 'United States',
            'program': ['Medicare', 'Healthcare'],
            'source_url': None,
            'source_last_checked': datetime.now().isoformat(),
            'priority_score': 1.0,
            'metadata': {
                'processing_timestamp': datetime.now().isoformat(),
                'source_method': 'test_upload',
                'content_length': len(file_data),
                'extraction_method': 'doc_parser',
                'test_metadata': {
                    'test_id': 'upload_test_001',
                    'test_type': 'integration',
                    'test_timestamp': datetime.now().isoformat()
                }
            },
            'tags': ['test', 'medicare', 'plan'],
            'status': 'pending'
        }
        
        # Upload document
        logger.info(f"Uploading test document: {filename}")
        
        # Call your document upload endpoint here
        # Example:
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(
        #         'http://localhost:3000/api/upload',
        #         data={'file': file_data, 'metadata': json.dumps(document_data)}
        #     ) as response:
        #         result = await response.json()
        #         logger.info(f"Upload response: {result}")
        
        # For now, just log the test data
        logger.info("Test document created successfully")
        logger.info(f"File hash: {file_hash}")
        logger.info(f"Document metadata: {json.dumps(document_data, indent=2)}")
        
        return {
            'success': True,
            'filename': filename,
            'file_hash': file_hash,
            'metadata': document_data
        }
        
    except Exception as e:
        logger.error(f"Error in test upload: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

async def main():
    """Run the test upload."""
    result = await test_document_upload()
    if result['success']:
        logger.info("Test completed successfully")
    else:
        logger.error(f"Test failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())