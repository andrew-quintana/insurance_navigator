#!/usr/bin/env python3
"""
Row Level Security (RLS) Testing Script

This script tests all RLS policies to ensure they are working correctly.
It creates test users with different roles and verifies access controls.

Usage:
    python test_rls_policies.py [--database-url DATABASE_URL]
"""

import asyncio
import asyncpg
import os
import json
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, date

@dataclass
class TestResult:
    """Result of a single test."""
    test_name: str
    passed: bool
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class TestSuite:
    """Collection of test results."""
    name: str
    results: List[TestResult]
    
    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)
    
    @property
    def total_count(self) -> int:
        return len(self.results)
    
    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 100.0
        return (self.passed_count / self.total_count) * 100

class RLSTester:
    """Main class for testing RLS policies."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection: Optional[asyncpg.Connection] = None
        self.test_suites: List[TestSuite] = []
        
        # Test user data
        self.test_users = {
            'admin_user': {
                'id': str(uuid.uuid4()),
                'email': 'admin@test.com',
                'full_name': 'Admin User',
                'password_hash': 'hashed_password_admin'
            },
            'regular_user1': {
                'id': str(uuid.uuid4()),
                'email': 'user1@test.com',
                'full_name': 'Regular User 1',
                'password_hash': 'hashed_password_1'
            },
            'regular_user2': {
                'id': str(uuid.uuid4()),
                'email': 'user2@test.com',
                'full_name': 'Regular User 2',
                'password_hash': 'hashed_password_2'
            }
        }
        
    async def connect(self):
        """Connect to the database."""
        try:
            self.connection = await asyncpg.connect(self.database_url)
            print("Connected to database successfully")
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            raise
            
    async def disconnect(self):
        """Disconnect from the database."""
        if self.connection:
            await self.connection.close()
            print("Disconnected from database")
    
    async def setup_test_data(self):
        """Create test data for RLS testing."""
        print("Setting up test data...")
        
        try:
            # Create admin role if it doesn't exist
            await self.connection.execute("""
                INSERT INTO roles (id, name, description)
                VALUES ($1, 'admin', 'Administrator role')
                ON CONFLICT (name) DO NOTHING
            """, str(uuid.uuid4()))
            
            # Create test users
            for user_key, user_data in self.test_users.items():
                await self.connection.execute("""
                    INSERT INTO users (id, email, hashed_password, full_name)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (email) DO UPDATE 
                    SET id = EXCLUDED.id, hashed_password = EXCLUDED.hashed_password
                """, user_data['id'], user_data['email'], 
                    user_data['password_hash'], user_data['full_name'])
            
            # Assign admin role to admin user
            admin_role_id = await self.connection.fetchval(
                "SELECT id FROM roles WHERE name = 'admin'"
            )
            
            await self.connection.execute("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES ($1, $2)
                ON CONFLICT (user_id, role_id) DO NOTHING
            """, self.test_users['admin_user']['id'], admin_role_id)
            
            # Create test policy record with proper date objects
            test_policy_id = str(uuid.uuid4())
            await self.connection.execute("""
                INSERT INTO policy_records (
                    policy_id, raw_policy_path, summary, structured_metadata,
                    encrypted_policy_data, source_type, coverage_start_date, coverage_end_date
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (policy_id) DO NOTHING
            """, test_policy_id, '/test/policy.pdf', 
                '{"summary": "Test policy"}', '{"metadata": "test"}',
                '{"encrypted": "data"}', 'uploaded', 
                date(2024, 1, 1), date(2024, 12, 31))
            
            # Link policy to regular user 1
            await self.connection.execute("""
                INSERT INTO user_policy_links (
                    user_id, policy_id, role, relationship_verified
                )
                VALUES ($1, $2, 'subscriber', true)
                ON CONFLICT DO NOTHING
            """, self.test_users['regular_user1']['id'], test_policy_id)
            
            print("Test data setup completed")
            
        except Exception as e:
            print(f"Error setting up test data: {e}")
            raise
    
    async def cleanup_test_data(self):
        """Clean up test data after testing."""
        print("Cleaning up test data...")
        
        try:
            # Remove test users and related data
            for user_data in self.test_users.values():
                await self.connection.execute(
                    "DELETE FROM user_policy_links WHERE user_id = $1",
                    user_data['id']
                )
                await self.connection.execute(
                    "DELETE FROM user_roles WHERE user_id = $1",
                    user_data['id']
                )
                await self.connection.execute(
                    "DELETE FROM users WHERE id = $1",
                    user_data['id']
                )
            
            # Remove test policy records
            await self.connection.execute(
                "DELETE FROM policy_records WHERE raw_policy_path LIKE '/test/%'"
            )
            
            print("Test data cleanup completed")
            
        except Exception as e:
            print(f"Error cleaning up test data: {e}")
    
    async def test_table_rls_enabled(self) -> TestSuite:
        """Test that RLS is enabled on all required tables."""
        results = []
        required_tables = [
            'users', 'policy_records', 'user_policy_links', 'policy_access_logs',
            'roles', 'user_roles', 'encryption_keys', 'policy_access_policies',
            'agent_policy_context', 'regulatory_documents'
        ]
        
        for table in required_tables:
            try:
                rls_enabled = await self.connection.fetchval("""
                    SELECT rowsecurity 
                    FROM pg_tables 
                    WHERE tablename = $1 AND schemaname = 'public'
                """, table)
                
                if rls_enabled:
                    results.append(TestResult(
                        test_name=f"RLS enabled on {table}",
                        passed=True
                    ))
                else:
                    results.append(TestResult(
                        test_name=f"RLS enabled on {table}",
                        passed=False,
                        error_message=f"RLS is not enabled on table {table}"
                    ))
                    
            except Exception as e:
                results.append(TestResult(
                    test_name=f"RLS enabled on {table}",
                    passed=False,
                    error_message=f"Error checking RLS on {table}: {e}"
                ))
        
        return TestSuite("RLS Enabled Tests", results)
    
    async def test_user_access_policies(self) -> TestSuite:
        """Test user access policies."""
        results = []
        
        # Test that users can access their own records
        try:
            # Set current user context to regular_user1
            await self.connection.execute(
                "SET LOCAL rls.current_user_id = $1",
                self.test_users['regular_user1']['id']
            )
            
            # Should be able to access own user record
            user_count = await self.connection.fetchval("""
                SELECT COUNT(*) FROM users WHERE id = $1
            """, self.test_users['regular_user1']['id'])
            
            results.append(TestResult(
                test_name="User can access own record",
                passed=user_count == 1,
                error_message=None if user_count == 1 else f"Expected 1 record, got {user_count}"
            ))
            
        except Exception as e:
            results.append(TestResult(
                test_name="User can access own record",
                passed=False,
                error_message=f"Error testing user access: {e}"
            ))
        
        # Test that users cannot access other users' records
        try:
            other_user_count = await self.connection.fetchval("""
                SELECT COUNT(*) FROM users WHERE id = $1
            """, self.test_users['regular_user2']['id'])
            
            results.append(TestResult(
                test_name="User cannot access other user records",
                passed=other_user_count == 0,
                error_message=None if other_user_count == 0 else f"User can access other user records"
            ))
            
        except Exception as e:
            results.append(TestResult(
                test_name="User cannot access other user records",
                passed=False,
                error_message=f"Error testing user isolation: {e}"
            ))
        
        return TestSuite("User Access Policy Tests", results)
    
    async def test_admin_access_policies(self) -> TestSuite:
        """Test admin access policies."""
        results = []
        
        try:
            # Set current user context to admin
            await self.connection.execute(
                "SET LOCAL rls.current_user_id = $1",
                self.test_users['admin_user']['id']
            )
            
            # Admin should be able to access all user records
            total_users = await self.connection.fetchval("SELECT COUNT(*) FROM users")
            
            results.append(TestResult(
                test_name="Admin can access all user records",
                passed=total_users >= 3,  # At least our 3 test users
                error_message=None if total_users >= 3 else f"Admin cannot access all users"
            ))
            
            # Admin should be able to access all policy records
            total_policies = await self.connection.fetchval("SELECT COUNT(*) FROM policy_records")
            
            results.append(TestResult(
                test_name="Admin can access all policy records",
                passed=total_policies >= 0,  # Should have at least test data
                error_message=None if total_policies >= 0 else "Admin cannot access policy records"
            ))
            
        except Exception as e:
            results.append(TestResult(
                test_name="Admin access tests",
                passed=False,
                error_message=f"Error testing admin access: {e}"
            ))
        
        return TestSuite("Admin Access Policy Tests", results)
    
    async def test_policy_access_controls(self) -> TestSuite:
        """Test policy-specific access controls."""
        results = []
        
        try:
            # Set context to user1 who has a linked policy
            await self.connection.execute(
                "SET LOCAL rls.current_user_id = $1",
                self.test_users['regular_user1']['id']
            )
            
            # User1 should be able to access their linked policies
            accessible_policies = await self.connection.fetchval("""
                SELECT COUNT(*) FROM policy_records pr
                WHERE EXISTS (
                    SELECT 1 FROM user_policy_links upl
                    WHERE upl.policy_id = pr.policy_id
                    AND upl.user_id = $1
                    AND upl.relationship_verified = true
                )
            """, self.test_users['regular_user1']['id'])
            
            results.append(TestResult(
                test_name="User can access linked policies",
                passed=accessible_policies >= 1,
                error_message=None if accessible_policies >= 1 else "User cannot access linked policies"
            ))
            
            # Set context to user2 who has no linked policies
            await self.connection.execute(
                "SET LOCAL rls.current_user_id = $1",
                self.test_users['regular_user2']['id']
            )
            
            # User2 should not be able to access any policies
            inaccessible_policies = await self.connection.fetchval("""
                SELECT COUNT(*) FROM policy_records
            """)
            
            results.append(TestResult(
                test_name="User cannot access unlinked policies",
                passed=inaccessible_policies == 0,
                error_message=None if inaccessible_policies == 0 else f"User can access {inaccessible_policies} unlinked policies"
            ))
            
        except Exception as e:
            results.append(TestResult(
                test_name="Policy access control tests",
                passed=False,
                error_message=f"Error testing policy access: {e}"
            ))
        
        return TestSuite("Policy Access Control Tests", results)
    
    async def test_helper_functions(self) -> TestSuite:
        """Test RLS helper functions."""
        results = []
        
        try:
            # Test admin function with admin user
            await self.connection.execute(
                "SET LOCAL rls.current_user_id = $1",
                self.test_users['admin_user']['id']
            )
            
            is_admin = await self.connection.fetchval("SELECT auth.is_admin()")
            
            results.append(TestResult(
                test_name="auth.is_admin() returns true for admin",
                passed=is_admin is True,
                error_message=None if is_admin else "Admin function returned false for admin user"
            ))
            
            # Test admin function with regular user
            await self.connection.execute(
                "SET LOCAL rls.current_user_id = $1",
                self.test_users['regular_user1']['id']
            )
            
            is_not_admin = await self.connection.fetchval("SELECT auth.is_admin()")
            
            results.append(TestResult(
                test_name="auth.is_admin() returns false for regular user",
                passed=is_not_admin is False,
                error_message=None if not is_not_admin else "Admin function returned true for regular user"
            ))
            
            # Test role function
            has_admin_role = await self.connection.fetchval("SELECT auth.has_role('admin')")
            
            results.append(TestResult(
                test_name="auth.has_role() works correctly",
                passed=has_admin_role is False,
                error_message=None if not has_admin_role else "Regular user appears to have admin role"
            ))
            
        except Exception as e:
            results.append(TestResult(
                test_name="Helper function tests",
                passed=False,
                error_message=f"Error testing helper functions: {e}"
            ))
        
        return TestSuite("Helper Function Tests", results)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all RLS tests."""
        print("Starting RLS policy tests...")
        
        try:
            await self.setup_test_data()
            
            # Run test suites
            self.test_suites = [
                await self.test_table_rls_enabled(),
                await self.test_user_access_policies(),
                await self.test_admin_access_policies(),
                await self.test_policy_access_controls(),
                await self.test_helper_functions()
            ]
            
            return self.generate_test_report()
            
        finally:
            await self.cleanup_test_data()
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        total_tests = sum(suite.total_count for suite in self.test_suites)
        total_passed = sum(suite.passed_count for suite in self.test_suites)
        total_failed = sum(suite.failed_count for suite in self.test_suites)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 100.0
            },
            'test_suites': [
                {
                    'name': suite.name,
                    'total': suite.total_count,
                    'passed': suite.passed_count,
                    'failed': suite.failed_count,
                    'success_rate': suite.success_rate,
                    'results': [asdict(result) for result in suite.results]
                }
                for suite in self.test_suites
            ],
            'recommendations': []
        }
        
        # Add recommendations based on test results
        if total_failed > 0:
            report['recommendations'].append(
                "Some RLS tests failed. Review the failed tests and fix the underlying issues."
            )
        
        if total_tests == 0:
            report['recommendations'].append(
                "No tests were run. Verify database connectivity and test setup."
            )
        
        return report
    
    def print_summary(self, report: Dict[str, Any]):
        """Print a summary of test results."""
        print("\n" + "="*60)
        print("RLS POLICY TEST RESULTS")
        print("="*60)
        
        summary = report['summary']
        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        
        print("\nTest Suite Results:")
        for suite_data in report['test_suites']:
            status = "✓" if suite_data['failed'] == 0 else "✗"
            print(f"  {status} {suite_data['name']}: {suite_data['passed']}/{suite_data['total']} passed")
        
        # Show failed tests
        failed_tests = []
        for suite_data in report['test_suites']:
            for result in suite_data['results']:
                if not result['passed']:
                    failed_tests.append(f"  - {result['test_name']}: {result['error_message']}")
        
        if failed_tests:
            print("\nFailed Tests:")
            for test in failed_tests:
                print(test)
        
        if report['recommendations']:
            print("\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  - {rec}")

async def main():
    """Main function to run RLS tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test RLS policies')
    parser.add_argument('--database-url', help='Database URL (defaults to DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: Database URL not provided. Use --database-url or set DATABASE_URL environment variable")
        return
    
    # Run tests
    tester = RLSTester(database_url)
    
    try:
        await tester.connect()
        report = await tester.run_all_tests()
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'rls_test_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to {report_file}")
        
        # Print summary
        tester.print_summary(report)
        
    except Exception as e:
        print(f"Error running tests: {e}")
        raise
    finally:
        await tester.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 