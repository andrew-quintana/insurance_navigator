#!/usr/bin/env python3
"""
Phase 5 Complete Verification Test

OBJECTIVE: Verify the claim that "Phase 5 Complete: Vector Processing Pipeline" 
by testing the entire document processing flow end-to-end.

TEST PLAN:
1. Test Edge Functions are deployed and responding
2. Test complete document upload pipeline
3. Verify vector processing works 
4. Test semantic search functionality
5. Validate no dependencies on unused shared modules
6. RCA any issues found

EXPECTED FLOW:
Document Upload → LlamaParse → Vector Processing → Database Storage → Search
"""

import asyncio
import aiohttp
import asyncpg
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback
import tempfile
import io
from pathlib import Path

class Phase5VerificationTest:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL', 'https://jhrespvvhbnloxrieycf.supabase.co')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.database_url = os.getenv('DATABASE_URL')
        
        # Test results tracking
        self.test_results = {
            'test_start': datetime.utcnow().isoformat(),
            'tests_passed': [],
            'tests_failed': [],
            'tests_skipped': [],
            'edge_functions_status': {},
            'pipeline_status': {},
            'vector_processing_status': {},
            'search_functionality_status': {},
            'rca_findings': []
        }
        
        # Edge Functions to test
        self.edge_functions = [
            'upload-handler',
            'processing-webhook', 
            'progress-tracker'
        ]
        
        print("🧪 Phase 5 Complete Verification Test Initialized")
        print(f"📡 Supabase URL: {self.supabase_url}")
        print(f"🔑 Service Key: {'✅ Present' if self.supabase_service_key else '❌ Missing'}")
        print(f"🗄️ Database: {'✅ Present' if self.database_url else '❌ Missing'}")

    async def run_complete_test(self):
        """Execute the complete Phase 5 verification test suite"""
        print("\n" + "="*60)
        print("🚀 STARTING PHASE 5 COMPLETE VERIFICATION TEST")
        print("="*60)
        
        try:
            # Test 1: Edge Functions Deployment Status
            await self.test_edge_functions_deployment()
            
            # Test 2: Database Vector Infrastructure  
            await self.test_vector_database_infrastructure()
            
            # Test 3: Main Server API Endpoints
            await self.test_main_server_endpoints()
            
            # Test 4: Document Upload Pipeline (if functions deployed)
            if any(status.get('deployed', False) for status in self.test_results['edge_functions_status'].values()):
                await self.test_document_upload_pipeline()
            else:
                self.test_results['tests_skipped'].append("Document upload pipeline (Edge Functions not deployed)")
            
            # Test 5: Vector Processing Integration
            await self.test_vector_processing_integration()
            
            # Test 6: Semantic Search Functionality
            await self.test_semantic_search()
            
            # Test 7: Shared Module Dependency Check
            await self.test_shared_module_dependencies()
            
            # Generate comprehensive test report
            await self.generate_test_report()
            
        except Exception as e:
            print(f"❌ CRITICAL TEST FAILURE: {e}")
            traceback.print_exc()
            self.test_results['tests_failed'].append(f"Critical test failure: {str(e)}")
        
        finally:
            print("\n" + "="*60)
            print("📊 PHASE 5 VERIFICATION TEST COMPLETE")
            print("="*60)

    async def test_edge_functions_deployment(self):
        """Test 1: Verify Edge Functions are deployed and responding"""
        print("\n🔍 TEST 1: Edge Functions Deployment Status")
        print("-" * 40)
        
        async with aiohttp.ClientSession() as session:
            for func_name in self.edge_functions:
                func_url = f"{self.supabase_url}/functions/v1/{func_name}"
                
                try:
                    print(f"📡 Testing {func_name}: {func_url}")
                    
                    # Test OPTIONS for CORS
                    async with session.options(func_url) as response:
                        cors_status = response.status in [200, 204]
                        print(f"   CORS: {'✅' if cors_status else '❌'} (Status: {response.status})")
                    
                    # Test GET/POST to see if function responds (expect auth error)
                    async with session.get(func_url) as response:
                        function_exists = response.status != 404
                        expects_auth = response.status == 401
                        
                        status_info = {
                            'deployed': function_exists,
                            'cors_enabled': cors_status,
                            'requires_auth': expects_auth,
                            'status_code': response.status,
                            'url': func_url
                        }
                        
                        self.test_results['edge_functions_status'][func_name] = status_info
                        
                        if function_exists:
                            print(f"   Function: ✅ Deployed (Status: {response.status})")
                            if expects_auth:
                                print(f"   Auth: ✅ Required (correctly secured)")
                            self.test_results['tests_passed'].append(f"Edge Function {func_name} deployed")
                        else:
                            print(f"   Function: ❌ Not Found (Status: {response.status})")
                            self.test_results['tests_failed'].append(f"Edge Function {func_name} not deployed")
                            self.test_results['rca_findings'].append(f"RCA: {func_name} not deployed - likely needs manual deployment via Dashboard")
                
                except Exception as e:
                    print(f"   Error: ❌ {str(e)}")
                    self.test_results['tests_failed'].append(f"Edge Function {func_name} test failed: {str(e)}")
                    self.test_results['rca_findings'].append(f"RCA: {func_name} connection failed - check URL or network")

    async def test_vector_database_infrastructure(self):
        """Test 2: Verify vector database tables and pgvector extension"""
        print("\n🗄️ TEST 2: Vector Database Infrastructure")
        print("-" * 40)
        
        if not self.database_url:
            print("❌ Database URL not configured")
            self.test_results['tests_failed'].append("Database URL missing")
            return
        
        try:
            # Connect with statement cache disabled for compatibility
            conn = await asyncpg.connect(self.database_url, statement_cache_size=0)
            print("✅ Database connection established")
            
            # Test pgvector extension
            try:
                pgvector_check = await conn.fetchval("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                if pgvector_check:
                    print("✅ pgvector extension installed")
                    self.test_results['tests_passed'].append("pgvector extension available")
                else:
                    print("❌ pgvector extension not found")
                    self.test_results['tests_failed'].append("pgvector extension missing")
            except Exception as e:
                print(f"❌ pgvector check failed: {e}")
                self.test_results['tests_failed'].append(f"pgvector check error: {str(e)}")
            
            # Test required tables
            required_tables = [
                'user_document_vectors',
                'documents', 
                'processing_progress'
            ]
            
            for table in required_tables:
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    print(f"✅ Table {table}: {count} rows")
                    self.test_results['tests_passed'].append(f"Table {table} exists with {count} rows")
                except Exception as e:
                    print(f"❌ Table {table}: Error - {e}")
                    self.test_results['tests_failed'].append(f"Table {table} missing or inaccessible")
                    self.test_results['rca_findings'].append(f"RCA: Table {table} issue - may need migration")
            
            # Test vector table structure
            try:
                vector_columns = await conn.fetch("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_document_vectors'
                    ORDER BY ordinal_position
                """)
                
                print(f"📊 user_document_vectors schema:")
                vector_embedding_exists = False
                for col in vector_columns:
                    print(f"   - {col['column_name']}: {col['data_type']}")
                    if 'embedding' in col['column_name'].lower():
                        vector_embedding_exists = True
                
                if vector_embedding_exists:
                    print("✅ Vector embedding columns found")
                    self.test_results['tests_passed'].append("Vector embedding columns present")
                else:
                    print("❌ No vector embedding columns found")
                    self.test_results['tests_failed'].append("Vector embedding columns missing")
                    self.test_results['rca_findings'].append("RCA: Vector columns missing - schema may need updates")
                    
            except Exception as e:
                print(f"❌ Vector table schema check failed: {e}")
                self.test_results['tests_failed'].append(f"Vector schema check failed: {str(e)}")
            
            await conn.close()
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.test_results['tests_failed'].append(f"Database connection failed: {str(e)}")
            self.test_results['rca_findings'].append("RCA: Database connection failed - check credentials and network")

    async def test_main_server_endpoints(self):
        """Test 3: Verify main server API endpoints are working"""
        print("\n🌐 TEST 3: Main Server API Endpoints")
        print("-" * 40)
        
        # Test health endpoint
        try:
            async with aiohttp.ClientSession() as session:
                # Health check
                async with session.get('http://localhost:8000/health') as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ Health endpoint: {health_data.get('status', 'unknown')}")
                        print(f"   Database: {health_data.get('database', 'unknown')}")
                        self.test_results['tests_passed'].append("Main server health endpoint working")
                    else:
                        print(f"❌ Health endpoint failed: {response.status}")
                        self.test_results['tests_failed'].append(f"Health endpoint failed: {response.status}")
                
                # Test embeddings endpoint (for Edge Functions)
                async with session.post(
                    'http://localhost:8000/api/embeddings',
                    json={'text': 'test embedding'},
                    headers={'Authorization': 'Bearer test-token'}
                ) as response:
                    if response.status in [200, 401]:  # 401 is fine, means endpoint exists
                        print(f"✅ Embeddings endpoint: Responds (Status: {response.status})")
                        self.test_results['tests_passed'].append("Embeddings endpoint available")
                    else:
                        print(f"❌ Embeddings endpoint: {response.status}")
                        self.test_results['tests_failed'].append(f"Embeddings endpoint failed: {response.status}")
                        
        except Exception as e:
            print(f"❌ Main server test failed: {e}")
            self.test_results['tests_failed'].append(f"Main server test failed: {str(e)}")
            self.test_results['rca_findings'].append("RCA: Main server not running - start with 'python main.py'")

    async def test_document_upload_pipeline(self):
        """Test 4: Test document upload pipeline if Edge Functions are deployed"""
        print("\n📄 TEST 4: Document Upload Pipeline")
        print("-" * 40)
        
        # Create a test document
        test_content = """
        INSURANCE POLICY TEST DOCUMENT
        
        Policy Number: TEST-001
        Policyholder: Test User
        Coverage: Medicare Supplement Plan F
        
        This is a test document for verifying the document processing pipeline.
        It contains sample insurance policy information that should be processed
        through LlamaParse (or fallback), chunked, and converted to vector embeddings.
        
        Benefits covered:
        - Hospital services
        - Medical services
        - Prescription drugs
        - Preventive care
        
        Deductible: $200
        Out-of-pocket maximum: $2000
        Premium: $150/month
        """
        
        # Save as temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            test_file_path = f.name
        
        try:
            print(f"📝 Created test document: {len(test_content)} characters")
            print("⚠️ Note: Upload pipeline test requires valid auth token")
            print("   This test verifies endpoint structure, not full pipeline")
            
            # Test upload endpoint structure
            upload_url = f"{self.supabase_url}/functions/v1/upload-handler"
            
            async with aiohttp.ClientSession() as session:
                # Test OPTIONS (CORS)
                async with session.options(upload_url) as response:
                    print(f"📡 Upload CORS: {'✅' if response.status in [200, 204] else '❌'} (Status: {response.status})")
                
                # Test POST (expect auth required)
                async with session.post(upload_url, json={'test': 'data'}) as response:
                    if response.status == 401:
                        print("✅ Upload endpoint: Requires authentication (correctly secured)")
                        self.test_results['tests_passed'].append("Upload endpoint security working")
                    elif response.status == 404:
                        print("❌ Upload endpoint: Not found (function not deployed)")
                        self.test_results['tests_failed'].append("Upload endpoint not found")
                    else:
                        print(f"⚠️ Upload endpoint: Unexpected status {response.status}")
                        self.test_results['tests_failed'].append(f"Upload endpoint unexpected status: {response.status}")
                        
            self.test_results['pipeline_status']['upload_endpoint'] = 'tested'
            
        except Exception as e:
            print(f"❌ Upload pipeline test failed: {e}")
            self.test_results['tests_failed'].append(f"Upload pipeline test failed: {str(e)}")
        
        finally:
            # Cleanup
            try:
                os.unlink(test_file_path)
            except:
                pass

    async def test_vector_processing_integration(self):
        """Test 5: Test vector processing integration with main server"""
        print("\n🔢 TEST 5: Vector Processing Integration")
        print("-" * 40)
        
        try:
            # Test creating vectors via main server upload endpoint
            async with aiohttp.ClientSession() as session:
                # Test with small text document
                test_text = "Test insurance policy document for vector processing"
                
                print(f"📝 Testing vector processing with: '{test_text[:50]}...'")
                print("⚠️ Note: This test requires main server to be running")
                
                # Create a simple text file for upload
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(test_text)
                    test_file = f.name
                
                try:
                    # Test the main server upload endpoint
                    with open(test_file, 'rb') as f:
                        files = {'file': ('test.txt', f, 'text/plain')}
                        
                        async with session.post(
                            'http://localhost:8000/upload-policy',
                            data=files,
                            headers={'Authorization': 'Bearer test-token'}
                        ) as response:
                            if response.status == 401:
                                print("✅ Vector processing endpoint: Requires auth (secured)")
                                self.test_results['tests_passed'].append("Vector processing endpoint exists and secured")
                            elif response.status == 200:
                                result = await response.json()
                                print(f"✅ Vector processing: Success - {result}")
                                self.test_results['tests_passed'].append("Vector processing working")
                            else:
                                print(f"⚠️ Vector processing endpoint: Status {response.status}")
                                
                except Exception as upload_error:
                    print(f"⚠️ Vector processing test failed: {upload_error}")
                    self.test_results['rca_findings'].append("RCA: Vector processing requires running main server")
                
                finally:
                    os.unlink(test_file)
                    
            self.test_results['vector_processing_status']['integration_tested'] = True
            
        except Exception as e:
            print(f"❌ Vector processing integration test failed: {e}")
            self.test_results['tests_failed'].append(f"Vector processing test failed: {str(e)}")

    async def test_semantic_search(self):
        """Test 6: Test semantic search functionality"""
        print("\n🔍 TEST 6: Semantic Search Functionality")
        print("-" * 40)
        
        try:
            # Test search endpoint
            async with aiohttp.ClientSession() as session:
                search_query = "insurance coverage benefits"
                
                async with session.post(
                    'http://localhost:8000/search-documents',
                    data={'query': search_query, 'limit': 5},
                    headers={'Authorization': 'Bearer test-token'}
                ) as response:
                    if response.status == 401:
                        print("✅ Search endpoint: Requires auth (secured)")
                        self.test_results['tests_passed'].append("Search endpoint exists and secured")
                    elif response.status == 200:
                        results = await response.json()
                        print(f"✅ Search functionality: {results.get('total_results', 0)} results")
                        self.test_results['tests_passed'].append("Search functionality working")
                    else:
                        print(f"⚠️ Search endpoint: Status {response.status}")
                        
            self.test_results['search_functionality_status']['endpoint_tested'] = True
            
        except Exception as e:
            print(f"❌ Search functionality test failed: {e}")
            self.test_results['tests_failed'].append(f"Search functionality test failed: {str(e)}")

    async def test_shared_module_dependencies(self):
        """Test 7: Verify no dependencies on unused shared modules"""
        print("\n📦 TEST 7: Shared Module Dependencies Check")
        print("-" * 40)
        
        try:
            # Check if shared modules exist
            shared_llamaparse = Path('db/supabase/functions/_shared/llamaparse-client.ts')
            shared_vector = Path('db/supabase/functions/_shared/vector-processor.ts')
            
            print(f"📁 llamaparse-client.ts: {'✅ Exists' if shared_llamaparse.exists() else '❌ Not found'}")
            print(f"📁 vector-processor.ts: {'✅ Exists' if shared_vector.exists() else '❌ Not found'}")
            
            # Check if these are referenced in deployed functions
            function_files = [
                'db/supabase/functions/upload-handler/index.ts',
                'db/supabase/functions/processing-webhook/index.ts',
                'db/supabase/functions/progress-tracker/index.ts'
            ]
            
            has_shared_imports = False
            for func_file in function_files:
                if Path(func_file).exists():
                    with open(func_file, 'r') as f:
                        content = f.read()
                        if '../_shared/' in content or 'from "../_shared' in content:
                            print(f"⚠️ {func_file} imports shared modules")
                            has_shared_imports = True
                        else:
                            print(f"✅ {func_file} uses inlined approach")
            
            if not has_shared_imports:
                print("✅ No shared module dependencies in deployed functions")
                self.test_results['tests_passed'].append("No shared module dependencies")
                
                if shared_llamaparse.exists() or shared_vector.exists():
                    print("💡 Recommendation: Remove unused shared modules")
                    self.test_results['rca_findings'].append("RCA: Unused shared modules can be safely removed")
            else:
                print("❌ Functions depend on shared modules (Dashboard deployment issue)")
                self.test_results['tests_failed'].append("Shared module dependencies found")
                self.test_results['rca_findings'].append("RCA: Dashboard deployment doesn't support shared modules - need CLI or inline")
                
        except Exception as e:
            print(f"❌ Shared module dependency check failed: {e}")
            self.test_results['tests_failed'].append(f"Shared module check failed: {str(e)}")

    async def generate_test_report(self):
        """Generate comprehensive test report and RCA"""
        print("\n📊 GENERATING COMPREHENSIVE TEST REPORT")
        print("="*60)
        
        # Calculate test statistics
        total_tests = len(self.test_results['tests_passed']) + len(self.test_results['tests_failed']) + len(self.test_results['tests_skipped'])
        pass_rate = (len(self.test_results['tests_passed']) / total_tests * 100) if total_tests > 0 else 0
        
        # Summary
        print(f"\n📈 TEST SUMMARY")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {len(self.test_results['tests_passed'])} ✅")
        print(f"   Failed: {len(self.test_results['tests_failed'])} ❌")
        print(f"   Skipped: {len(self.test_results['tests_skipped'])} ⏭️")
        print(f"   Pass Rate: {pass_rate:.1f}%")
        
        # Phase 5 Status Assessment
        print(f"\n🎯 PHASE 5 CLAIM VERIFICATION")
        edge_functions_deployed = sum(1 for status in self.test_results['edge_functions_status'].values() if status.get('deployed', False))
        database_ready = 'user_document_vectors' in str(self.test_results['tests_passed'])
        
        if edge_functions_deployed >= 2 and database_ready:
            phase5_status = "PARTIALLY VERIFIED ⚠️"
            phase5_color = "YELLOW"
        elif edge_functions_deployed == 0:
            phase5_status = "NOT VERIFIED ❌"
            phase5_color = "RED"
        else:
            phase5_status = "INFRASTRUCTURE READY ✅"
            phase5_color = "GREEN"
        
        print(f"   Phase 5 Status: {phase5_status}")
        print(f"   Edge Functions: {edge_functions_deployed}/3 deployed")
        print(f"   Vector Database: {'✅ Ready' if database_ready else '❌ Issues'}")
        
        # Detailed Results
        print(f"\n✅ PASSED TESTS ({len(self.test_results['tests_passed'])})")
        for test in self.test_results['tests_passed']:
            print(f"   • {test}")
            
        if self.test_results['tests_failed']:
            print(f"\n❌ FAILED TESTS ({len(self.test_results['tests_failed'])})")
            for test in self.test_results['tests_failed']:
                print(f"   • {test}")
        
        if self.test_results['tests_skipped']:
            print(f"\n⏭️ SKIPPED TESTS ({len(self.test_results['tests_skipped'])})")
            for test in self.test_results['tests_skipped']:
                print(f"   • {test}")
        
        # Root Cause Analysis
        if self.test_results['rca_findings']:
            print(f"\n🔍 ROOT CAUSE ANALYSIS")
            for i, finding in enumerate(self.test_results['rca_findings'], 1):
                print(f"   {i}. {finding}")
        
        # Action Items
        print(f"\n📋 RECOMMENDED ACTIONS")
        
        if edge_functions_deployed == 0:
            print("   🚨 CRITICAL: Deploy Edge Functions via Supabase Dashboard")
            print("      → Go to: https://supabase.com/dashboard/project/jhrespvvhbnloxrieycf")
            print("      → Copy code from db/supabase/functions/*/index.ts files")
        
        if edge_functions_deployed < 3:
            print(f"   ⚠️ MEDIUM: Deploy remaining {3 - edge_functions_deployed} Edge Functions")
        
        if 'unused shared modules' in str(self.test_results['rca_findings']).lower():
            print("   💡 OPTIMIZATION: Remove unused shared modules")
            print("      → rm db/supabase/functions/_shared/llamaparse-client.ts")
            print("      → rm db/supabase/functions/_shared/vector-processor.ts")
        
        # Final Assessment
        print(f"\n🏁 FINAL ASSESSMENT")
        if pass_rate >= 80:
            print("   ✅ System is largely functional and ready for production")
        elif pass_rate >= 60:
            print("   ⚠️ System has issues but core functionality works") 
        else:
            print("   ❌ System requires significant fixes before production")
        
        print(f"\n💾 Full test results saved to test_results object")
        
        # Save detailed results
        self.test_results['test_end'] = datetime.utcnow().isoformat()
        self.test_results['total_tests'] = total_tests
        self.test_results['pass_rate'] = pass_rate
        self.test_results['phase5_status'] = phase5_status
        
        return self.test_results

async def main():
    """Run the Phase 5 verification test"""
    test = Phase5VerificationTest()
    results = await test.run_complete_test()
    
    # Return results for analysis
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
    print(f"\n🎯 Test completed. Results available in 'results' object.") 