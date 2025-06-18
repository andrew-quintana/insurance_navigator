#!/usr/bin/env python3
"""
Comprehensive Deployment and Testing Script for Supabase Edge Functions
Includes RCA logging and security compliance testing
"""

import asyncio
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
        logging.FileHandler(f'deployment_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class EdgeFunctionTester:
    def __init__(self):
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

    def run_command(self, command: str, cwd: str = None) -> Dict[str, Any]:
        """Execute command with comprehensive logging"""
        logger.info(f"🔧 Executing: {command}")
        
        try:
            result = subprocess.run(
                command.split(),
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
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
        
        # Check environment variables
        required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_ROLE_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            self.log_step("Environment Variables", "ERROR", {"missing": missing_vars})
            return False
        
        self.log_step("Prerequisites Check", "SUCCESS", {
            "supabase_version": supabase_check['stdout'].strip(),
            "deno_version": deno_check['stdout'].split('\n')[0].strip()
        })
        
        return True

    def deploy_functions(self) -> bool:
        """Deploy Edge Functions to Supabase"""
        logger.info("🚀 Deploying Edge Functions...")
        
        # Check if functions directory exists
        functions_path = Path("supabase/functions")
        if not functions_path.exists():
            self.log_step("Functions Directory Check", "ERROR", {"path": str(functions_path)})
            return False
        
        # List available functions
        available_functions = [f.name for f in functions_path.iterdir() if f.is_dir() and f.name != "tests"]
        self.log_step("Available Functions", "SUCCESS", {"functions": available_functions})
        
        # Deploy each function
        deployment_success = True
        for function_name in available_functions:
            logger.info(f"📦 Deploying function: {function_name}")
            
            deploy_result = self.run_command(f"supabase functions deploy {function_name}")
            
            if deploy_result['success']:
                self.log_step(f"Deploy {function_name}", "SUCCESS", {
                    "function": function_name,
                    "output": deploy_result['stdout'][:200]
                })
                self.deployment_results.append({
                    'function': function_name,
                    'status': 'deployed',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                self.log_step(f"Deploy {function_name}", "ERROR", {
                    "function": function_name,
                    "error": deploy_result['stderr']
                })
                deployment_success = False
        
        return deployment_success

    def run_local_tests(self) -> bool:
        """Run comprehensive local tests"""
        logger.info("🧪 Running local tests...")
        
        # Start Supabase locally
        logger.info("🔧 Starting Supabase locally...")
        start_result = self.run_command("supabase start")
        
        if not start_result['success']:
            self.log_step("Supabase Start", "ERROR", {"error": start_result['stderr']})
            return False
        
        self.log_step("Supabase Start", "SUCCESS", {"output": "Local Supabase started"})
        
        # Wait for services to be ready
        time.sleep(10)
        
        # Run function tests
        test_files = list(Path("supabase/functions/tests").glob("*-test.ts"))
        
        if not test_files:
            self.log_step("Test Files", "WARNING", {"message": "No test files found"})
            return True
        
        test_success = True
        for test_file in test_files:
            logger.info(f"🧪 Running test: {test_file.name}")
            
            test_result = self.run_command(
                f"deno test --allow-all {test_file}",
                cwd="supabase/functions"
            )
            
            if test_result['success']:
                self.log_step(f"Test {test_file.name}", "SUCCESS", {
                    "test_file": test_file.name,
                    "output": test_result['stdout']
                })
                self.test_results.append({
                    'test_file': test_file.name,
                    'status': 'passed',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                self.log_step(f"Test {test_file.name}", "ERROR", {
                    "test_file": test_file.name,
                    "error": test_result['stderr']
                })
                test_success = False
        
        return test_success

    def security_compliance_check(self) -> bool:
        """Perform security compliance checks"""
        logger.info("🔒 Running security compliance checks...")
        
        security_issues = []
        
        # Check for hardcoded secrets
        for func_dir in Path("supabase/functions").iterdir():
            if func_dir.is_dir() and func_dir.name != "tests":
                for file_path in func_dir.glob("**/*.ts"):
                    content = file_path.read_text()
                    
                    # Simple pattern matching for potential secrets
                    if 'api_key' in content.lower() and 'env' not in content.lower():
                        security_issues.append(f"Potential hardcoded API key in {file_path}")
                    
                    if 'password' in content.lower() and 'env' not in content.lower():
                        security_issues.append(f"Potential hardcoded password in {file_path}")
        
        if security_issues:
            self.log_step("Security Check", "WARNING", {"issues": security_issues})
        else:
            self.log_step("Security Check", "SUCCESS", {"message": "No obvious security issues found"})
        
        return len(security_issues) == 0

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        report = {
            'summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration_seconds': total_duration,
                'deployment_success': len(self.deployment_results) > 0,
                'test_success': len(self.test_results) > 0,
                'total_errors': len(self.errors)
            },
            'deployments': self.deployment_results,
            'test_results': self.test_results,
            'errors': self.errors,
            'environment': {
                'supabase_url': os.getenv('SUPABASE_URL', 'Not set'),
                'has_openai_key': bool(os.getenv('OPENAI_API_KEY')),
                'python_version': sys.version
            }
        }
        
        # Write report to file
        report_file = f"edge_function_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Test report saved to: {report_file}")
        
        return report

async def main():
    """Main deployment and testing orchestrator"""
    logger.info("🚀 Starting Edge Function Deployment and Testing")
    
    tester = EdgeFunctionTester()
    
    try:
        # 1. Prerequisites check
        if not tester.check_prerequisites():
            logger.error("❌ Prerequisites check failed")
            return False
        
        # 2. Security compliance check
        tester.security_compliance_check()
        
        # 3. Local testing first
        local_test_success = tester.run_local_tests()
        
        # 4. Deploy to Supabase if local tests pass
        if local_test_success:
            deployment_success = tester.deploy_functions()
        else:
            logger.warning("⚠️ Skipping deployment due to local test failures")
            deployment_success = False
        
        # 5. Generate report
        report = tester.generate_report()
        
        # 6. Final summary
        if deployment_success and local_test_success:
            logger.info("🎉 All tests passed and deployment successful!")
            return True
        else:
            logger.error("❌ Some tests failed or deployment unsuccessful")
            logger.info(f"📊 Summary: {len(tester.deployment_results)} deployments, {len(tester.test_results)} tests, {len(tester.errors)} errors")
            return False
            
    except Exception as e:
        logger.error(f"💥 Unexpected error during testing: {e}")
        tester.log_step("Main Process", "ERROR", {"error": str(e)})
        return False
    
    finally:
        # Always generate report
        tester.generate_report()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 