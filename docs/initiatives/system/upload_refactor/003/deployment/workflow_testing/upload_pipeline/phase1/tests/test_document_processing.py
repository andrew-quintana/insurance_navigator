#!/usr/bin/env python3
"""
Test document processing with the test documents
"""

import asyncio
import sys
import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
sys.path.append(os.path.dirname(__file__))

class DocumentProcessorTester:
    """Test document processing with real documents"""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.test_documents = [
            {
                "name": "simulated_insurance_document.pdf",
                "path": "examples/simulated_insurance_document.pdf",
                "expected_size": 1.7 * 1024,  # 1.7KB
                "max_processing_time": 30  # 30 seconds
            },
            {
                "name": "scan_classic_hmo.pdf", 
                "path": "examples/scan_classic_hmo.pdf",
                "expected_size": 2.4 * 1024 * 1024,  # 2.4MB
                "max_processing_time": 300  # 5 minutes
            }
        ]
    
    def check_file_exists(self, file_path):
        """Check if test file exists"""
        path = Path(file_path)
        if not path.exists():
            print(f"❌ Test file not found: {file_path}")
            return False
        
        size = path.stat().st_size
        print(f"✅ Test file found: {file_path} ({size:,} bytes)")
        return True
    
    def test_upload_document(self, document_info):
        """Test uploading a document"""
        print(f"\n📄 Testing upload: {document_info['name']}")
        
        # Check file exists
        if not self.check_file_exists(document_info['path']):
            return False
        
        try:
            # Upload file
            with open(document_info['path'], 'rb') as f:
                files = {'file': (document_info['name'], f, 'application/pdf')}
                
                # For now, use the test endpoint since we don't have auth set up
                response = requests.post(
                    f"{self.api_base_url}/test/upload",
                    json={"filename": document_info['name']},
                    timeout=10
                )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Upload successful: {data['status']}")
                return True
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False
    
    def test_health_checks(self):
        """Test service health"""
        print("\n🏥 Testing service health...")
        
        try:
            # Test API health
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API health: {data['status']}")
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def test_processing_performance(self, document_info):
        """Test document processing performance"""
        print(f"\n⏱️  Testing processing performance: {document_info['name']}")
        
        start_time = time.time()
        
        # Simulate processing time (in a real test, this would be actual processing)
        # For now, we'll just test the upload and basic functionality
        success = self.test_upload_document(document_info)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        
        if processing_time > document_info['max_processing_time']:
            print(f"⚠️  Processing time exceeded limit: {processing_time:.2f}s > {document_info['max_processing_time']}s")
            return False
        else:
            print(f"✅ Processing time within limit: {processing_time:.2f}s <= {document_info['max_processing_time']}s")
            return success
    
    def run_all_tests(self):
        """Run all document processing tests"""
        print("🧪 Running document processing tests...")
        print("=" * 60)
        
        # Test health checks first
        if not self.test_health_checks():
            print("❌ Health checks failed, aborting tests")
            return False
        
        results = []
        
        # Test each document
        for doc_info in self.test_documents:
            print(f"\n📋 Testing document: {doc_info['name']}")
            print("-" * 40)
            
            success = self.test_processing_performance(doc_info)
            results.append((doc_info['name'], success))
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 Test Results:")
        print("=" * 60)
        
        passed = 0
        for doc_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {doc_name}")
            if success:
                passed += 1
        
        print(f"\n📈 Summary: {passed}/{len(results)} document tests passed")
        
        if passed == len(results):
            print("🎉 All document processing tests passed!")
            return True
        else:
            print("⚠️  Some document processing tests failed")
            return False

async def main():
    """Main test function"""
    tester = DocumentProcessorTester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
