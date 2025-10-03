#!/usr/bin/env python3
"""
Phase 3 Test Suite: Security & Accessibility Validation

This script runs comprehensive security and accessibility validation tests
for the cloud deployment, implementing Phase 3 of the cloud deployment testing.
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.testing.cloud_deployment.phase3_security_validator import CloudSecurityValidator
from backend.testing.cloud_deployment.phase3_accessibility_validator import CloudAccessibilityValidator

class Phase3TestSuite:
    """Phase 3 test suite for security and accessibility validation"""
    
    def __init__(self):
        self.config = self._load_config()
        self.results = {}
        
    def _load_config(self) -> dict:
        """Load configuration from environment variables"""
        config = {
            "vercel_url": os.getenv("VERCEL_URL", "https://insurance-navigator.vercel.app"),
            "api_url": os.getenv("API_URL", "https://insurance-navigator-api.onrender.com"),
            "worker_url": os.getenv("WORKER_URL", "https://insurance-navigator-worker.onrender.com"),
            "supabase_url": os.getenv("SUPABASE_URL", "https://znvwzkdblknkkztqyfnu.supabase.co"),
            "DOCUMENT_ENCRYPTION_KEY": os.getenv("DOCUMENT_ENCRYPTION_KEY", "test_key")
        }
        
        print("Configuration loaded:")
        for key, value in config.items():
            if "KEY" in key or "URL" in key:
                print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
        
        return config
    
    async def run_security_validation(self) -> dict:
        """Run comprehensive security validation"""
        print("\n🔒 Starting Security Validation...")
        
        async with CloudSecurityValidator(self.config) as validator:
            results = await validator.run_phase3_security_validation()
            
            print(f"Security validation completed: {results['summary']['overall_status']}")
            print(f"Overall security score: {results['summary']['overall_score']:.2f}")
            
            if results['summary']['failed_tests'] > 0:
                print(f"⚠️  {results['summary']['failed_tests']} security tests failed")
            
            return results
    
    async def run_accessibility_validation(self) -> dict:
        """Run comprehensive accessibility validation"""
        print("\n♿ Starting Accessibility Validation...")
        
        async with CloudAccessibilityValidator(self.config) as validator:
            results = await validator.run_phase3_accessibility_validation()
            
            print(f"Accessibility validation completed: {results['summary']['overall_status']}")
            print(f"Overall accessibility score: {results['summary']['overall_score']:.2f}")
            
            if results['summary']['failed_tests'] > 0:
                print(f"⚠️  {results['summary']['failed_tests']} accessibility tests failed")
            
            return results
    
    async def run_phase3_validation(self) -> dict:
        """Run complete Phase 3 validation"""
        print("🚀 Starting Phase 3: Security & Accessibility Validation")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Run security validation
            security_results = await self.run_security_validation()
            
            # Run accessibility validation
            accessibility_results = await self.run_accessibility_validation()
            
            # Calculate overall results
            total_tests = (
                security_results['summary']['total_tests'] + 
                accessibility_results['summary']['total_tests']
            )
            
            total_passed = (
                security_results['summary']['passed_tests'] + 
                accessibility_results['summary']['passed_tests']
            )
            
            total_failed = (
                security_results['summary']['failed_tests'] + 
                accessibility_results['summary']['failed_tests']
            )
            
            total_warnings = (
                security_results['summary']['warning_tests'] + 
                accessibility_results['summary']['warning_tests']
            )
            
            overall_status = "pass" if total_failed == 0 else "fail"
            
            # Calculate overall score
            security_score = security_results['summary']['overall_score']
            accessibility_score = accessibility_results['summary']['overall_score']
            overall_score = (security_score + accessibility_score) / 2
            
            # Compile comprehensive results
            comprehensive_results = {
                "timestamp": datetime.now().isoformat(),
                "test_id": f"phase3_comprehensive_{int(time.time())}",
                "phase": "Phase 3: Security & Accessibility Validation",
                "config": self.config,
                "security_validation": security_results,
                "accessibility_validation": accessibility_results,
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": total_passed,
                    "failed_tests": total_failed,
                    "warning_tests": total_warnings,
                    "overall_status": overall_status,
                    "overall_score": overall_score,
                    "security_score": security_score,
                    "accessibility_score": accessibility_score
                },
                "execution_time": time.time() - start_time
            }
            
            # Print summary
            print("\n" + "=" * 60)
            print("📊 PHASE 3 VALIDATION SUMMARY")
            print("=" * 60)
            print(f"Overall Status: {overall_status.upper()}")
            print(f"Overall Score: {overall_score:.2f}")
            print(f"Security Score: {security_score:.2f}")
            print(f"Accessibility Score: {accessibility_score:.2f}")
            print(f"Total Tests: {total_tests}")
            print(f"Passed: {total_passed}")
            print(f"Failed: {total_failed}")
            print(f"Warnings: {total_warnings}")
            print(f"Execution Time: {time.time() - start_time:.2f} seconds")
            
            # Print detailed results
            if total_failed > 0:
                print("\n⚠️  FAILED TESTS:")
                if security_results['summary']['failed_tests'] > 0:
                    print(f"  Security: {security_results['summary']['failed_tests']} failed")
                if accessibility_results['summary']['failed_tests'] > 0:
                    print(f"  Accessibility: {accessibility_results['summary']['failed_tests']} failed")
            
            if total_warnings > 0:
                print("\n⚠️  WARNINGS:")
                if security_results['summary']['warning_tests'] > 0:
                    print(f"  Security: {security_results['summary']['warning_tests']} warnings")
                if accessibility_results['summary']['warning_tests'] > 0:
                    print(f"  Accessibility: {accessibility_results['summary']['warning_tests']} warnings")
            
            # Save results
            self._save_results(comprehensive_results)
            
            return comprehensive_results
            
        except Exception as e:
            print(f"❌ Phase 3 validation failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "test_id": f"phase3_comprehensive_{int(time.time())}",
                "phase": "Phase 3: Security & Accessibility Validation",
                "config": self.config,
                "error": str(e),
                "summary": {
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 1,
                    "warning_tests": 0,
                    "overall_status": "error"
                },
                "execution_time": time.time() - start_time
            }
    
    def _save_results(self, results: dict):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phase3_validation_results_{timestamp}.json"
        filepath = Path(__file__).parent / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📁 Results saved to: {filepath}")
    
    def print_recommendations(self, results: dict):
        """Print security and accessibility recommendations"""
        print("\n" + "=" * 60)
        print("📋 RECOMMENDATIONS")
        print("=" * 60)
        
        # Security recommendations
        if 'security_validation' in results:
            security_result = results['security_validation']
            if 'security_validation' in security_result and 'recommendations' in security_result['security_validation']:
                recommendations = security_result['security_validation']['recommendations']
                if recommendations:
                    print("\n🔒 Security Recommendations:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"  {i}. {rec}")
        
        # Accessibility recommendations
        if 'accessibility_validation' in results:
            accessibility_result = results['accessibility_validation']
            if 'accessibility_validation' in accessibility_result and 'recommendations' in accessibility_result['accessibility_validation']:
                recommendations = accessibility_result['accessibility_validation']['recommendations']
                if recommendations:
                    print("\n♿ Accessibility Recommendations:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"  {i}. {rec}")

async def main():
    """Main function to run Phase 3 validation"""
    test_suite = Phase3TestSuite()
    
    try:
        results = await test_suite.run_phase3_validation()
        
        # Print recommendations
        test_suite.print_recommendations(results)
        
        # Exit with appropriate code
        if results['summary']['overall_status'] == 'pass':
            print("\n✅ Phase 3 validation completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Phase 3 validation failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Phase 3 validation encountered an error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
