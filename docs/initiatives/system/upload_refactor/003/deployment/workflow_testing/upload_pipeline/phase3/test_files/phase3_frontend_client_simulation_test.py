#!/usr/bin/env python3
"""
Phase 3 Frontend Client Simulation Test
Simulates a complete frontend client workflow testing both API service and worker service
"""

import asyncio
import httpx
import json
import os
import time
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FrontendClientSimulator:
    """Simulates a frontend client interacting with the upload pipeline"""
    
    def __init__(self):
        self.api_url = "https://insurance-navigator-api.onrender.com"
        self.database_url = os.getenv('POOLER_URL', '${DATABASE_URL}/register", 
                    json=registration_data, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.user_id = data.get("user", {}).get("id")
                    logger.info(f"✅ User registered successfully: {self.user_id}")
                    return {
                        "step": "register_user",
                        "status": "passed",
                        "user_id": self.user_id,
                        "response": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"❌ Registration failed: {response.status_code}")
                    return {
                        "step": "register_user",
                        "status": "failed",
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return {
                "step": "register_user",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def step2_login_user(self) -> Dict[str, Any]:
        """Step 2: Login user (simulating frontend login)"""
        logger.info("🔐 Step 2: Logging in user...")
        
        try:
            async with httpx.AsyncClient() as client:
                login_data = {
                    "email": f"frontend-test-{int(time.time())}@example.com",
                    "password": "testpassword123"
                }
                
                response = await client.post(
                    f"{self.api_url}/login", 
                    json=login_data, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    self.user_id = data.get("user", {}).get("id")
                    logger.info(f"✅ User logged in successfully: {self.user_id}")
                    return {
                        "step": "login_user",
                        "status": "passed",
                        "user_id": self.user_id,
                        "access_token": self.access_token[:20] + "...",  # Truncated for security
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"❌ Login failed: {response.status_code}")
                    return {
                        "step": "login_user",
                        "status": "failed",
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return {
                "step": "login_user",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def step3_initiate_upload(self) -> Dict[str, Any]:
        """Step 3: Initiate document upload (simulating frontend upload initiation)"""
        logger.info("📤 Step 3: Initiating document upload...")
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                # Create a realistic test document
                test_content = f"""# Insurance Policy Document

## Policy Information
Policy Number: TEST-{uuid.uuid4().hex[:8]}
Policy Type: Comprehensive Health Insurance
Effective Date: {datetime.utcnow().strftime('%Y-%m-%d')}
Expiration Date: {(datetime.utcnow() + timedelta(days=365)).strftime('%Y-%m-%d')}

## Coverage Details
- Medical Coverage: $1,000,000
- Prescription Drug Coverage: $50,000
- Dental Coverage: $2,000
- Vision Coverage: $1,000

## Terms and Conditions
This policy provides comprehensive health insurance coverage for the policyholder and eligible dependents.

## Contact Information
Insurance Provider: Test Insurance Company
Phone: (555) 123-4567
Email: support@testinsurance.com

Document ID: {uuid.uuid4()}
Generated: {datetime.utcnow().isoformat()}
""".encode('utf-8')
                
                # Create test file
                test_file = ("insurance_policy.pdf", test_content, "application/pdf")
                
                upload_data = {
                    "policy_id": f"policy-{uuid.uuid4().hex[:8]}",
                    "document_type": "insurance_policy"
                }
                
                files = {"file": test_file}
                
                response = await client.post(
                    f"{self.api_url}/upload-document-backend",
                    data=upload_data,
                    files=files,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.document_id = data.get("document_id")
                    self.job_id = data.get("job_id")
                    logger.info(f"✅ Upload initiated successfully")
                    logger.info(f"   Document ID: {self.document_id}")
                    logger.info(f"   Job ID: {self.job_id}")
                    return {
                        "step": "initiate_upload",
                        "status": "passed",
                        "document_id": self.document_id,
                        "job_id": self.job_id,
                        "response": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"❌ Upload initiation failed: {response.status_code}")
                    return {
                        "step": "initiate_upload",
                        "status": "failed",
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Upload initiation error: {e}")
            return {
                "step": "initiate_upload",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def step4_monitor_processing(self) -> Dict[str, Any]:
        """Step 4: Monitor document processing (simulating frontend polling)"""
        logger.info("⏳ Step 4: Monitoring document processing...")
        
        try:
            import asyncpg
            
            # Connect to database to monitor processing
            conn = await asyncpg.connect(self.database_url, statement_cache_size=0)
            
            # Expected pipeline stages
            expected_stages = [
                "uploaded",
                "parse_queued", 
                "parsed",
                "parse_validated",
                "chunks_stored",
                "embedding_in_progress",
                "embeddings_stored",
                "complete"
            ]
            
            stage_transitions = []
            start_time = datetime.utcnow()
            
            # Monitor for up to 5 minutes
            for attempt in range(600):  # 600 * 0.5 seconds = 5 minutes
                result = await conn.fetchrow("""
                    SELECT state, status, updated_at, last_error, progress
                    FROM upload_pipeline.upload_jobs 
                    WHERE job_id = $1 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """, self.job_id)
                
                if result:
                    current_state = result['state']
                    current_status = result['status']
                    updated_at = result['updated_at']
                    
                    # Check if this is a new stage transition
                    if current_status not in [s['status'] for s in stage_transitions]:
                        stage_transitions.append({
                            'status': current_status,
                            'state': current_state,
                            'timestamp': updated_at,
                            'attempt': attempt + 1
                        })
                        logger.info(f"🔄 Stage: {current_status} (state: {current_state}) - Attempt {attempt + 1}")
                        
                        # Check if processing is complete
                        if current_status == "complete" and current_state == "done":
                            logger.info("🎉 Document processing completed successfully!")
                            break
                        elif current_state == "deadletter":
                            logger.error(f"❌ Processing failed: {result['last_error']}")
                            break
                    else:
                        logger.info(f"⏳ Current stage: {current_status} (state: {current_state}) - Attempt {attempt + 1}")
                else:
                    logger.error("❌ No job found in database")
                    break
                    
                await asyncio.sleep(0.5)  # Check every 0.5 seconds
            
            await conn.close()
            
            # Analyze results
            completed_stages = [s['status'] for s in stage_transitions]
            missing_stages = set(expected_stages) - set(completed_stages)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "step": "monitor_processing",
                "status": "passed" if "complete" in completed_stages else "failed",
                "stages_completed": completed_stages,
                "expected_stages": expected_stages,
                "missing_stages": list(missing_stages),
                "stage_transitions": stage_transitions,
                "processing_time": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Processing monitoring error: {e}")
            return {
                "step": "monitor_processing",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def step5_verify_results(self) -> Dict[str, Any]:
        """Step 5: Verify processing results (simulating frontend result verification)"""
        logger.info("✅ Step 5: Verifying processing results...")
        
        try:
            import asyncpg
            
            # Connect to database to verify results
            conn = await asyncpg.connect(self.database_url, statement_cache_size=0)
            
            # Get document information
            doc_info = await conn.fetchrow("""
                SELECT document_id, filename, processing_status, created_at, updated_at
                FROM upload_pipeline.documents 
                WHERE document_id = $1
            """, self.document_id)
            
            # Get job information
            job_info = await conn.fetchrow("""
                SELECT job_id, status, state, created_at, updated_at, progress
                FROM upload_pipeline.upload_jobs 
                WHERE job_id = $1
            """, self.job_id)
            
            # Get chunk information
            chunk_count = await conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.document_chunks 
                WHERE document_id = $1
            """, self.document_id)
            
            # Get embedding information
            embedding_count = await conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.document_chunks 
                WHERE document_id = $1 AND embedding IS NOT NULL
            """, self.document_id)
            
            await conn.close()
            
            # Verify results
            verification_results = {
                "document_exists": doc_info is not None,
                "document_processing_status": doc_info["processing_status"] if doc_info else None,
                "job_completed": job_info["status"] == "complete" if job_info else False,
                "job_state": job_info["state"] if job_info else None,
                "chunks_created": chunk_count,
                "embeddings_generated": embedding_count,
                "processing_successful": (
                    doc_info and 
                    doc_info["processing_status"] == "complete" and 
                    job_info and 
                    job_info["status"] == "complete" and 
                    chunk_count > 0 and 
                    embedding_count > 0
                )
            }
            
            logger.info(f"📊 Verification Results:")
            logger.info(f"   Document exists: {verification_results['document_exists']}")
            logger.info(f"   Document status: {verification_results['document_processing_status']}")
            logger.info(f"   Job completed: {verification_results['job_completed']}")
            logger.info(f"   Job state: {verification_results['job_state']}")
            logger.info(f"   Chunks created: {verification_results['chunks_created']}")
            logger.info(f"   Embeddings generated: {verification_results['embeddings_generated']}")
            logger.info(f"   Overall success: {verification_results['processing_successful']}")
            
            return {
                "step": "verify_results",
                "status": "passed" if verification_results["processing_successful"] else "failed",
                "verification_results": verification_results,
                "document_info": dict(doc_info) if doc_info else None,
                "job_info": dict(job_info) if job_info else None,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Result verification error: {e}")
            return {
                "step": "verify_results",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def run_complete_workflow(self) -> Dict[str, Any]:
        """Run the complete frontend client workflow"""
        logger.info("🚀 Starting Frontend Client Simulation Test")
        logger.info("=" * 60)
        
        start_time = time.time()
        workflow_results = []
        
        # Step 1: Register user
        logger.info("\n1️⃣ User Registration...")
        register_result = await self.step1_register_user()
        workflow_results.append(register_result)
        
        if register_result["status"] != "passed":
            logger.error("❌ Registration failed, stopping workflow")
            return self._create_summary(workflow_results, start_time)
        
        # Step 2: Login user
        logger.info("\n2️⃣ User Login...")
        login_result = await self.step2_login_user()
        workflow_results.append(login_result)
        
        if login_result["status"] != "passed":
            logger.error("❌ Login failed, stopping workflow")
            return self._create_summary(workflow_results, start_time)
        
        # Step 3: Initiate upload
        logger.info("\n3️⃣ Document Upload Initiation...")
        upload_result = await self.step3_initiate_upload()
        workflow_results.append(upload_result)
        
        if upload_result["status"] != "passed":
            logger.error("❌ Upload initiation failed, stopping workflow")
            return self._create_summary(workflow_results, start_time)
        
        # Step 4: Monitor processing
        logger.info("\n4️⃣ Document Processing Monitoring...")
        monitor_result = await self.step4_monitor_processing()
        workflow_results.append(monitor_result)
        
        # Step 5: Verify results
        logger.info("\n5️⃣ Processing Results Verification...")
        verify_result = await self.step5_verify_results()
        workflow_results.append(verify_result)
        
        return self._create_summary(workflow_results, start_time)
    
    def _create_summary(self, workflow_results: List[Dict[str, Any]], start_time: float) -> Dict[str, Any]:
        """Create workflow summary"""
        total_time = time.time() - start_time
        
        # Calculate step results
        total_steps = len(workflow_results)
        passed_steps = len([r for r in workflow_results if r['status'] == 'passed'])
        failed_steps = len([r for r in workflow_results if r['status'] == 'failed'])
        
        # Determine overall success
        overall_success = (
            passed_steps == total_steps and 
            any(r.get('verification_results', {}).get('processing_successful', False) for r in workflow_results)
        )
        
        summary = {
            "test_type": "Frontend Client Simulation",
            "timestamp": datetime.utcnow().isoformat(),
            "api_url": self.api_url,
            "total_duration": total_time,
            "overall_success": overall_success,
            "summary": {
                "total_steps": total_steps,
                "passed_steps": passed_steps,
                "failed_steps": failed_steps,
                "success_rate": (passed_steps / total_steps * 100) if total_steps > 0 else 0
            },
            "workflow_results": workflow_results,
            "test_metadata": {
                "user_id": self.user_id,
                "document_id": self.document_id,
                "job_id": self.job_id
            }
        }
        
        # Log summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 FRONTEND CLIENT SIMULATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"API URL: {self.api_url}")
        logger.info(f"Overall Success: {'✅ YES' if overall_success else '❌ NO'}")
        logger.info(f"Total Steps: {total_steps}")
        logger.info(f"Passed Steps: {passed_steps}")
        logger.info(f"Failed Steps: {failed_steps}")
        logger.info(f"Success Rate: {summary['summary']['success_rate']:.1f}%")
        logger.info(f"Total Duration: {total_time:.2f} seconds")
        logger.info(f"User ID: {self.user_id}")
        logger.info(f"Document ID: {self.document_id}")
        logger.info(f"Job ID: {self.job_id}")
        
        return summary

async def main():
    """Main function"""
    simulator = FrontendClientSimulator()
    
    try:
        # Run complete workflow
        results = await simulator.run_complete_workflow()
        
        # Save results to file
        timestamp = int(time.time())
        filename = f"phase3_frontend_client_simulation_{timestamp}.json"
        filepath = f"docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/upload_pipeline/phase3/results/{filename}"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📁 Results saved to: {filepath}")
        
        # Return success/failure
        return results['overall_success']
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
