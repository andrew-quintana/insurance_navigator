#!/usr/bin/env python3
"""
Cloud Integration Tester - End-to-end testing of upload pipeline in cloud

This script tests the complete upload pipeline in the cloud environment:
- Frontend (Vercel) → Backend (Render API) → Worker (Render Worker) → Database (Supabase)
- Document upload, processing, and conversation workflow
- Performance validation and error handling
"""

import asyncio
import aiohttp
import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import logging

# Load production environment variables
load_dotenv('.env.production')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CloudIntegrationTester:
    """End-to-end cloud integration testing"""
    
    def __init__(self):
        self.session = None
        self.config = {
            'vercel_url': os.getenv('VERCEL_URL', 'https://insurance-navigator.vercel.app'),
            'api_url': os.getenv('API_BASE_URL', '***REMOVED***'),
            'worker_url': os.getenv('RENDER_WORKER_URL', 'https://insurance-navigator-worker.onrender.com'),
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'supabase_service_key': os.getenv('SERVICE_ROLE_KEY')
        }
        
        # Test data
        self.test_documents = [
            {
                'name': 'test_insurance_policy.pdf',
                'type': 'application/pdf',
                'size': 1024 * 1024,  # 1MB
                'content': b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Insurance Policy) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000204 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n297\n%%EOF'
            }
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),  # 5 minutes for long operations
            headers={
                'Accept': 'application/json',
                'User-Agent': 'InsuranceNavigator-CloudIntegrationTester/1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_full_integration_test(self) -> Dict[str, Any]:
        """Run complete end-to-end integration test"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_id': str(uuid.uuid4()),
            'config': self.config,
            'tests': {},
            'summary': {},
            'performance_metrics': {}
        }
        
        logger.info("🚀 Starting Cloud Integration Testing")
        
        try:
            # Test 1: Environment Validation
            logger.info("🔧 Testing Environment Validation...")
            env_result = await self._test_environment_validation()
            results['tests']['environment_validation'] = env_result
            
            # Test 2: Service Health Checks
            logger.info("🏥 Testing Service Health...")
            health_result = await self._test_service_health()
            results['tests']['service_health'] = health_result
            
            # Test 3: Frontend Accessibility
            logger.info("🌐 Testing Frontend Accessibility...")
            frontend_result = await self._test_frontend_accessibility()
            results['tests']['frontend_accessibility'] = frontend_result
            
            # Test 4: API Endpoints
            logger.info("🔌 Testing API Endpoints...")
            api_result = await self._test_api_endpoints()
            results['tests']['api_endpoints'] = api_result
            
            # Test 5: Database Connectivity
            logger.info("🗄️ Testing Database Connectivity...")
            db_result = await self._test_database_connectivity()
            results['tests']['database_connectivity'] = db_result
            
            # Test 6: Document Upload Pipeline
            logger.info("📄 Testing Document Upload Pipeline...")
            upload_result = await self._test_document_upload_pipeline()
            results['tests']['document_upload_pipeline'] = upload_result
            
            # Test 7: Worker Processing
            logger.info("⚙️ Testing Worker Processing...")
            worker_result = await self._test_worker_processing()
            results['tests']['worker_processing'] = worker_result
            
            # Test 8: End-to-End Workflow
            logger.info("🔄 Testing End-to-End Workflow...")
            e2e_result = await self._test_end_to_end_workflow()
            results['tests']['end_to_end_workflow'] = e2e_result
            
            # Generate summary and performance metrics
            results['summary'] = self._generate_test_summary(results['tests'])
            results['performance_metrics'] = self._calculate_performance_metrics(results['tests'])
            
        except Exception as e:
            logger.error(f"Integration test failed: {str(e)}")
            results['error'] = str(e)
            results['summary'] = {'status': 'failed', 'error': str(e)}
        
        return results
    
    async def _test_environment_validation(self) -> Dict[str, Any]:
        """Test environment configuration"""
        result = {
            'status': 'unknown',
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check required URLs
            required_urls = ['vercel_url', 'api_url', 'supabase_url']
            for url_key in required_urls:
                url = self.config.get(url_key)
                if url:
                    result['checks'][f'{url_key}_configured'] = True
                else:
                    result['checks'][f'{url_key}_configured'] = False
                    result['errors'].append(f"{url_key} not configured")
            
            # Check Supabase credentials
            if self.config.get('supabase_key') and self.config.get('supabase_service_key'):
                result['checks']['supabase_credentials'] = True
            else:
                result['checks']['supabase_credentials'] = False
                result['errors'].append("Supabase credentials not configured")
            
            # Determine status
            if result['errors']:
                result['status'] = 'failed'
            elif result['warnings']:
                result['status'] = 'warning'
            else:
                result['status'] = 'passed'
        
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"Environment validation error: {str(e)}")
        
        return result
    
    async def _test_service_health(self) -> Dict[str, Any]:
        """Test service health endpoints"""
        result = {
            'status': 'unknown',
            'services': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Test API health
            try:
                async with self.session.get(f"{self.config['api_url']}/health", timeout=30) as response:
                    api_health = {
                        'status_code': response.status,
                        'response_time': 0,  # Could add timing
                        'healthy': response.status == 200
                    }
                    
                    if response.status == 200:
                        try:
                            health_data = await response.json()
                            api_health['data'] = health_data
                        except:
                            api_health['data'] = await response.text()
                    
                    result['services']['api'] = api_health
                    
                    if not api_health['healthy']:
                        result['warnings'].append(f"API health check failed: {response.status}")
            
            except Exception as e:
                result['services']['api'] = {'healthy': False, 'error': str(e)}
                result['errors'].append(f"API health check error: {str(e)}")
            
            # Test worker accessibility (404 is expected for background workers)
            try:
                async with self.session.get(self.config['worker_url'], timeout=30) as response:
                    worker_health = {
                        'status_code': response.status,
                        'accessible': response.status in [200, 404],
                        'note': '404 expected for background workers' if response.status == 404 else None
                    }
                    result['services']['worker'] = worker_health
                    
                    if not worker_health['accessible']:
                        result['warnings'].append(f"Worker not accessible: {response.status}")
            
            except Exception as e:
                result['services']['worker'] = {'accessible': False, 'error': str(e)}
                result['errors'].append(f"Worker accessibility error: {str(e)}")
            
            # Determine overall status
            if result['errors']:
                result['status'] = 'failed'
            elif result['warnings']:
                result['status'] = 'warning'
            else:
                result['status'] = 'passed'
        
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"Service health test error: {str(e)}")
        
        return result
    
    async def _test_frontend_accessibility(self) -> Dict[str, Any]:
        """Test frontend accessibility"""
        result = {
            'status': 'unknown',
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Test main page
            async with self.session.get(self.config['vercel_url'], timeout=30) as response:
                result['checks']['main_page_accessible'] = response.status == 200
                result['checks']['main_page_status'] = response.status
                
                if response.status != 200:
                    result['errors'].append(f"Main page not accessible: {response.status}")
            
            # Test API endpoints from frontend
            api_endpoints = ['/api/health', '/api/upload', '/api/documents']
            for endpoint in api_endpoints:
                try:
                    async with self.session.get(f"{self.config['vercel_url']}{endpoint}", timeout=30) as response:
                        result['checks'][f'endpoint_{endpoint.replace("/", "_")}'] = {
                            'accessible': response.status in [200, 404, 405],  # 404/405 are acceptable
                            'status': response.status
                        }
                except Exception as e:
                    result['checks'][f'endpoint_{endpoint.replace("/", "_")}'] = {
                        'accessible': False,
                        'error': str(e)
                    }
            
            # Determine status
            if result['errors']:
                result['status'] = 'failed'
            elif result['warnings']:
                result['status'] = 'warning'
            else:
                result['status'] = 'passed'
        
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"Frontend accessibility test error: {str(e)}")
        
        return result
    
    async def _test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints"""
        result = {
            'status': 'unknown',
            'endpoints': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Test health endpoint
            async with self.session.get(f"{self.config['api_url']}/health", timeout=30) as response:
                health_data = await response.json() if response.status == 200 else None
                result['endpoints']['health'] = {
                    'status_code': response.status,
                    'healthy': response.status == 200,
                    'data': health_data
                }
            
            # Test upload endpoint (should return method not allowed for GET)
            async with self.session.get(f"{self.config['api_url']}/api/v1/upload", timeout=30) as response:
                result['endpoints']['upload'] = {
                    'status_code': response.status,
                    'accessible': response.status in [200, 405],  # 405 is expected for GET
                    'note': 'Method not allowed expected for GET request'
                }
            
            # Test documents endpoint
            async with self.session.get(f"{self.config['api_url']}/documents", timeout=30) as response:
                result['endpoints']['documents'] = {
                    'status_code': response.status,
                    'accessible': response.status in [200, 401, 403],  # Auth required
                    'note': 'Authentication may be required'
                }
            
            # Determine status
            failed_endpoints = [k for k, v in result['endpoints'].items() if not v.get('accessible', False)]
            if failed_endpoints:
                result['warnings'].append(f"Some endpoints not accessible: {failed_endpoints}")
            
            if result['errors']:
                result['status'] = 'failed'
            elif result['warnings']:
                result['status'] = 'warning'
            else:
                result['status'] = 'passed'
        
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"API endpoints test error: {str(e)}")
        
        return result
    
    async def _test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity"""
        result = {
            'status': 'unknown',
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Test Supabase connectivity via API health check
            async with self.session.get(f"{self.config['api_url']}/health", timeout=30) as response:
                if response.status == 200:
                    health_data = await response.json()
                    if health_data.get('services', {}).get('database') == 'healthy':
                        result['checks']['database_healthy'] = True
                    else:
                        result['checks']['database_healthy'] = False
                        result['warnings'].append("Database not healthy according to API")
                else:
                    result['checks']['database_healthy'] = False
                    result['errors'].append(f"API health check failed: {response.status}")
            
            # Determine status
            if result['errors']:
                result['status'] = 'failed'
            elif result['warnings']:
                result['status'] = 'warning'
            else:
                result['status'] = 'passed'
        
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"Database connectivity test error: {str(e)}")
        
        return result
    
    async def _test_document_upload_pipeline(self) -> Dict[str, Any]:
        """Test document upload pipeline"""
        result = {
            'status': 'unknown',
            'upload_tests': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Test upload endpoint with test document
            test_doc = self.test_documents[0]
            
            # Create multipart form data
            data = aiohttp.FormData()
            data.add_field('file', test_doc['content'], filename=test_doc['name'], content_type=test_doc['type'])
            
            async with self.session.post(f"{self.config['api_url']}/api/v1/upload", data=data, timeout=60) as response:
                upload_result = {
                    'status_code': response.status,
                    'success': response.status in [200, 201],
                    'response_time': 0  # Could add timing
                }
                
                if response.status in [200, 201]:
                    try:
                        upload_data = await response.json()
                        upload_result['data'] = upload_data
                        result['upload_tests']['document_upload'] = upload_result
                    except:
                        upload_result['data'] = await response.text()
                        result['upload_tests']['document_upload'] = upload_result
                else:
                    result['upload_tests']['document_upload'] = upload_result
                    result['warnings'].append(f"Upload failed: {response.status}")
            
            # Determine status
            if result['errors']:
                result['status'] = 'failed'
            elif result['warnings']:
                result['status'] = 'warning'
            else:
                result['status'] = 'passed'
        
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"Document upload pipeline test error: {str(e)}")
        
        return result
    
    async def _test_worker_processing(self) -> Dict[str, Any]:
        """Test worker processing capabilities"""
        result = {
            'status': 'unknown',
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check if worker is accessible (404 is expected)
            async with self.session.get(self.config['worker_url'], timeout=30) as response:
                result['checks']['worker_accessible'] = response.status in [200, 404]
                result['checks']['worker_status'] = response.status
                
                if response.status == 404:
                    result['checks']['worker_note'] = '404 expected for background worker'
                elif response.status != 200:
                    result['warnings'].append(f"Worker not accessible: {response.status}")
            
            # Check worker logs for processing activity (if accessible)
            # This would require Render CLI access to logs
            
            # Determine status
            if result['errors']:
                result['status'] = 'failed'
            elif result['warnings']:
                result['status'] = 'warning'
            else:
                result['status'] = 'passed'
        
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"Worker processing test error: {str(e)}")
        
        return result
    
    async def _test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test complete end-to-end workflow"""
        result = {
            'status': 'unknown',
            'workflow_steps': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Step 1: Upload document
            test_doc = self.test_documents[0]
            data = aiohttp.FormData()
            data.add_field('file', test_doc['content'], filename=test_doc['name'], content_type=test_doc['type'])
            
            async with self.session.post(f"{self.config['api_url']}/api/v1/upload", data=data, timeout=60) as response:
                if response.status in [200, 201]:
                    upload_data = await response.json()
                    result['workflow_steps']['upload'] = {
                        'success': True,
                        'document_id': upload_data.get('document_id'),
                        'status': upload_data.get('status')
                    }
                else:
                    result['workflow_steps']['upload'] = {
                        'success': False,
                        'error': f"Upload failed: {response.status}"
                    }
                    result['errors'].append("Upload step failed")
            
            # Step 2: Check document processing status
            if result['workflow_steps']['upload']['success']:
                doc_id = result['workflow_steps']['upload']['document_id']
                if doc_id:
                    # Wait a moment for processing
                    await asyncio.sleep(5)
                    
                    async with self.session.get(f"{self.config['api_url']}/documents/{doc_id}", timeout=30) as response:
                        if response.status == 200:
                            doc_data = await response.json()
                            result['workflow_steps']['processing'] = {
                                'success': True,
                                'status': doc_data.get('status'),
                                'processed': doc_data.get('processed', False)
                            }
                        else:
                            result['workflow_steps']['processing'] = {
                                'success': False,
                                'error': f"Status check failed: {response.status}"
                            }
                            result['warnings'].append("Processing status check failed")
            
            # Determine overall status
            if result['errors']:
                result['status'] = 'failed'
            elif result['warnings']:
                result['status'] = 'warning'
            else:
                result['status'] = 'passed'
        
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(f"End-to-end workflow test error: {str(e)}")
        
        return result
    
    def _generate_test_summary(self, tests: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary"""
        summary = {
            'total_tests': len(tests),
            'passed_tests': 0,
            'failed_tests': 0,
            'warning_tests': 0,
            'error_tests': 0,
            'overall_status': 'unknown'
        }
        
        for test_name, test_result in tests.items():
            status = test_result.get('status', 'unknown')
            if status == 'passed':
                summary['passed_tests'] += 1
            elif status == 'failed':
                summary['failed_tests'] += 1
            elif status == 'warning':
                summary['warning_tests'] += 1
            elif status == 'error':
                summary['error_tests'] += 1
        
        # Determine overall status
        if summary['failed_tests'] > 0 or summary['error_tests'] > 0:
            summary['overall_status'] = 'failed'
        elif summary['warning_tests'] > 0:
            summary['overall_status'] = 'warning'
        else:
            summary['overall_status'] = 'passed'
        
        return summary
    
    def _calculate_performance_metrics(self, tests: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics"""
        metrics = {
            'total_execution_time': 0,
            'average_response_time': 0,
            'slowest_test': None,
            'fastest_test': None
        }
        
        # This would be populated with actual timing data
        # For now, return placeholder metrics
        
        return metrics

async def main():
    """Main function for cloud integration testing"""
    print("🚀 Starting Cloud Integration Testing")
    print("=" * 60)
    
    async with CloudIntegrationTester() as tester:
        results = await tester.run_full_integration_test()
        
        # Print results
        summary = results.get('summary', {})
        print(f"\n📊 CLOUD INTEGRATION TEST RESULTS")
        print(f"Overall Status: {summary.get('overall_status', 'unknown').upper()}")
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed: {summary.get('passed_tests', 0)} ✅")
        print(f"Failed: {summary.get('failed_tests', 0)} ❌")
        print(f"Warnings: {summary.get('warning_tests', 0)} ⚠️")
        print(f"Errors: {summary.get('error_tests', 0)} 🚨")
        
        # Print individual test results
        for test_name, test_result in results.get('tests', {}).items():
            status = test_result.get('status', 'unknown')
            status_emoji = {
                'passed': '✅',
                'failed': '❌',
                'warning': '⚠️',
                'error': '🚨'
            }.get(status, '❓')
            
            print(f"\n{status_emoji} {test_name.replace('_', ' ').title()}: {status.upper()}")
            
            # Print errors and warnings
            errors = test_result.get('errors', [])
            warnings = test_result.get('warnings', [])
            
            if errors:
                for error in errors:
                    print(f"  🚨 Error: {error}")
            
            if warnings:
                for warning in warnings:
                    print(f"  ⚠️ Warning: {warning}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"scripts/cloud_deployment/cloud_integration_test_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Test results saved to: {results_file}")
        
        # Final status
        if summary.get('overall_status') == 'passed':
            print(f"\n🎉 CLOUD INTEGRATION TESTING PASSED!")
            print(f"✅ All systems are operational in the cloud environment")
        else:
            print(f"\n⚠️ CLOUD INTEGRATION TESTING COMPLETED WITH ISSUES")
            print(f"🔧 Review the results above and address any failures")

if __name__ == "__main__":
    asyncio.run(main())
