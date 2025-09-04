#!/usr/bin/env python3
"""
RAG Test Suite Runner

Main entry point for running RAG pipeline tests with flexible document ID configuration.

Usage:
    python run_rag_tests.py                           # Test with default document ID
    python run_rag_tests.py <document-id>             # Test with specific document ID
    python run_rag_tests.py --quick                   # Quick validation test
    python run_rag_tests.py <document-id> --quick     # Quick test with specific document
    python run_rag_tests.py --integration             # Run integration tests
    python run_rag_tests.py --all                     # Run all tests (basic + integration)
"""

import asyncio
import sys
import logging
import argparse
from typing import Dict, Any, Optional

# Import test modules
from tests.rag.test_rag_runner import RAGTestRunner, test_current_document, test_document
from tests.rag.test_langgraph_integration import test_langgraph_integration
from tests.config.rag_test_config import get_test_config, update_document_id

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{title.center(60)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_results(results: Dict[str, bool], test_type: str = "Tests"):
    """Print test results with colors."""
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"\n{Colors.BOLD}{test_type} Results: {passed}/{total} passed{Colors.END}")
    
    for test_name, success in results.items():
        status_color = Colors.GREEN if success else Colors.RED
        status_text = "PASS" if success else "FAIL"
        print(f"  {status_color}{'✓' if success else '✗'} {test_name}: {status_text}{Colors.END}")

async def run_basic_tests(document_id: Optional[str] = None) -> Dict[str, bool]:
    """Run basic RAG pipeline tests."""
    print_header("RAG Pipeline Basic Tests")
    
    if document_id:
        print(f"Testing with document ID: {Colors.YELLOW}{document_id}{Colors.END}")
        results = await test_document(document_id)
    else:
        config = get_test_config()
        print(f"Testing with default document ID: {Colors.YELLOW}{config.primary_document.document_id}{Colors.END}")
        results = await test_current_document()
    
    print_results(results, "Basic Tests")
    return results

async def run_integration_tests(document_id: Optional[str] = None) -> Dict[str, bool]:
    """Run LangGraph integration tests."""
    print_header("LangGraph Integration Tests")
    
    if document_id:
        print(f"Testing integration with document ID: {Colors.YELLOW}{document_id}{Colors.END}")
    else:
        config = get_test_config()
        print(f"Testing integration with default document ID: {Colors.YELLOW}{config.primary_document.document_id}{Colors.END}")
    
    results = await test_langgraph_integration(document_id)
    print_results(results, "Integration Tests")
    return results

async def run_quick_test(document_id: Optional[str] = None) -> bool:
    """Run a quick validation test."""
    print_header("Quick RAG Validation")
    
    runner = RAGTestRunner(document_id=document_id)
    
    if document_id:
        print(f"Quick test with document ID: {Colors.YELLOW}{document_id}{Colors.END}")
    else:
        print(f"Quick test with default document ID: {Colors.YELLOW}{runner.config.primary_document.document_id}{Colors.END}")
    
    # Test essentials
    doc_exists = await runner.test_document_exists()
    has_vectors = await runner.test_document_vectorization()
    search_works = await runner.test_vector_search()
    
    success = doc_exists and has_vectors and search_works
    
    if success:
        print(f"\n{Colors.GREEN}✓ Quick validation PASSED - RAG pipeline is ready{Colors.END}")
    else:
        print(f"\n{Colors.RED}✗ Quick validation FAILED - RAG pipeline needs attention{Colors.END}")
    
    return success

async def run_all_tests(document_id: Optional[str] = None) -> Dict[str, Any]:
    """Run all tests (basic + integration)."""
    print_header("Complete RAG Test Suite")
    
    if document_id:
        print(f"Running complete test suite with document ID: {Colors.YELLOW}{document_id}{Colors.END}")
    else:
        config = get_test_config()
        print(f"Running complete test suite with default document ID: {Colors.YELLOW}{config.primary_document.document_id}{Colors.END}")
    
    # Run basic tests
    basic_results = await run_basic_tests(document_id)
    
    # Run integration tests
    integration_results = await run_integration_tests(document_id)
    
    # Combined results
    all_results = {
        "basic": basic_results,
        "integration": integration_results
    }
    
    # Overall summary
    basic_passed = sum(1 for result in basic_results.values() if result)
    basic_total = len(basic_results)
    integration_passed = sum(1 for result in integration_results.values() if result)
    integration_total = len(integration_results)
    
    total_passed = basic_passed + integration_passed
    total_tests = basic_total + integration_total
    
    print_header("Overall Test Summary")
    print(f"Basic Tests: {Colors.GREEN if basic_passed == basic_total else Colors.RED}{basic_passed}/{basic_total}{Colors.END}")
    print(f"Integration Tests: {Colors.GREEN if integration_passed == integration_total else Colors.RED}{integration_passed}/{integration_total}{Colors.END}")
    print(f"Total: {Colors.GREEN if total_passed == total_tests else Colors.RED}{total_passed}/{total_tests}{Colors.END}")
    
    return all_results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RAG Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_rag_tests.py                                 # Test with default document
  python run_rag_tests.py d64bfbbe-ff7f-4b51-b220-a0fa20756d9d  # Test specific document
  python run_rag_tests.py --quick                         # Quick validation
  python run_rag_tests.py --integration                   # Integration tests only
  python run_rag_tests.py --all                          # Run all tests
        """
    )
    
    parser.add_argument('document_id', nargs='?', help='Document ID to test (optional)')
    parser.add_argument('--quick', action='store_true', help='Run quick validation test')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def run_tests():
        try:
            if args.quick:
                success = await run_quick_test(args.document_id)
                return 0 if success else 1
            elif args.integration:
                results = await run_integration_tests(args.document_id)
                failed = [name for name, passed in results.items() if not passed]
                return 0 if not failed else 1
            elif args.all:
                results = await run_all_tests(args.document_id)
                # Check if any test failed
                all_passed = True
                for test_category, test_results in results.items():
                    if not all(test_results.values()):
                        all_passed = False
                        break
                return 0 if all_passed else 1
            else:
                # Default: run basic tests
                results = await run_basic_tests(args.document_id)
                failed = [name for name, passed in results.items() if not passed]
                return 0 if not failed else 1
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
            return 1
        except Exception as e:
            print(f"\n{Colors.RED}Error running tests: {e}{Colors.END}")
            return 1
    
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
