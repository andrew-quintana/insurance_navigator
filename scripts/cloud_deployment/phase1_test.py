#!/usr/bin/env python3
"""
Phase 1 Cloud Deployment Test Execution Script

Executes autonomous testing for cloud environment setup and validation.
Tests Vercel frontend, Render backend, and Supabase database connectivity.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from testing.cloud_deployment.phase1_validator import CloudEnvironmentValidator


class Phase1TestRunner:
    """Runs Phase 1 cloud deployment tests"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    async def run_all_tests(self) -> dict:
        """Run all Phase 1 tests and return results"""
        print("🚀 Starting Phase 1 Cloud Deployment Testing")
        print("=" * 60)
        
        self.start_time = datetime.now()
        
        # Load configuration
        config = self._load_configuration()
        
        # Run tests
        async with CloudEnvironmentValidator(config) as validator:
            print("\n📱 Testing Vercel Frontend Deployment...")
            vercel_result = await validator.validate_vercel_deployment()
            self.results['vercel'] = vercel_result.to_dict()
            self._print_test_result("Vercel", vercel_result)
            
            print("\n🔧 Testing Render Backend Deployment...")
            render_result = await validator.validate_render_deployment()
            self.results['render'] = render_result.to_dict()
            self._print_test_result("Render", render_result)
            
            print("\n🗄️  Testing Supabase Database Connectivity...")
            supabase_result = await validator.validate_supabase_connectivity()
            self.results['supabase'] = supabase_result.to_dict()
            self._print_test_result("Supabase", supabase_result)
        
        self.end_time = datetime.now()
        
        # Generate summary
        summary = self._generate_summary()
        self.results['summary'] = summary
        
        # Print final results
        self._print_final_summary(summary)
        
        return self.results
    
    def _load_configuration(self) -> dict:
        """Load configuration from environment variables"""
        config = {
            'vercel_url': os.getenv('VERCEL_URL', 'https://insurance-navigator.vercel.app'),
            'render_url': os.getenv('RENDER_URL', 'https://insurance-navigator-api.onrender.com'),
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_anon_key': os.getenv('SUPABASE_ANON_KEY'),
            'supabase_service_key': os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
            'api_base_url': os.getenv('API_BASE_URL', 'https://insurance-navigator-api.onrender.com'),
        }
        
        print(f"Configuration loaded:")
        print(f"  Vercel URL: {config['vercel_url']}")
        print(f"  Render URL: {config['render_url']}")
        print(f"  Supabase URL: {config['supabase_url'] or 'Not configured'}")
        print(f"  API Base URL: {config['api_base_url']}")
        
        return config
    
    def _print_test_result(self, service_name: str, result):
        """Print individual test result"""
        status_emoji = {
            'pass': '✅',
            'fail': '❌',
            'warning': '⚠️'
        }
        
        emoji = status_emoji.get(result.status, '❓')
        print(f"  {emoji} {service_name} Validation: {result.status.upper()}")
        
        if result.errors:
            print(f"    Errors: {len(result.errors)}")
            for error in result.errors:
                print(f"      - {error}")
        
        if result.metrics:
            print(f"    Metrics: {len(result.metrics)} collected")
            if 'total_validation_time' in result.metrics:
                print(f"    Validation Time: {result.metrics['total_validation_time']:.2f}s")
    
    def _generate_summary(self) -> dict:
        """Generate test summary"""
        total_tests = len(self.results) - 1  # Exclude summary itself
        passed_tests = sum(1 for result in self.results.values() 
                          if isinstance(result, dict) and result.get('status') == 'pass')
        failed_tests = sum(1 for result in self.results.values() 
                          if isinstance(result, dict) and result.get('status') == 'fail')
        warning_tests = sum(1 for result in self.results.values() 
                           if isinstance(result, dict) and result.get('status') == 'warning')
        
        total_time = (self.end_time - self.start_time).total_seconds()
        
        # Check if all tests passed (100% pass rate required)
        all_passed = failed_tests == 0 and warning_tests == 0
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'warning_tests': warning_tests,
            'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'all_tests_passed': all_passed,
            'total_execution_time': total_time,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'phase1_complete': all_passed,
            'ready_for_phase2': all_passed
        }
        
        return summary
    
    def _print_final_summary(self, summary: dict):
        """Print final test summary"""
        print("\n" + "=" * 60)
        print("📊 PHASE 1 TEST SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Warnings: {summary['warning_tests']} ⚠️")
        print(f"Pass Rate: {summary['pass_rate']:.1f}%")
        print(f"Total Execution Time: {summary['total_execution_time']:.2f}s")
        
        print("\n" + "-" * 60)
        
        if summary['all_tests_passed']:
            print("🎉 PHASE 1 COMPLETED SUCCESSFULLY!")
            print("✅ All cloud environment validations passed")
            print("✅ Ready to proceed to Phase 2 (Integration & Performance Testing)")
            print("\nNext Steps:")
            print("1. Developer should perform visual validation of deployments")
            print("2. Review deployment logs and configuration")
            print("3. Test initial user experience and navigation")
            print("4. Proceed to Phase 2 when ready")
        else:
            print("❌ PHASE 1 FAILED")
            print("❌ Some cloud environment validations failed")
            print("❌ Must resolve issues before proceeding to Phase 2")
            print("\nRequired Actions:")
            print("1. Review failed tests and error messages")
            print("2. Fix deployment issues")
            print("3. Re-run Phase 1 tests")
            print("4. Achieve 100% pass rate before proceeding")
        
        print("\n" + "=" * 60)
    
    def save_results(self, output_file: str = None):
        """Save test results to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"phase1_test_results_{timestamp}.json"
        
        output_path = Path(__file__).parent / output_file
        
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Test results saved to: {output_path}")
        return output_path


async def main():
    """Main function"""
    runner = Phase1TestRunner()
    
    try:
        # Run all tests
        results = await runner.run_all_tests()
        
        # Save results
        output_file = runner.save_results()
        
        # Exit with appropriate code
        if results['summary']['all_tests_passed']:
            print("\n🎯 Phase 1 testing completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Phase 1 testing failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Phase 1 testing encountered an error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
