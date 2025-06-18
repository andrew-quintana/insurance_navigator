#!/usr/bin/env python3
"""
Supabase Edge Functions Deployment & Testing Script
Deploys to your actual Supabase project and tests with comprehensive RCA logging
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Setup comprehensive logging for RCA
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(f'supabase_deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SupabaseEdgeFunctionDeployer:
    def __init__(self):
        self.deployment_results = []
        self.test_results = []
        self.errors = []
        self.start_time = datetime.now()
        self.functions_path = Path("db/supabase/functions")
        
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

    def run_command(self, command: str, cwd: str = None) -> Dict[str, Any]:
        """Execute command with comprehensive logging"""
        logger.info(f"🔧 Executing: {command}")
        
        # Set PATH to include Deno
        env = os.environ.copy()
        env['PATH'] = f"{os.path.expanduser('~/.deno/bin')}:{env.get('PATH', '')}"
        
        try:
            result = subprocess.run(
                command.split(),
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300,
                env=env
            )
            
            log_details = {
                'command': command,
                'return_code': result.returncode,
                'stdout_lines': len(result.stdout.splitlines()) if result.stdout else 0,
                'stderr_lines': len(result.stderr.splitlines()) if result.stderr else 0
            }
            
            if result.returncode == 0:
                self.log_step(f"Command: {command}", "SUCCESS", log_details)
            else:
                log_details['stderr'] = result.stderr[:500] + '...' if len(result.stderr) > 500 else result.stderr
                self.log_step(f"Command: {command}", "ERROR", log_details)
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            error_details = {'command': command, 'error': 'Command timeout (300s)'}
            self.log_step(f"Command: {command}", "ERROR", error_details)
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            error_details = {'command': command, 'error': str(e)}
            self.log_step(f"Command: {command}", "ERROR", error_details)
            return {'success': False, 'error': str(e)}

    def check_prerequisites(self) -> bool:
        """Check all prerequisites for deployment"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check Supabase CLI
        supabase_check = self.run_command("supabase --version")
        if not supabase_check['success']:
            self.log_step("Supabase CLI Check", "ERROR", {"error": "Supabase CLI not found"})
            return False
        
        # Check Deno
        deno_check = self.run_command("deno --version")
        if not deno_check['success']:
            self.log_step("Deno Check", "ERROR", {"error": "Deno not found"})
            return False
        
        # Check project link
        project_check = self.run_command("supabase projects list")
        if not project_check['success']:
            self.log_step("Project Link Check", "ERROR", {"error": "Not authenticated with Supabase"})
            return False
        
        # Check functions directory
        if not self.functions_path.exists():
            self.log_step("Functions Directory Check", "ERROR", {"path": str(self.functions_path)})
            return False
        
        self.log_step("Prerequisites Check", "SUCCESS", {
            "supabase_version": supabase_check['stdout'].strip().split('\n')[0],
            "deno_version": deno_check['stdout'].split('\n')[0].strip(),
            "functions_path": str(self.functions_path)
        })
        
        return True

    def list_available_functions(self) -> List[str]:
        """List all available Edge Functions"""
        functions = []
        
        for item in self.functions_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
                # Check if it has an index.ts file
                if (item / "index.ts").exists():
                    functions.append(item.name)
        
        self.log_step("Available Functions", "SUCCESS", {"functions": functions})
        return functions

    def deploy_function(self, function_name: str) -> bool:
        """Deploy a single Edge Function"""
        logger.info(f"📦 Deploying function: {function_name}")
        
        # Deploy the function
        deploy_result = self.run_command(f"supabase functions deploy {function_name}")
        
        if deploy_result['success']:
            self.log_step(f"Deploy {function_name}", "SUCCESS", {
                "function": function_name,
                "output": deploy_result['stdout'][:200] + '...' if len(deploy_result['stdout']) > 200 else deploy_result['stdout']
            })
            self.deployment_results.append({
                'function': function_name,
                'status': 'deployed',
                'timestamp': datetime.now().isoformat(),
                'output': deploy_result['stdout']
            })
            return True
        else:
            self.log_step(f"Deploy {function_name}", "ERROR", {
                "function": function_name,
                "error": deploy_result['stderr']
            })
            return False

    def test_function_invocation(self, function_name: str, test_payload: Dict[str, Any]) -> bool:
        """Test a deployed function with a sample payload"""
        logger.info(f"🧪 Testing function: {function_name}")
        
        # Create a test payload file
        test_file = f"test_payload_{function_name}.json"
        with open(test_file, 'w') as f:
            json.dump(test_payload, f)
        
        try:
            # Use curl to test the function (more reliable than supabase functions invoke)
            test_result = self.run_command(
                f"supabase functions invoke {function_name} --data @{test_file}"
            )
            
            if test_result['success']:
                self.log_step(f"Test {function_name}", "SUCCESS", {
                    "function": function_name,
                    "response": test_result['stdout'][:200] + '...' if len(test_result['stdout']) > 200 else test_result['stdout']
                })
                self.test_results.append({
                    'function': function_name,
                    'status': 'passed',
                    'timestamp': datetime.now().isoformat(),
                    'response': test_result['stdout']
                })
                return True
            else:
                self.log_step(f"Test {function_name}", "WARNING", {
                    "function": function_name,
                    "error": test_result['stderr'],
                    "note": "Function deployed but test failed - may be due to auth or payload issues"
                })
                return False
                
        finally:
            # Cleanup test file
            if os.path.exists(test_file):
                os.remove(test_file)

    def deploy_all_functions(self) -> bool:
        """Deploy all Edge Functions"""
        logger.info("🚀 Deploying all Edge Functions...")
        
        functions = self.list_available_functions()
        
        if not functions:
            self.log_step("Functions List", "WARNING", {"message": "No functions found to deploy"})
            return False
        
        deployment_success = True
        
        for function_name in functions:
            success = self.deploy_function(function_name)
            if not success:
                deployment_success = False
            
            # Small delay between deployments
            time.sleep(2)
        
        return deployment_success

    def run_comprehensive_tests(self) -> bool:
        """Run comprehensive tests on deployed functions"""
        logger.info("🧪 Running comprehensive function tests...")
        
        # Test payloads for different functions
        test_payloads = {
            'vector-processor': {
                'documentId': 'test-doc-123',
                'extractedText': 'This is test content for vector processing.',
                'documentType': 'user'
            },
            'bulk-regulatory-processor': {
                'documents': [
                    {
                        'url': 'https://www.cms.gov/test-article',
                        'title': 'Test Article',
                        'jurisdiction': 'federal',
                        'document_type': 'guidance'
                    }
                ],
                'batch_size': 1
            },
            'doc-processor': {
                'documentId': 'test-doc-456'
            },
            'doc-parser': {
                'documentId': 'test-doc-789'
            }
        }
        
        test_success = True
        
        for function_name in self.deployment_results:
            if isinstance(function_name, dict):
                func_name = function_name['function']
            else:
                func_name = function_name
                
            if func_name in test_payloads:
                success = self.test_function_invocation(func_name, test_payloads[func_name])
                if not success:
                    test_success = False
            else:
                logger.info(f"⚠️ No test payload defined for {func_name}")
        
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
                'functions_path': str(self.functions_path),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Write report to file
        report_file = f"supabase_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Deployment report saved to: {report_file}")
        
        return report

def main():
    """Main deployment orchestrator"""
    logger.info("🚀 Starting Supabase Edge Functions Deployment")
    
    deployer = SupabaseEdgeFunctionDeployer()
    
    try:
        # 1. Prerequisites check
        if not deployer.check_prerequisites():
            logger.error("❌ Prerequisites check failed")
            return False
        
        # 2. Deploy all functions
        deployment_success = deployer.deploy_all_functions()
        
        # 3. Run tests if deployment succeeded
        if deployment_success:
            test_success = deployer.run_comprehensive_tests()
        else:
            logger.warning("⚠️ Skipping tests due to deployment failures")
            test_success = False
        
        # 4. Generate report
        report = deployer.generate_report()
        
        # 5. Final summary
        if deployment_success:
            logger.info("🎉 Edge Functions deployment completed!")
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