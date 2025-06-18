#!/usr/bin/env python3
"""
Deploy Supabase Edge Functions using the new API endpoint (without Docker)
Uses the Supabase Management API to deploy functions directly
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
from typing import Dict, List, Any

# Setup comprehensive logging for RCA
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(f'api_deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SupabaseAPIDeployer:
    def __init__(self, project_ref: str, access_token: str):
        self.project_ref = project_ref
        self.access_token = access_token
        self.base_url = "https://api.supabase.com/v1"
        self.functions_path = Path("db/supabase/functions")
        self.deployment_results = []
        self.test_results = []
        self.errors = []
        self.start_time = datetime.now()
        
    def log_step(self, step: str, status: str, details: Dict[str, Any] = None):
        """Enhanced logging for RCA"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'details': details or {},
            'elapsed_time': (datetime.now() - self.start_time).total_seconds()
        }
        
        if status == 'SUCCESS':
            logger.info(f"✅ {step}: {details}")
        elif status == 'WARNING':
            logger.warning(f"⚠️ {step}: {details}")
        elif status == 'ERROR':
            logger.error(f"❌ {step}: {details}")
            self.errors.append(log_entry)
        
        return log_entry

    def create_function_bundle(self, function_name: str) -> bytes:
        """Create a zip bundle for the function"""
        logger.info(f"📦 Creating bundle for function: {function_name}")
        
        function_path = self.functions_path / function_name
        
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
                    logger.debug(f"Added to bundle: {rel_path}")
        
        zip_buffer.seek(0)
        bundle_data = zip_buffer.getvalue()
        
        self.log_step(f"Bundle {function_name}", "SUCCESS", {
            "function": function_name,
            "bundle_size": len(bundle_data),
            "files_included": len([f for f in function_path.rglob('*') if f.is_file()])
        })
        
        return bundle_data

    def deploy_function(self, function_name: str, verify_jwt: bool = False) -> bool:
        """Deploy a single function using the Supabase API"""
        logger.info(f"🚀 Deploying function: {function_name}")
        
        try:
            # Create function bundle
            bundle_data = self.create_function_bundle(function_name)
            
            # Encode bundle as base64
            bundle_b64 = base64.b64encode(bundle_data).decode('utf-8')
            
            # Prepare deployment payload
            deployment_payload = {
                "slug": function_name,
                "body": bundle_b64,
                "verify_jwt": verify_jwt
            }
            
            # Deploy using Supabase API
            url = f"{self.base_url}/projects/{self.project_ref}/functions"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"📡 Sending deployment request to: {url}")
            
            response = requests.post(url, json=deployment_payload, headers=headers)
            
            if response.status_code in [200, 201]:
                self.log_step(f"Deploy {function_name}", "SUCCESS", {
                    "function": function_name,
                    "status_code": response.status_code,
                    "response": response.json() if response.content else "No content"
                })
                
                self.deployment_results.append({
                    'function': function_name,
                    'status': 'deployed',
                    'timestamp': datetime.now().isoformat(),
                    'response': response.json() if response.content else {}
                })
                return True
            else:
                error_details = {
                    "function": function_name,
                    "status_code": response.status_code,
                    "error": response.text
                }
                self.log_step(f"Deploy {function_name}", "ERROR", error_details)
                return False
                
        except Exception as e:
            error_details = {
                "function": function_name,
                "error": str(e),
                "type": type(e).__name__
            }
            self.log_step(f"Deploy {function_name}", "ERROR", error_details)
            return False

    def test_function(self, function_name: str) -> bool:
        """Test a deployed function"""
        logger.info(f"🧪 Testing function: {function_name}")
        
        try:
            # Test with a simple payload
            test_payload = {"test": True, "timestamp": datetime.now().isoformat()}
            
            url = f"https://{self.project_ref}.supabase.co/functions/v1/{function_name}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }
            
            response = requests.post(url, json=test_payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                self.log_step(f"Test {function_name}", "SUCCESS", {
                    "function": function_name,
                    "status_code": response.status_code,
                    "response": response.text[:200] + '...' if len(response.text) > 200 else response.text
                })
                
                self.test_results.append({
                    'function': function_name,
                    'status': 'passed',
                    'timestamp': datetime.now().isoformat(),
                    'response': response.text
                })
                return True
            else:
                self.log_step(f"Test {function_name}", "WARNING", {
                    "function": function_name,
                    "status_code": response.status_code,
                    "error": response.text,
                    "note": "Function deployed but test failed - may be due to auth or payload requirements"
                })
                return False
                
        except Exception as e:
            self.log_step(f"Test {function_name}", "WARNING", {
                "function": function_name,
                "error": str(e),
                "note": "Test failed but function may still be working"
            })
            return False

    def list_available_functions(self) -> List[str]:
        """List all available Edge Functions"""
        functions = []
        
        if not self.functions_path.exists():
            self.log_step("Functions Directory Check", "ERROR", {"path": str(self.functions_path)})
            return functions
        
        for item in self.functions_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
                if (item / "index.ts").exists():
                    functions.append(item.name)
        
        self.log_step("Available Functions", "SUCCESS", {"functions": functions})
        return functions

    def deploy_all_functions(self) -> bool:
        """Deploy all available functions"""
        logger.info("🚀 Deploying all Edge Functions via API...")
        
        functions = self.list_available_functions()
        
        if not functions:
            self.log_step("Functions List", "WARNING", {"message": "No functions found to deploy"})
            return False
        
        deployment_success = True
        
        # Special handling for functions that don't need JWT verification
        no_jwt_functions = ['processing-webhook', 'doc-parser']
        
        for function_name in functions:
            verify_jwt = function_name not in no_jwt_functions
            
            logger.info(f"📦 Deploying {function_name} (JWT verification: {verify_jwt})")
            success = self.deploy_function(function_name, verify_jwt=verify_jwt)
            
            if not success:
                deployment_success = False
            
            # Small delay between deployments
            import time
            time.sleep(2)
        
        return deployment_success

    def run_function_tests(self) -> bool:
        """Test all deployed functions"""
        logger.info("🧪 Running function tests...")
        
        test_success = True
        deployed_functions = [result['function'] for result in self.deployment_results if result['status'] == 'deployed']
        
        for function_name in deployed_functions:
            success = self.test_function(function_name)
            if not success:
                test_success = False
        
        return test_success

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        report = {
            'summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration_seconds': total_duration,
                'functions_deployed': len(self.deployment_results),
                'tests_passed': len([t for t in self.test_results if t['status'] == 'passed']),
                'total_errors': len(self.errors),
                'deployment_success': len(self.deployment_results) > 0 and len(self.errors) == 0
            },
            'deployments': self.deployment_results,
            'test_results': self.test_results,
            'errors': self.errors,
            'environment': {
                'project_ref': self.project_ref,
                'functions_path': str(self.functions_path),
                'api_endpoint': self.base_url,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Write report to file
        report_file = f"api_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Deployment report saved to: {report_file}")
        
        return report

def main():
    """Main deployment orchestrator"""
    
    # Get project configuration
    project_ref = "jhrespvvhbnloxrieycf"  # Your project ref
    access_token = os.getenv('SUPABASE_ACCESS_TOKEN')
    
    if not access_token:
        logger.error("❌ SUPABASE_ACCESS_TOKEN environment variable is required")
        logger.info("💡 Get your access token from: https://app.supabase.com/account/tokens")
        return False
    
    logger.info("🚀 Starting Supabase Edge Functions API Deployment")
    
    deployer = SupabaseAPIDeployer(project_ref, access_token)
    
    try:
        # 1. Deploy all functions
        deployment_success = deployer.deploy_all_functions()
        
        # 2. Run tests if deployment succeeded
        if deployment_success:
            test_success = deployer.run_function_tests()
        else:
            logger.warning("⚠️ Skipping tests due to deployment failures")
            test_success = False
        
        # 3. Generate report
        report = deployer.generate_report()
        
        # 4. Final summary
        if deployment_success:
            logger.info("🎉 Edge Functions deployment completed via API!")
            logger.info(f"📊 Summary: {len(deployer.deployment_results)} deployed, {len(deployer.test_results)} tested, {len(deployer.errors)} errors")
            
            if test_success:
                logger.info("✅ All tests passed!")
            else:
                logger.warning("⚠️ Some tests failed - functions are deployed but may need debugging")
            
            return True
        else:
            logger.error("❌ Deployment failed")
            return False
            
    except Exception as e:
        logger.error(f"💥 Unexpected error during deployment: {e}")
        deployer.log_step("Main Process", "ERROR", {"error": str(e)})
        return False
    
    finally:
        # Always generate report
        deployer.generate_report()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 