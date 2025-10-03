#!/usr/bin/env python3
"""
Phase C Testing with Local Backend + Production Supabase
Execute Phase C tests using local backend services with production Supabase database.

This configuration allows testing the complete UUID pipeline with real production data
while using local backend services for easier debugging and development.

Usage:
    python run_phase_c_local_prod_tests.py [--verbose] [--test-specific TEST]

Examples:
    python run_phase_c_local_prod_tests.py
    python run_phase_c_local_prod_tests.py --verbose
    python run_phase_c_local_prod_tests.py --test-specific uuid_generation
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.phase_c_local_backend_production_supabase import LocalBackendProductionSupabaseTester


class LocalProdTestExecutor:
    """Executes Phase C tests with local backend and production Supabase."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.config = self._load_configuration()
        
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration for local backend + production Supabase."""
        return {
            "backend": {
                "type": "local",
                "api_base_url": "http://localhost:8000",
                "upload_endpoint": "http://localhost:8000/upload",
                "chat_endpoint": "http://localhost:8000/chat",
                "health_endpoint": "http://localhost:8000/health"
            },
            "database": {
                "type": "production_supabase",
                "url": "https://znvwzkdblknkkztqyfnu.supabase.co",
                "database_url": "postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres",
                "pooler_url": "${DATABASE_URL}/summary['total_tests']*100):.1f}%" if summary['total_tests'] > 0 else "N/A")
        
        if summary["critical_failures"] > 0:
            print(f"\n🚨 CRITICAL ISSUES DETECTED")
            print("UUID standardization may not be ready for production deployment.")
            print("Please resolve critical issues before proceeding.")
            sys.exit(1)
        elif summary["failed"] > 0:
            print(f"\n⚠️ NON-CRITICAL ISSUES DETECTED")
            print("UUID standardization is mostly working but some issues need attention.")
            print("Consider addressing these issues for optimal performance.")
            sys.exit(2)
        else:
            print(f"\n✅ ALL TESTS PASSED")
            print("UUID standardization is working correctly with local backend and production Supabase.")
            print("Ready for Phase 3 cloud deployment.")
            sys.exit(0)
    
    def print_usage_examples(self):
        """Print usage examples."""
        print("\n" + "=" * 60)
        print("📖 USAGE EXAMPLES")
        print("=" * 60)
        
        print("1. Run all tests:")
        print("   python run_phase_c_local_prod_tests.py")
        print()
        
        print("2. Run with verbose output:")
        print("   python run_phase_c_local_prod_tests.py --verbose")
        print()
        
        print("3. Run specific test (if implemented):")
        print("   python run_phase_c_local_prod_tests.py --test-specific uuid_generation")
        print()
        
        print("4. Check prerequisites only:")
        print("   python -c \"from run_phase_c_local_prod_tests import LocalProdTestExecutor; executor = LocalProdTestExecutor(); print('Prerequisites OK' if executor._check_prerequisites() else 'Prerequisites FAILED')\"")
        print()
        
        print("5. Test local backend health:")
        print("   curl -f http://localhost:8000/health")
        print()
        
        print("6. Test production Supabase connection:")
        print("   python -c \"import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres'))\"")
        print()
        
        print("=" * 60)
        print("📋 PREREQUISITES")
        print("=" * 60)
        print("1. Local backend must be running on http://localhost:8000")
        print("2. Production Supabase database must be accessible")
        print("3. Required Python packages: aiohttp, asyncpg")
        print("4. Environment variables must be set (handled automatically)")
        print()
        
        print("=" * 60)
        print("🔧 TROUBLESHOOTING")
        print("=" * 60)
        print("If tests fail:")
        print("1. Ensure local backend is running: python main.py")
        print("2. Check database connectivity")
        print("3. Verify environment variables are set")
        print("4. Run with --verbose for detailed error information")
        print()


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Phase C Testing with Local Backend + Production Supabase")
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--test-specific",
        help="Run specific test (if implemented)"
    )
    
    parser.add_argument(
        "--help-examples",
        action="store_true",
        help="Show usage examples and troubleshooting"
    )
    
    args = parser.parse_args()
    
    if args.help_examples:
        executor = LocalProdTestExecutor(verbose=args.verbose)
        executor.print_usage_examples()
        return
    
    # Create executor and run tests
    executor = LocalProdTestExecutor(verbose=args.verbose)
    
    # Run tests
    await executor.run_tests(test_specific=args.test_specific)


if __name__ == "__main__":
    asyncio.run(main())
