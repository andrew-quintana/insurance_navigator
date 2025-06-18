#!/usr/bin/env python3
"""
Simple Edge Function deployment test using Supabase API
Tests the deployment approach without Docker requirement
"""

import base64
import json
import logging
import os
import requests
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_function_bundle(function_path: Path) -> bytes:
    """Create a zip bundle for the function"""
    logger.info(f"📦 Creating bundle for: {function_path.name}")
    
    if not function_path.exists():
        raise FileNotFoundError(f"Function directory not found: {function_path}")
    
    if not (function_path / "index.ts").exists():
        raise FileNotFoundError(f"index.ts not found in {function_path}")
    
    # Create zip in memory
    import io
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add all files in the function directory
        for file_path in function_path.rglob('*'):
            if file_path.is_file():
                # Calculate relative path within the function
                rel_path = file_path.relative_to(function_path)
                zip_file.write(file_path, str(rel_path))
                logger.info(f"  Added: {rel_path}")
    
    zip_buffer.seek(0)
    bundle_data = zip_buffer.getvalue()
    
    logger.info(f"✅ Bundle created: {len(bundle_data)} bytes")
    return bundle_data

def deploy_function_test():
    """Test deployment of vector-processor function"""
    
    # Configuration
    project_ref = "jhrespvvhbnloxrieycf"
    function_name = "vector-processor"
    
    # You need to get this from: https://app.supabase.com/account/tokens
    access_token = os.getenv('SUPABASE_ACCESS_TOKEN')
    
    if not access_token:
        logger.error("❌ SUPABASE_ACCESS_TOKEN environment variable is required")
        logger.info("💡 Get your access token from: https://app.supabase.com/account/tokens")
        logger.info("💡 Then run: export SUPABASE_ACCESS_TOKEN='your_token_here'")
        return False
    
    logger.info(f"🚀 Testing deployment of {function_name}")
    logger.info(f"📍 Project: {project_ref}")
    
    try:
        # Create function bundle
        function_path = Path("db/supabase/functions") / function_name
        bundle_data = create_function_bundle(function_path)
        
        # Encode bundle as base64
        bundle_b64 = base64.b64encode(bundle_data).decode('utf-8')
        
        # Prepare deployment payload
        deployment_payload = {
            "slug": function_name,
            "body": bundle_b64,
            "verify_jwt": False  # Set based on your needs
        }
        
        # Deploy using Supabase API
        url = f"https://api.supabase.com/v1/projects/{project_ref}/functions"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"📡 Sending deployment request to: {url}")
        
        response = requests.post(url, json=deployment_payload, headers=headers)
        
        logger.info(f"📊 Response status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            logger.info("✅ Deployment successful!")
            
            if response.content:
                try:
                    response_data = response.json()
                    logger.info(f"📋 Response: {json.dumps(response_data, indent=2)}")
                except:
                    logger.info(f"📋 Response: {response.text}")
            
            # Test the deployed function
            logger.info("🧪 Testing deployed function...")
            test_function(project_ref, function_name, access_token)
            
            return True
        else:
            logger.error(f"❌ Deployment failed: {response.status_code}")
            logger.error(f"📋 Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                logger.error(f"📋 Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
            
            return False
            
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return False

def test_function(project_ref: str, function_name: str, access_token: str):
    """Test a deployed function"""
    try:
        # Test with a simple payload
        test_payload = {"test": True, "timestamp": datetime.now().isoformat()}
        
        url = f"https://{project_ref}.supabase.co/functions/v1/{function_name}"
        headers = {
            "Content-Type": "application/json",
            # "Authorization": f"Bearer {access_token}"  # Remove for functions with verify_jwt=false
        }
        
        logger.info(f"🧪 Testing function at: {url}")
        
        response = requests.post(url, json=test_payload, headers=headers, timeout=30)
        
        logger.info(f"🧪 Test response status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("✅ Function test successful!")
            logger.info(f"📋 Response: {response.text[:200]}...")
        else:
            logger.warning(f"⚠️ Function test returned: {response.status_code}")
            logger.warning(f"📋 Response: {response.text}")
            
    except Exception as e:
        logger.warning(f"⚠️ Function test error: {e}")

def main():
    """Main deployment test"""
    logger.info("🚀 Starting Supabase Edge Function API Deployment Test")
    
    success = deploy_function_test()
    
    if success:
        logger.info("🎉 API deployment test completed successfully!")
        logger.info("💡 You can now deploy all functions using this method")
    else:
        logger.error("❌ API deployment test failed")
        logger.info("💡 Check your access token and network connectivity")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 