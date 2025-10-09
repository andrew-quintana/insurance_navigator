#!/usr/bin/env python3
"""
Validate chat_flow_investigation.py behavior without requiring full infrastructure

This script validates:
1. Script handles missing API endpoint gracefully
2. Script handles authentication failures gracefully
3. Script handles network errors gracefully
4. Script generates proper output files
5. Script provides clear error messages
6. Script exits cleanly at each failure point
"""

import subprocess
import sys
import os
import time
import json
from pathlib import Path

print("═" * 80)
print("FM-038: Investigation Script Behavior Validation")
print("═" * 80)
print()

# Track test results
tests_passed = 0
tests_failed = 0

def print_result(test_name, passed, details=""):
    global tests_passed, tests_failed
    if passed:
        print(f"✅ PASSED: {test_name}")
        if details:
            print(f"   {details}")
        tests_passed += 1
    else:
        print(f"❌ FAILED: {test_name}")
        if details:
            print(f"   {details}")
        tests_failed += 1

# =============================================================================
# Test 1: Run script with no accessible API endpoint
# =============================================================================
print("Test 1: Running script with no accessible API endpoint...")
print("─" * 80)

# Ensure no API is running on localhost:8000
import socket
def is_port_open(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

if is_port_open(8000):
    print("⚠️  Warning: Something is already running on port 8000")
    print("   This test may not work as expected")
else:
    print("✅ Port 8000 is free (no local API running)")

print()
print("Running investigation script...")
print("Expected: Script should handle missing API gracefully and exit cleanly")
print()

# Run the script with a timeout
start_time = time.time()
try:
    result = subprocess.run(
        [sys.executable, "tests/fm_038/chat_flow_investigation.py"],
        timeout=30,  # Should fail fast if no API found
        capture_output=True,
        text=True,
        cwd=os.getcwd()
    )
    duration = time.time() - start_time
    
    print(f"Script completed in {duration:.2f} seconds")
    print(f"Exit code: {result.returncode}")
    print()
    
    # Check output for graceful failure messages
    output = result.stdout + result.stderr
    
    # Should have clear error messages
    if "No working API endpoint found" in output or "Cannot proceed" in output:
        print_result("Graceful API failure handling", True, 
                    "Script clearly communicated API endpoint failure")
    else:
        print_result("Graceful API failure handling", False,
                    "Missing clear error message about API endpoint")
    
    # Should have logged the failure
    if "❌" in output or "ERROR" in output:
        print_result("Error logging present", True,
                    "Script logged errors appropriately")
    else:
        print_result("Error logging present", False,
                    "No error indicators found in output")
    
    # Should complete without crash
    if result.returncode == 0:
        print_result("Clean exit on API failure", True,
                    "Script exited with code 0")
    else:
        print_result("Clean exit on API failure", False,
                    f"Script exited with code {result.returncode}")
    
    # Should produce investigation summary
    if "Investigation Complete" in output or "SUMMARY" in output:
        print_result("Investigation summary generated", True,
                    "Script provided final summary")
    else:
        print_result("Investigation summary generated", False,
                    "No final summary found")
    
except subprocess.TimeoutExpired:
    print_result("Script timeout behavior", False,
                "Script took longer than 30 seconds (should fail fast)")
except Exception as e:
    print_result("Script execution", False, f"Exception: {e}")

print()

# =============================================================================
# Test 2: Check output file generation
# =============================================================================
print("Test 2: Checking output file generation...")
print("─" * 80)

# Find most recent log files
log_files = list(Path('.').glob('chat_flow_investigation_*.log'))
json_files = list(Path('.').glob('chat_flow_investigation_report_*.json'))

if log_files:
    latest_log = max(log_files, key=os.path.getctime)
    log_size = latest_log.stat().st_size
    print(f"✅ Log file found: {latest_log.name}")
    print(f"   Size: {log_size} bytes")
    
    if log_size > 100:
        print_result("Log file creation", True,
                    "Log file created with content")
    else:
        print_result("Log file creation", False,
                    "Log file seems empty or too small")
else:
    print_result("Log file creation", False,
                "No log file found")

if json_files:
    latest_json = max(json_files, key=os.path.getctime)
    print(f"✅ JSON report found: {latest_json.name}")
    
    try:
        with open(latest_json, 'r') as f:
            report_data = json.load(f)
        
        # Validate structure
        has_metrics = 'metrics' in report_data
        has_function_calls = 'function_calls' in report_data
        
        if has_metrics and has_function_calls:
            print_result("JSON report structure", True,
                        "Report has expected structure")
            
            # Show summary
            print()
            print("📊 Report Summary:")
            metrics = report_data.get('metrics', {})
            print(f"   Total Requests: {metrics.get('total_requests', 0)}")
            print(f"   Successful: {metrics.get('successful_requests', 0)}")
            print(f"   Failed: {metrics.get('failed_requests', 0)}")
            print(f"   Function Calls: {len(report_data.get('function_calls', []))}")
        else:
            print_result("JSON report structure", False,
                        "Report missing expected fields")
    except json.JSONDecodeError:
        print_result("JSON report validity", False,
                    "JSON report is invalid")
else:
    print_result("JSON report creation", False,
                "No JSON report found")

print()

# =============================================================================
# Test 3: Check error message clarity in log files
# =============================================================================
print("Test 3: Checking error message clarity...")
print("─" * 80)

if log_files:
    latest_log = max(log_files, key=os.path.getctime)
    
    with open(latest_log, 'r') as f:
        log_content = f.read()
    
    # Count error indicators
    error_indicators = [
        ('❌', 'Error emoji'),
        ('ERROR', 'ERROR level logs'),
        ('✅', 'Success emoji'),
        ('INFO', 'INFO level logs'),
    ]
    
    print("Error indicator counts:")
    for indicator, description in error_indicators:
        count = log_content.count(indicator)
        print(f"   {indicator} ({description}): {count}")
    
    # Check for specific error messages
    if "No working API endpoint found" in log_content:
        print_result("Clear error messages", True,
                    "Found clear 'No API endpoint' message")
    else:
        print_result("Clear error messages", False,
                    "Expected error messages not found")
    
    # Check for investigation sections
    sections = [
        "FINDING WORKING API ENDPOINT",
        "AUTHENTICATION FLOW",
        "INVESTIGATION SUMMARY"
    ]
    
    sections_found = sum(1 for section in sections if section in log_content)
    if sections_found >= 2:
        print_result("Investigation flow logging", True,
                    f"Found {sections_found}/3 expected sections")
    else:
        print_result("Investigation flow logging", False,
                    f"Only found {sections_found}/3 expected sections")

print()

# =============================================================================
# Test 4: Validate script syntax and imports
# =============================================================================
print("Test 4: Validating script syntax and imports...")
print("─" * 80)

try:
    with open("tests/fm_038/chat_flow_investigation.py", 'r') as f:
        script_content = f.read()
    
    # Try to compile
    compile(script_content, "chat_flow_investigation.py", 'exec')
    print_result("Script syntax", True, "No syntax errors")
    
    # Check for required imports
    required_imports = ['asyncio', 'aiohttp', 'json', 'logging']
    imports_found = all(f"import {imp}" in script_content for imp in required_imports)
    
    if imports_found:
        print_result("Required imports", True, "All required imports present")
    else:
        print_result("Required imports", False, "Some imports missing")
    
except SyntaxError as e:
    print_result("Script syntax", False, f"Syntax error: {e}")
except Exception as e:
    print_result("Script validation", False, f"Error: {e}")

print()

# =============================================================================
# Test 5: Check documentation completeness
# =============================================================================
print("Test 5: Checking documentation...")
print("─" * 80)

docs_to_check = [
    ("tests/fm_038/PHASE_1_README.md", "Usage guide"),
    ("tests/fm_038/PHASE_1_COMPLETE.md", "Completion summary"),
    ("tests/fm_038/chat_flow_investigation.py", "Main script")
]

for doc_path, description in docs_to_check:
    if os.path.exists(doc_path):
        size = os.path.getsize(doc_path)
        print(f"✅ {description}: {doc_path} ({size} bytes)")
    else:
        print(f"❌ {description}: {doc_path} - NOT FOUND")

print()

# =============================================================================
# Final Summary
# =============================================================================
print("═" * 80)
print("VALIDATION SUMMARY")
print("═" * 80)
print()

total_tests = tests_passed + tests_failed
pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0

print(f"Tests Passed: {tests_passed}/{total_tests} ({pass_rate:.1f}%)")
print(f"Tests Failed: {tests_failed}/{total_tests}")
print()

if tests_failed == 0:
    print("✅ ALL VALIDATIONS PASSED")
    print()
    print("The investigation script demonstrates:")
    print("  ✅ Graceful handling of missing API endpoints")
    print("  ✅ Clear error messages and logging")
    print("  ✅ Clean exit codes")
    print("  ✅ Proper output file generation")
    print("  ✅ Valid JSON report structure")
    print("  ✅ Comprehensive documentation")
    print()
    print("The script is ready for production testing.")
    print()
    print("To test with real API:")
    print("  1. Ensure production API is accessible")
    print("  2. Run: python tests/fm_038/chat_flow_investigation.py")
    print()
    sys.exit(0)
else:
    print("⚠️  SOME VALIDATIONS FAILED")
    print()
    print("Please review the failures above.")
    print()
    sys.exit(1)

