#!/usr/bin/env python3
"""
Production Readiness Validation Script

This script runs comprehensive validation tests to ensure the Insurance Navigator
system meets all production readiness requirements after Phase 3 implementation.

Usage:
    python validate_production_readiness.py [--base-url http://localhost:8000] [--output results.json]
"""

import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Import validation suite
from tests.phase3_production_validation import run_phase3_validation
from tests.test_utilities.validation_helper import validate_production_readiness

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_validation_summary(results: Dict[str, Any]) -> None:
    """Print a comprehensive validation summary."""
    print("\n" + "="*80)
    print("PHASE 3 PRODUCTION READINESS VALIDATION REPORT")
    print("="*80)
    
    # Overall status
    overall_success = results.get("success", False)
    success_rate = results.get("success_rate", 0.0)
    
    status_emoji = "✅" if overall_success else "❌"
    print(f"\n{status_emoji} OVERALL STATUS: {'PRODUCTION READY' if overall_success else 'NOT READY FOR PRODUCTION'}")
    print(f"📊 SUCCESS RATE: {success_rate:.1%} ({results.get('passed_tests', 0)}/{results.get('total_tests', 0)} tests passed)")
    
    # Test results breakdown
    print(f"\n📋 TEST RESULTS BREAKDOWN:")
    print("-" * 40)
    
    test_results = results.get("results", [])
    for result in test_results:
        test_name = result.get("test_name", "Unknown Test")
        success = result.get("success", False)
        emoji = "✅" if success else "❌"
        print(f"{emoji} {test_name}")
        
        # Show failure details for failed tests
        if not success and "details" in result:
            error = result["details"].get("error", "Unknown error")
            print(f"   └─ Error: {error}")
    
    # Production readiness assessment
    if test_results:
        readiness_assessment = validate_production_readiness(test_results)
        print(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
        print("-" * 40)
        print(f"Ready for Production: {'Yes' if readiness_assessment['production_ready'] else 'No'}")
        print(f"Minimum Success Rate: {readiness_assessment['minimum_required']:.1%}")
        print(f"Actual Success Rate: {readiness_assessment['success_metrics']['success_rate']:.1%}")
        
        if readiness_assessment['critical_failures']:
            print(f"❗ Critical Failures: {', '.join(readiness_assessment['critical_failures'])}")
        
        if readiness_assessment['warning_failures']:
            print(f"⚠️  Warning Failures: {', '.join(readiness_assessment['warning_failures'])}")
        
        print(f"\n💡 Recommendation: {readiness_assessment['recommendation']}")
    
    # Timestamp
    print(f"\n⏰ Validation completed at: {results.get('timestamp', 'Unknown')}")
    print("="*80 + "\n")

def save_results_to_file(results: Dict[str, Any], output_file: str) -> None:
    """Save validation results to a JSON file."""
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Validation results saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to save results to {output_file}: {e}")

async def main():
    """Main validation execution function."""
    parser = argparse.ArgumentParser(
        description="Validate Insurance Navigator production readiness"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the API server (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--output",
        help="Output file for validation results (JSON format)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting Phase 3 Production Readiness Validation")
    logger.info(f"Target URL: {args.base_url}")
    
    try:
        # Run validation tests
        results = await run_phase3_validation(args.base_url)
        
        # Print summary
        print_validation_summary(results)
        
        # Save results if output file specified
        if args.output:
            save_results_to_file(results, args.output)
        
        # Exit with appropriate code
        if results.get("success", False):
            logger.info("✅ All validation tests passed - System is ready for production")
            sys.exit(0)
        else:
            logger.error("❌ Validation tests failed - System is NOT ready for production")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        print(f"\n❌ VALIDATION FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
