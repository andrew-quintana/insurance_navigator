#!/usr/bin/env python3
"""
Final Edge Functions Deployment Script
Uses the official Supabase CLI --use-api flag for Docker-free deployment
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
        logging.FileHandler(f'final_deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class FinalEdgeFunctionDeployer:
    def __init__(self):
        self.deployment_results = []
        self.test_results = []
        self.errors = []
        self.start_time = datetime.now()
        self.project_ref = "jhrespvvhbnloxrieycf"
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
        
        # Check Supabase CLI beta
        cli_check = self.run_command("npx supabase@beta --version")
        if not cli_check['success']:
            self.log_step("Supabase CLI Beta Check", "ERROR", {"error": "Supabase CLI beta not available"})
            return False
        
        # Check Deno
        deno_check = self.run_command("deno --version")
        if not deno_check['success']:
            self.log_step("Deno Check", "ERROR", {"error": "Deno not found"})
            return False
        
        # Check access token
        access_token = os.getenv('SUPABASE_ACCESS_TOKEN')
        if not access_token:
            self.log_step("Access Token Check", "ERROR", {
                "error": "SUPABASE_ACCESS_TOKEN environment variable is required",
                "instructions": [
                    "1. Go to: https://app.supabase.com/account/tokens",
                    "2. Click 'Generate new token'", 
                    "3. Copy the token",
                    "4. Run: export SUPABASE_ACCESS_TOKEN='your_token_here'"
                ]
            })
            return False
        
        if not access_token.startswith('sbp_'):
            self.log_step("Access Token Format", "ERROR", {
                "error": "Access token must start with 'sbp_'",
                "current_format": access_token[:10] + "..." if len(access_token) > 10 else access_token
            })
            return False
        
        # Check project link
        project_check = self.run_command("npx supabase@beta projects list")
        if not project_check['success']:
            self.log_step("Project Link Check", "ERROR", {"error": "Not authenticated with Supabase"})
            return False
        
        # Check functions directory
        if not self.functions_path.exists():
            self.log_step("Functions Directory Check", "ERROR", {"path": str(self.functions_path)})
            return False
        
        self.log_step("Prerequisites Check", "SUCCESS", {
            "cli_version": cli_check['stdout'].strip(),
            "deno_version": deno_check['stdout'].split('\n')[0].strip(),
            "functions_path": str(self.functions_path),
            "access_token_format": "Valid (sbp_...)"
        })
        
        return True

    def list_available_functions(self) -> List[str]:
        """List all available Edge Functions"""
        functions = []
        
        for item in self.functions_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('_'):
                if (item / "index.ts").exists():
                    functions.append(item.name)
        
        self.log_step("Available Functions", "SUCCESS", {"functions": functions})
        return functions

    def deploy_function(self, function_name: str) -> bool:
        """Deploy a single Edge Function using CLI --use-api"""
        logger.info(f"📦 Deploying function: {function_name}")
        
        # Deploy the function using the new --use-api flag
        deploy_result = self.run_command(
            f"npx supabase@beta functions deploy {function_name} --use-api --project-ref {self.project_ref}",
            cwd="db"
        )
        
        if deploy_result['success']:
            self.log_step(f"Deploy {function_name}", "SUCCESS", {
                "function": function_name,
                "output": deploy_result['stdout'][:300] + '...' if len(deploy_result['stdout']) > 300 else deploy_result['stdout']
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

    def test_function(self, function_name: str) -> bool:
        """Test a deployed function"""
        logger.info(f"🧪 Testing function: {function_name}")
        
        try:
            import requests
            
            # Test with a simple payload
            test_payload = {"test": True, "timestamp": datetime.now().isoformat()}
            
            url = f"https://{self.project_ref}.supabase.co/functions/v1/{function_name}"
            headers = {
                "Content-Type": "application/json",
                # Note: Some functions may require Authorization header with anon key
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

    def deploy_all_functions(self) -> bool:
        """Deploy all Edge Functions"""
        logger.info("🚀 Deploying all Edge Functions using CLI --use-api...")
        
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
                'cli_method': 'supabase@beta --use-api',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Write report to file
        report_file = f"final_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Deployment report saved to: {report_file}")
        
        return report

def main():
    """Main deployment orchestrator"""
    logger.info("🚀 Starting Final Edge Functions Deployment (Docker-Free)")
    
    deployer = FinalEdgeFunctionDeployer()
    
    try:
        # 1. Prerequisites check
        if not deployer.check_prerequisites():
            logger.error("❌ Prerequisites check failed")
            return False
        
        # 2. Deploy all functions
        deployment_success = deployer.deploy_all_functions()
        
        # 3. Run tests if deployment succeeded
        if deployment_success:
            test_success = deployer.run_function_tests()
        else:
            logger.warning("⚠️ Skipping tests due to deployment failures")
            test_success = False
        
        # 4. Generate report
        report = deployer.generate_report()
        
        # 5. Final summary
        if deployment_success:
            logger.info("🎉 Edge Functions deployment completed successfully!")
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