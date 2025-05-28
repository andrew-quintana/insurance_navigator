#!/usr/bin/env python3
"""
Function Security Testing Script

This script tests the security fixes applied to database functions to ensure
they properly implement fixed search paths and secure authentication.

Usage:
    python test_function_security.py [--database-url DATABASE_URL]
"""

import asyncio
import asyncpg
import os
import json
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class SecurityTestResult:
    """Result of a security test."""
    test_name: str
    passed: bool
    security_level: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    vulnerability_type: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class FunctionSecurityTester:
    """Main class for testing function security."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection: Optional[asyncpg.Connection] = None
        self.test_results: List[SecurityTestResult] = []
        
        # Test user for security tests
        self.test_user_id = str(uuid.uuid4())
        self.admin_user_id = str(uuid.uuid4())
        
    async def connect(self):
        """Connect to the database."""
        try:
            self.connection = await asyncpg.connect(self.database_url)
            print("✅ Connected to database successfully")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            raise
            
    async def disconnect(self):
        """Disconnect from the database."""
        if self.connection:
            await self.connection.close()
            print("✅ Disconnected from database")
    
    async def setup_test_data(self):
        """Create test data for security testing."""
        print("🔧 Setting up test data...")
        
        try:
            # Create admin role if it doesn't exist
            await self.connection.execute("""
                INSERT INTO roles (id, name, description)
                VALUES ($1, 'admin', 'Administrator role')
                ON CONFLICT (name) DO NOTHING
            """, str(uuid.uuid4()))
            
            # Create test users
            await self.connection.execute("""
                INSERT INTO users (id, email, hashed_password, full_name)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (email) DO UPDATE 
                SET id = EXCLUDED.id
            """, self.test_user_id, 'test@security.com', 'hashed_password', 'Test User')
            
            await self.connection.execute("""
                INSERT INTO users (id, email, hashed_password, full_name)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (email) DO UPDATE 
                SET id = EXCLUDED.id
            """, self.admin_user_id, 'admin@security.com', 'hashed_password', 'Admin User')
            
            # Assign admin role to admin user
            admin_role_id = await self.connection.fetchval(
                "SELECT id FROM roles WHERE name = 'admin'"
            )
            
            await self.connection.execute("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES ($1, $2)
                ON CONFLICT (user_id, role_id) DO NOTHING
            """, self.admin_user_id, admin_role_id)
            
            print("✅ Test data setup completed")
            
        except Exception as e:
            print(f"❌ Error setting up test data: {e}")
            raise
    
    async def cleanup_test_data(self):
        """Clean up test data after testing."""
        print("🧹 Cleaning up test data...")
        
        try:
            # Remove test users and related data
            await self.connection.execute(
                "DELETE FROM user_roles WHERE user_id IN ($1, $2)",
                self.test_user_id, self.admin_user_id
            )
            await self.connection.execute(
                "DELETE FROM users WHERE id IN ($1, $2)",
                self.test_user_id, self.admin_user_id
            )
            
            print("✅ Test data cleanup completed")
            
        except Exception as e:
            print(f"❌ Error cleaning up test data: {e}")
    
    async def test_function_security_definer_usage(self) -> List[SecurityTestResult]:
        """Test that functions use SECURITY INVOKER instead of SECURITY DEFINER."""
        results = []
        
        try:
            # Check all functions in public schema
            functions = await self.connection.fetch("""
                SELECT proname, prosecdef, provolatile
                FROM pg_proc 
                WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                AND proname IN ('is_admin', 'get_current_user_id', 'has_role', 'can_access_policy', 'set_current_user_context', 'log_policy_access')
            """)
            
            for func in functions:
                if func['prosecdef']:  # SECURITY DEFINER
                    results.append(SecurityTestResult(
                        test_name=f"Function {func['proname']} uses SECURITY INVOKER",
                        passed=False,
                        security_level="HIGH",
                        vulnerability_type="privilege_escalation",
                        error_message=f"Function {func['proname']} uses SECURITY DEFINER instead of SECURITY INVOKER"
                    ))
                else:  # SECURITY INVOKER
                    results.append(SecurityTestResult(
                        test_name=f"Function {func['proname']} uses SECURITY INVOKER",
                        passed=True,
                        security_level="HIGH",
                        details={"function": func['proname'], "security_mode": "INVOKER"}
                    ))
                    
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Function security mode check",
                passed=False,
                security_level="CRITICAL",
                vulnerability_type="unknown",
                error_message=f"Error checking function security modes: {e}"
            ))
        
        return results
    
    async def test_search_path_injection(self) -> List[SecurityTestResult]:
        """Test that functions are protected against search path injection."""
        results = []
        
        try:
            # Try to manipulate search path and see if functions are affected
            # This test verifies that functions set their own search path
            
            # Set a malicious search path
            await self.connection.execute("SET search_path = information_schema, pg_catalog")
            
            # Test each function to see if it's affected by search path manipulation
            functions_to_test = [
                ('is_admin', 'SELECT public.is_admin()'),
                ('get_current_user_id', 'SELECT public.get_current_user_id()'),
                ('has_role', "SELECT public.has_role('admin')"),
            ]
            
            for func_name, test_query in functions_to_test:
                try:
                    # Execute function with manipulated search path
                    result = await self.connection.fetchval(test_query)
                    
                    # If function executes without error, it likely has fixed search path
                    results.append(SecurityTestResult(
                        test_name=f"Function {func_name} resistant to search path injection",
                        passed=True,
                        security_level="HIGH",
                        details={"function": func_name, "result": str(result)}
                    ))
                    
                except Exception as e:
                    # If function fails, it might be vulnerable to search path injection
                    results.append(SecurityTestResult(
                        test_name=f"Function {func_name} resistant to search path injection",
                        passed=False,
                        security_level="HIGH",
                        vulnerability_type="search_path_injection",
                        error_message=f"Function failed with manipulated search path: {e}"
                    ))
            
            # Reset search path
            await self.connection.execute("RESET search_path")
            
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Search path injection test",
                passed=False,
                security_level="CRITICAL",
                vulnerability_type="unknown",
                error_message=f"Error testing search path injection: {e}"
            ))
        
        return results
    
    async def test_admin_function_logic(self) -> List[SecurityTestResult]:
        """Test that admin function has proper authentication logic."""
        results = []
        
        try:
            # Test 1: Without any user context, should return false
            result = await self.connection.fetchval("SELECT public.is_admin()")
            
            results.append(SecurityTestResult(
                test_name="is_admin() returns false without user context",
                passed=result is False,
                security_level="CRITICAL",
                vulnerability_type="authentication_bypass" if result else None,
                error_message=None if result is False else f"Function returned {result} instead of false"
            ))
            
            # Test 2: With regular user context, should return false
            await self.connection.execute(
                "SELECT public.set_current_user_context($1)", 
                self.test_user_id
            )
            
            result = await self.connection.fetchval("SELECT public.is_admin()")
            
            results.append(SecurityTestResult(
                test_name="is_admin() returns false for regular user",
                passed=result is False,
                security_level="CRITICAL",
                vulnerability_type="privilege_escalation" if result else None,
                error_message=None if result is False else f"Regular user reported as admin: {result}"
            ))
            
            # Test 3: With admin user context, should return true
            await self.connection.execute(
                "SELECT public.set_current_user_context($1)", 
                self.admin_user_id
            )
            
            result = await self.connection.fetchval("SELECT public.is_admin()")
            
            results.append(SecurityTestResult(
                test_name="is_admin() returns true for admin user",
                passed=result is True,
                security_level="MEDIUM",
                error_message=None if result is True else f"Admin user not recognized: {result}"
            ))
            
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Admin function logic test",
                passed=False,
                security_level="CRITICAL",
                vulnerability_type="unknown",
                error_message=f"Error testing admin function: {e}"
            ))
        
        return results
    
    async def test_user_id_function_security(self) -> List[SecurityTestResult]:
        """Test that get_current_user_id function doesn't return hardcoded values."""
        results = []
        
        try:
            # Test 1: Without user context, should return null
            result = await self.connection.fetchval("SELECT public.get_current_user_id()")
            
            results.append(SecurityTestResult(
                test_name="get_current_user_id() returns null without context",
                passed=result is None,
                security_level="HIGH",
                vulnerability_type="authentication_bypass" if result else None,
                error_message=None if result is None else f"Function returned {result} instead of null"
            ))
            
            # Test 2: With user context, should return correct user ID
            await self.connection.execute(
                "SELECT public.set_current_user_context($1)", 
                self.test_user_id
            )
            
            result = await self.connection.fetchval("SELECT public.get_current_user_id()")
            
            results.append(SecurityTestResult(
                test_name="get_current_user_id() returns correct user ID",
                passed=str(result) == self.test_user_id,
                security_level="HIGH",
                error_message=None if str(result) == self.test_user_id else f"Wrong user ID returned: {result}"
            ))
            
            # Test 3: Check it's not returning the old hardcoded UUID
            hardcoded_uuid = '00000000-0000-0000-0000-000000000000'
            
            results.append(SecurityTestResult(
                test_name="get_current_user_id() doesn't return hardcoded UUID",
                passed=str(result) != hardcoded_uuid,
                security_level="CRITICAL",
                vulnerability_type="hardcoded_credentials" if str(result) == hardcoded_uuid else None,
                error_message=None if str(result) != hardcoded_uuid else "Function still returns hardcoded UUID"
            ))
            
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="User ID function security test",
                passed=False,
                security_level="CRITICAL",
                vulnerability_type="unknown",
                error_message=f"Error testing user ID function: {e}"
            ))
        
        return results
    
    async def test_function_input_validation(self) -> List[SecurityTestResult]:
        """Test that functions properly validate input parameters."""
        results = []
        
        try:
            # Test has_role with null input
            result = await self.connection.fetchval("SELECT public.has_role(NULL)")
            
            results.append(SecurityTestResult(
                test_name="has_role() handles null input securely",
                passed=result is False,
                security_level="MEDIUM",
                error_message=None if result is False else f"Function should return false for null input: {result}"
            ))
            
            # Test has_role with empty string
            result = await self.connection.fetchval("SELECT public.has_role('')")
            
            results.append(SecurityTestResult(
                test_name="has_role() handles empty string securely",
                passed=result is False,
                security_level="MEDIUM",
                error_message=None if result is False else f"Function should return false for empty string: {result}"
            ))
            
            # Test can_access_policy with null input
            result = await self.connection.fetchval("SELECT public.can_access_policy(NULL)")
            
            results.append(SecurityTestResult(
                test_name="can_access_policy() handles null input securely",
                passed=result is False,
                security_level="MEDIUM",
                error_message=None if result is False else f"Function should return false for null input: {result}"
            ))
            
            # Test set_current_user_context with null input (should raise exception)
            try:
                await self.connection.fetchval("SELECT public.set_current_user_context(NULL)")
                results.append(SecurityTestResult(
                    test_name="set_current_user_context() rejects null input",
                    passed=False,
                    security_level="HIGH",
                    vulnerability_type="input_validation",
                    error_message="Function should raise exception for null input"
                ))
            except Exception:
                results.append(SecurityTestResult(
                    test_name="set_current_user_context() rejects null input",
                    passed=True,
                    security_level="HIGH"
                ))
            
        except Exception as e:
            results.append(SecurityTestResult(
                test_name="Function input validation test",
                passed=False,
                security_level="HIGH",
                vulnerability_type="unknown",
                error_message=f"Error testing input validation: {e}"
            ))
        
        return results
    
    async def run_all_security_tests(self) -> Dict[str, Any]:
        """Run all security tests."""
        print("🔒 Starting function security tests...")
        
        try:
            await self.setup_test_data()
            
            # Run all security test suites
            all_results = []
            all_results.extend(await self.test_function_security_definer_usage())
            all_results.extend(await self.test_search_path_injection())
            all_results.extend(await self.test_admin_function_logic())
            all_results.extend(await self.test_user_id_function_security())
            all_results.extend(await self.test_function_input_validation())
            
            self.test_results = all_results
            
            return self.generate_security_report()
            
        finally:
            await self.cleanup_test_data()
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate a comprehensive security test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        # Group by security level
        by_security_level = {}
        vulnerabilities = []
        
        for result in self.test_results:
            level = result.security_level
            if level not in by_security_level:
                by_security_level[level] = {'total': 0, 'passed': 0, 'failed': 0}
            
            by_security_level[level]['total'] += 1
            if result.passed:
                by_security_level[level]['passed'] += 1
            else:
                by_security_level[level]['failed'] += 1
                if result.vulnerability_type:
                    vulnerabilities.append({
                        'test': result.test_name,
                        'type': result.vulnerability_type,
                        'level': result.security_level,
                        'message': result.error_message
                    })
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 100.0
            },
            'security_levels': by_security_level,
            'vulnerabilities': vulnerabilities,
            'detailed_results': [asdict(result) for result in self.test_results],
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on test results."""
        recommendations = []
        
        critical_failures = [r for r in self.test_results 
                           if not r.passed and r.security_level == 'CRITICAL']
        high_failures = [r for r in self.test_results 
                        if not r.passed and r.security_level == 'HIGH']
        
        if critical_failures:
            recommendations.append(
                f"CRITICAL: {len(critical_failures)} critical security issues found. Address immediately."
            )
        
        if high_failures:
            recommendations.append(
                f"HIGH: {len(high_failures)} high-severity security issues found. Address urgently."
            )
        
        # Check for specific vulnerability types
        vuln_types = set(r.vulnerability_type for r in self.test_results 
                        if not r.passed and r.vulnerability_type)
        
        if 'search_path_injection' in vuln_types:
            recommendations.append(
                "Implement fixed search paths in all database functions to prevent injection attacks."
            )
        
        if 'privilege_escalation' in vuln_types:
            recommendations.append(
                "Review and fix privilege escalation vulnerabilities in authentication functions."
            )
        
        if 'hardcoded_credentials' in vuln_types:
            recommendations.append(
                "Remove hardcoded credentials and implement proper authentication mechanisms."
            )
        
        if not recommendations:
            recommendations.append("All security tests passed. Continue monitoring for new vulnerabilities.")
        
        return recommendations
    
    def print_security_summary(self, report: Dict[str, Any]):
        """Print a summary of security test results."""
        print("\n" + "="*60)
        print("🔒 FUNCTION SECURITY TEST RESULTS")
        print("="*60)
        
        summary = report['summary']
        print(f"📊 Total tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Success rate: {summary['success_rate']:.1f}%")
        
        # Security level breakdown
        print("\n🔒 Security Level Breakdown:")
        levels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        for level in levels:
            if level in report['security_levels']:
                data = report['security_levels'][level]
                status = "✅" if data['failed'] == 0 else "❌"
                print(f"  {status} {level}: {data['passed']}/{data['total']} passed")
        
        # Show vulnerabilities
        if report['vulnerabilities']:
            print("\n🚨 Security Vulnerabilities Found:")
            for vuln in report['vulnerabilities']:
                print(f"  ❌ {vuln['level']}: {vuln['test']}")
                print(f"     Type: {vuln['type']}")
                print(f"     Details: {vuln['message']}")
        
        # Show recommendations
        if report['recommendations']:
            print("\n📋 Security Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")

async def main():
    """Main function to run security tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test database function security')
    parser.add_argument('--database-url', help='Database URL (defaults to DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Error: Database URL not provided. Use --database-url or set DATABASE_URL environment variable")
        return
    
    # Run security tests
    tester = FunctionSecurityTester(database_url)
    
    try:
        await tester.connect()
        report = await tester.run_all_security_tests()
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'function_security_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to {report_file}")
        
        # Print summary
        tester.print_security_summary(report)
        
        # Exit with appropriate code
        if report['summary']['failed'] > 0:
            print("\n❌ Security tests failed! Review and fix vulnerabilities.")
            exit(1)
        else:
            print("\n✅ All security tests passed!")
            exit(0)
        
    except Exception as e:
        print(f"❌ Error running security tests: {e}")
        exit(1)
    finally:
        await tester.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 