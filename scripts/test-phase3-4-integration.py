#!/usr/bin/env python3
"""
Comprehensive Integration Test for Phase 3 & 4
Tests all V2 Upload System components before Phase 5

This script tests:
- Database schema and migrations
- Edge Functions deployment
- Storage bucket configuration  
- LlamaParse integration
- Real-time progress tracking
- Feature flags
- Client integration
"""

import asyncio
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncpg
from supabase import create_client, Client
import requests
from pathlib import Path

class Phase34IntegrationTester:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'detailed_results': {},
            'errors': [],
            'warnings': []
        }
        
        # Load configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.database_url = os.getenv('DATABASE_URL')
        self.llamaparse_api_key = os.getenv('LLAMAPARSE_API_KEY')
        
        if not all([self.supabase_url, self.supabase_anon_key, self.supabase_service_key]):
            raise ValueError("Missing required Supabase environment variables")

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive integration tests for Phase 3 & 4"""
        print("🧪 Starting Phase 3 & 4 Integration Tests")
        print("=" * 60)
        
        test_suites = [
            ("Database Schema", self.test_database_schema),
            ("Edge Functions", self.test_edge_functions),
            ("Storage Configuration", self.test_storage_configuration),
            ("LlamaParse Integration", self.test_llamaparse_integration),
            ("Feature Flags", self.test_feature_flags),
            ("Real-time Progress", self.test_realtime_progress),
            ("Client Integration", self.test_client_integration),
            ("End-to-End Flow", self.test_end_to_end_flow)
        ]
        
        for suite_name, test_function in test_suites:
            try:
                print(f"\n🔍 Testing {suite_name}...")
                result = await test_function()
                self.results['detailed_results'][suite_name] = result
                
                if result['passed']:
                    print(f"✅ {suite_name}: PASSED")
                    self.results['tests_passed'] += 1
                else:
                    print(f"❌ {suite_name}: FAILED")
                    self.results['tests_failed'] += 1
                    
                self.results['tests_run'] += 1
                
            except Exception as e:
                print(f"❌ {suite_name}: ERROR - {str(e)}")
                self.results['detailed_results'][suite_name] = {
                    'passed': False,
                    'error': str(e),
                    'details': {}
                }
                self.results['tests_failed'] += 1
                self.results['tests_run'] += 1
                self.results['errors'].append(f"{suite_name}: {str(e)}")

        return self.generate_final_report()

    async def test_database_schema(self) -> Dict[str, Any]:
        """Test Phase 3/4 database schema and migrations"""
        result = {'passed': True, 'details': {}, 'issues': []}
        
        try:
            conn = await asyncpg.connect(self.database_url, statement_cache_size=0)
            
            # Test core V2 tables exist
            required_tables = [
                'documents', 'user_document_vectors', 'feature_flags', 
                'feature_flag_evaluations', 'realtime_progress_updates'
            ]
            
            for table in required_tables:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                result['details'][f'table_{table}'] = exists
                if not exists:
                    result['passed'] = False
                    result['issues'].append(f"Missing table: {table}")

            # Test key functions exist
            required_functions = [
                'update_document_progress', 'evaluate_feature_flag',
                'update_updated_at_column'
            ]
            
            for func in required_functions:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM pg_proc WHERE proname = $1)",
                    func
                )
                result['details'][f'function_{func}'] = exists
                if not exists:
                    result['passed'] = False
                    result['issues'].append(f"Missing function: {func}")

            # Test views exist
            required_views = [
                'document_processing_stats', 'failed_documents', 
                'stuck_documents', 'user_upload_stats'
            ]
            
            for view in required_views:
                exists = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.views WHERE table_name = $1)",
                    view
                )
                result['details'][f'view_{view}'] = exists
                if not exists:
                    result['passed'] = False
                    result['issues'].append(f"Missing view: {view}")

            # Test sample data operations
            try:
                # Test feature flag evaluation
                flag_result = await conn.fetchval(
                    "SELECT evaluate_feature_flag('test_flag', gen_random_uuid())"
                )
                result['details']['feature_flag_function_works'] = True
            except Exception as e:
                result['details']['feature_flag_function_works'] = False
                result['issues'].append(f"Feature flag function error: {str(e)}")

            await conn.close()
            
        except Exception as e:
            result['passed'] = False
            result['issues'].append(f"Database connection error: {str(e)}")
            
        return result

    async def test_edge_functions(self) -> Dict[str, Any]:
        """Test Edge Functions deployment and basic functionality"""
        result = {'passed': True, 'details': {}, 'issues': []}
        
        edge_functions = [
            'upload-handler',
            'processing-webhook', 
            'progress-tracker'
        ]
        
        for function_name in edge_functions:
            try:
                # Test function deployment (basic ping)
                url = f"{self.supabase_url}/functions/v1/{function_name}"
                
                # Test OPTIONS request (CORS)
                response = requests.options(url, timeout=10)
                cors_works = response.status_code in [200, 204]
                result['details'][f'{function_name}_cors'] = cors_works
                
                if not cors_works:
                    result['issues'].append(f"{function_name}: CORS not working")

                # Test basic connectivity
                if function_name == 'processing-webhook':
                    # Test webhook with mock data
                    mock_webhook = {
                        'source': 'test',
                        'status': 'completed',
                        'documentId': 'test-doc-id'
                    }
                    
                    response = requests.post(
                        url,
                        json=mock_webhook,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    # Expect 401/404 since we don't have valid auth/doc
                    webhook_deployed = response.status_code in [401, 404, 500]
                    result['details'][f'{function_name}_deployed'] = webhook_deployed
                    
                elif function_name == 'upload-handler':
                    # Test without auth (expect 401)
                    response = requests.post(url, json={}, timeout=10)
                    upload_deployed = response.status_code == 401
                    result['details'][f'{function_name}_deployed'] = upload_deployed
                    
                elif function_name == 'progress-tracker':
                    # Test without auth (expect 401)  
                    response = requests.get(url, timeout=10)
                    progress_deployed = response.status_code == 401
                    result['details'][f'{function_name}_deployed'] = progress_deployed

                if not result['details'].get(f'{function_name}_deployed', False):
                    result['passed'] = False
                    result['issues'].append(f"{function_name}: Not properly deployed")
                    
            except Exception as e:
                result['passed'] = False
                result['issues'].append(f"{function_name}: {str(e)}")
                result['details'][f'{function_name}_error'] = str(e)
                
        return result

    async def test_storage_configuration(self) -> Dict[str, Any]:
        """Test Supabase Storage bucket and policies"""
        result = {'passed': True, 'details': {}, 'issues': []}
        
        try:
            supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
            
            # Test documents bucket exists
            buckets = supabase.storage.list_buckets()
            documents_bucket_exists = any(b.name == 'documents' for b in buckets)
            result['details']['documents_bucket_exists'] = documents_bucket_exists
            
            if not documents_bucket_exists:
                result['passed'] = False
                result['issues'].append("Documents storage bucket not found")
            else:
                # Test bucket is accessible
                try:
                    files = supabase.storage.from_('documents').list()
                    result['details']['bucket_accessible'] = True
                except Exception as e:
                    result['details']['bucket_accessible'] = False
                    result['issues'].append(f"Bucket access error: {str(e)}")

            # Test RLS policies (attempt to access without proper auth)
            try:
                supabase_anon = create_client(self.supabase_url, self.supabase_anon_key)
                # This should fail due to RLS
                files = supabase_anon.storage.from_('documents').list()
                result['details']['rls_enforced'] = len(files) == 0
            except Exception:
                result['details']['rls_enforced'] = True  # Expected behavior

        except Exception as e:
            result['passed'] = False
            result['issues'].append(f"Storage test error: {str(e)}")
            
        return result

    async def test_llamaparse_integration(self) -> Dict[str, Any]:
        """Test LlamaParse integration components"""
        result = {'passed': True, 'details': {}, 'issues': []}
        
        # Test LlamaParse client files exist
        client_file = Path('db/supabase/functions/_shared/llamaparse-client.ts')
        result['details']['client_file_exists'] = client_file.exists()
        
        if not client_file.exists():
            result['passed'] = False
            result['issues'].append("LlamaParse client file missing")
        else:
            # Test client file has required exports
            content = client_file.read_text()
            required_exports = [
                'createLlamaParseClient', 'LlamaParseClient',
                'LlamaParseConfig', 'LlamaParseJobRequest'
            ]
            
            for export in required_exports:
                has_export = export in content
                result['details'][f'has_{export}'] = has_export
                if not has_export:
                    result['issues'].append(f"Missing export: {export}")

        # Test webhook URL configuration
        webhook_url = f"{self.supabase_url}/functions/v1/processing-webhook"
        result['details']['webhook_url'] = webhook_url
        
        # Test LlamaParse API key configuration
        if self.llamaparse_api_key:
            result['details']['api_key_configured'] = True
            result['details']['api_key_format'] = self.llamaparse_api_key.startswith('llx-')
        else:
            result['details']['api_key_configured'] = False
            result['issues'].append("LlamaParse API key not configured")

        return result

    async def test_feature_flags(self) -> Dict[str, Any]:
        """Test feature flag system"""
        result = {'passed': True, 'details': {}, 'issues': []}
        
        try:
            supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
            
            # Test feature flags table
            flags = supabase.table('feature_flags').select('*').execute()
            result['details']['feature_flags_accessible'] = True
            result['details']['existing_flags_count'] = len(flags.data)
            
            # Look for V2 upload flags
            v2_flags = [f for f in flags.data if 'v2' in f.get('flag_name', '').lower()]
            result['details']['v2_flags_count'] = len(v2_flags)
            
            # Test feature flag evaluation function
            test_result = supabase.rpc('evaluate_feature_flag', {
                'flag_name_param': 'test_flag',
                'user_id_param': '00000000-0000-0000-0000-000000000000'
            }).execute()
            
            result['details']['evaluation_function_works'] = True
            
        except Exception as e:
            result['passed'] = False
            result['issues'].append(f"Feature flags error: {str(e)}")
            
        return result

    async def test_realtime_progress(self) -> Dict[str, Any]:
        """Test real-time progress tracking"""
        result = {'passed': True, 'details': {}, 'issues': []}
        
        try:
            supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
            
            # Test realtime_progress_updates table
            progress_updates = supabase.table('realtime_progress_updates').select('*').limit(1).execute()
            result['details']['progress_table_accessible'] = True
            
            # Test inserting a progress update
            test_update = {
                'user_id': '00000000-0000-0000-0000-000000000000',
                'document_id': '00000000-0000-0000-0000-000000000000',
                'payload': {
                    'type': 'test',
                    'progress': 50,
                    'status': 'testing'
                }
            }
            
            insert_result = supabase.table('realtime_progress_updates').insert(test_update).execute()
            result['details']['can_insert_progress'] = len(insert_result.data) > 0
            
            # Clean up test data
            if insert_result.data:
                supabase.table('realtime_progress_updates').delete().eq('id', insert_result.data[0]['id']).execute()

        except Exception as e:
            result['passed'] = False
            result['issues'].append(f"Real-time progress error: {str(e)}")
            
        return result

    async def test_client_integration(self) -> Dict[str, Any]:
        """Test TypeScript client integration"""
        result = {'passed': True, 'details': {}, 'issues': []}
        
        # Test client file exists
        client_file = Path('db/supabase/client/v2-upload-client.ts')
        result['details']['client_file_exists'] = client_file.exists()
        
        if client_file.exists():
            content = client_file.read_text()
            
            # Test required interfaces and classes
            required_components = [
                'V2UploadClient', 'UploadProgress', 'UploadConfig',
                'createUploadClient', 'initializeUpload', 'completeUpload'
            ]
            
            for component in required_components:
                has_component = component in content
                result['details'][f'has_{component}'] = has_component
                if not has_component:
                    result['issues'].append(f"Missing component: {component}")
        else:
            result['passed'] = False
            result['issues'].append("Client file missing")

        return result

    async def test_end_to_end_flow(self) -> Dict[str, Any]:
        """Test complete upload flow simulation"""
        result = {'passed': True, 'details': {}, 'issues': []}
        
        try:
            supabase: Client = create_client(self.supabase_url, self.supabase_service_key)
            
            # Create a test user
            test_user_id = '00000000-0000-0000-0000-000000000001'
            
            # Test document creation
            test_document = {
                'user_id': test_user_id,
                'original_filename': 'test_integration.pdf',
                'file_size': 1024,
                'content_type': 'application/pdf',
                'file_hash': 'test_hash_123',
                'status': 'pending',
                'progress_percentage': 0,
                'total_chunks': 1,
                'processed_chunks': 0,
                'failed_chunks': 0,
                'storage_path': f'{test_user_id}/test_hash_123/test_integration.pdf'
            }
            
            doc_result = supabase.table('documents').insert(test_document).execute()
            result['details']['can_create_document'] = len(doc_result.data) > 0
            
            if doc_result.data:
                doc_id = doc_result.data[0]['id']
                result['details']['document_id'] = doc_id
                
                # Test document update
                update_result = supabase.table('documents').update({
                    'status': 'processing',
                    'progress_percentage': 50
                }).eq('id', doc_id).execute()
                
                result['details']['can_update_document'] = len(update_result.data) > 0
                
                # Test progress tracking
                progress_update = {
                    'user_id': test_user_id,
                    'document_id': doc_id,
                    'payload': {
                        'type': 'progress_update',
                        'progress': 50,
                        'status': 'processing'
                    }
                }
                
                progress_result = supabase.table('realtime_progress_updates').insert(progress_update).execute()
                result['details']['can_track_progress'] = len(progress_result.data) > 0
                
                # Clean up test data
                supabase.table('realtime_progress_updates').delete().eq('document_id', doc_id).execute()
                supabase.table('documents').delete().eq('id', doc_id).execute()
                
            else:
                result['passed'] = False
                result['issues'].append("Cannot create test document")

        except Exception as e:
            result['passed'] = False
            result['issues'].append(f"End-to-end test error: {str(e)}")
            
        return result

    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        success_rate = (self.results['tests_passed'] / self.results['tests_run'] * 100) if self.results['tests_run'] > 0 else 0
        
        report = {
            **self.results,
            'success_rate': round(success_rate, 2),
            'phase_3_4_ready': success_rate >= 85,
            'critical_issues': [],
            'recommendations': []
        }
        
        # Analyze critical issues
        for test_name, test_result in self.results['detailed_results'].items():
            if not test_result.get('passed', True):
                if test_name in ['Database Schema', 'Edge Functions']:
                    report['critical_issues'].append(f"CRITICAL: {test_name} failure")
                    
        # Generate recommendations
        if report['success_rate'] < 85:
            report['recommendations'].append("Fix critical failures before proceeding to Phase 5")
        elif report['success_rate'] < 95:
            report['recommendations'].append("Address warnings but can proceed to Phase 5")
        else:
            report['recommendations'].append("All systems ready for Phase 5!")
            
        return report

    def print_summary(self, report: Dict[str, Any]):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"🧪 PHASE 3 & 4 INTEGRATION TEST RESULTS")
        print(f"{'='*60}")
        print(f"Tests Run: {report['tests_run']}")
        print(f"Tests Passed: {report['tests_passed']}")
        print(f"Tests Failed: {report['tests_failed']}")
        print(f"Success Rate: {report['success_rate']}%")
        print(f"Phase 3/4 Ready: {'✅ YES' if report['phase_3_4_ready'] else '❌ NO'}")
        
        if report['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in report['critical_issues']:
                print(f"  - {issue}")
                
        if report['errors']:
            print(f"\n❌ ERRORS:")
            for error in report['errors'][:5]:  # Show first 5
                print(f"  - {error}")
                
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
            
        print(f"\n📊 DETAILED RESULTS:")
        for test_name, result in report['detailed_results'].items():
            status = "✅" if result.get('passed', True) else "❌"
            print(f"  {status} {test_name}")
            if not result.get('passed', True) and result.get('issues'):
                for issue in result['issues'][:2]:  # Show first 2 issues
                    print(f"      - {issue}")

async def main():
    """Run comprehensive Phase 3 & 4 integration tests"""
    tester = Phase34IntegrationTester()
    
    try:
        report = await tester.run_all_tests()
        tester.print_summary(report)
        
        # Save detailed report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'scripts/phase34_integration_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📋 Detailed report saved to: {report_file}")
        
        # Return appropriate exit code
        return 0 if report['phase_3_4_ready'] else 1
        
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main())) 