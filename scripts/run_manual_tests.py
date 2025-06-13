#!/usr/bin/env python3
"""
Manual Testing Helper Script for Database Refactoring
Assists with common testing operations and validations
"""

import os
import sys
import asyncio
import json
import time
import requests
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
DATABASE_URL = os.getenv('DATABASE_URL')

class TestHelper:
    def __init__(self):
        self.token = None
        self.test_user_email = f"test_{int(time.time())}@example.com"
        
    def print_step(self, step_name, description=""):
        print(f"\n🧪 {step_name}")
        if description:
            print(f"   {description}")
        print("-" * 50)
    
    def print_result(self, test_name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"     {details}")
    
    # Database Testing
    def test_database_connection(self):
        """Test database connectivity and basic queries"""
        self.print_step("Database Connection Test")
        
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Test basic connectivity
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            self.print_result("Database Connection", result['test'] == 1)
            
            # Count current tables
            cursor.execute("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = cursor.fetchone()['table_count']
            self.print_result("Table Count", True, f"{table_count} tables found")
            
            # Check if policy_basics column exists (post-migration)
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents' AND column_name = 'policy_basics'
            """)
            policy_basics_exists = cursor.fetchone() is not None
            self.print_result("Policy Basics Column", policy_basics_exists, 
                            "Migration applied" if policy_basics_exists else "Pre-migration state")
            
            conn.close()
            return True
            
        except Exception as e:
            self.print_result("Database Connection", False, str(e))
            return False
    
    def test_migration_status(self):
        """Check migration-specific database changes"""
        self.print_step("Migration Status Check")
        
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check for new audit_logs table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'audit_logs'
                )
            """)
            audit_logs_exists = cursor.fetchone()['exists']
            self.print_result("Audit Logs Table", audit_logs_exists)
            
            # Check for document_vectors table (renamed from user_document_vectors)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'document_vectors'
                )
            """)
            doc_vectors_exists = cursor.fetchone()['exists']
            self.print_result("Document Vectors Table", doc_vectors_exists)
            
            # Check for dropped complex tables
            dropped_tables = [
                'processing_jobs', 'agent_states', 'workflow_execution_states',
                'conversation_workflow_states', 'policy_records'
            ]
            
            for table in dropped_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = %s
                    )
                """, (table,))
                table_exists = cursor.fetchone()['exists']
                self.print_result(f"Dropped Table: {table}", not table_exists, 
                                "Still exists (pre-migration)" if table_exists else "Successfully dropped")
            
            conn.close()
            return True
            
        except Exception as e:
            self.print_result("Migration Status", False, str(e))
            return False
    
    # API Testing
    def test_api_health(self):
        """Test API server health and basic endpoints"""
        self.print_step("API Health Check")
        
        try:
            # Health endpoint
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            self.print_result("Health Endpoint", response.status_code == 200, 
                            f"Status: {response.status_code}")
            
            # Root endpoint
            response = requests.get(f"{API_BASE_URL}/", timeout=10)
            self.print_result("Root Endpoint", response.status_code == 200)
            
            # Check if response contains refactoring info
            if response.status_code == 200:
                data = response.json()
                version = data.get('version', '')
                self.print_result("API Version", True, f"Version: {version}")
            
            return True
            
        except Exception as e:
            self.print_result("API Health", False, str(e))
            return False
    
    def test_user_registration(self):
        """Test user registration and authentication"""
        self.print_step("User Registration Test")
        
        try:
            # Register test user
            registration_data = {
                "email": self.test_user_email,
                "password": "testpassword123",
                "full_name": "Test User"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/register",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.print_result("User Registration", True, f"Token: {self.token[:20]}...")
                return True
            else:
                self.print_result("User Registration", False, 
                                f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_result("User Registration", False, str(e))
            return False
    
    def test_chat_functionality(self):
        """Test the simplified chat endpoint"""
        self.print_step("Chat Functionality Test")
        
        if not self.token:
            self.print_result("Chat Test", False, "No authentication token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            chat_data = {"message": "What insurance coverage do I have?"}
            
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json=chat_data,
                headers=headers,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.print_result("Chat Response", True, 
                                f"Response time: {response_time:.2f}s")
                self.print_result("Chat Content", 'text' in data, 
                                f"Response text length: {len(data.get('text', ''))}")
                
                # Check for workflow_type indicating simplified architecture
                workflow_type = data.get('workflow_type', '')
                self.print_result("Simplified Architecture", 
                                workflow_type == 'simplified_navigator',
                                f"Workflow: {workflow_type}")
                return True
            else:
                self.print_result("Chat Response", False, 
                                f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("Chat Functionality", False, str(e))
            return False
    
    def test_performance_targets(self):
        """Test if performance targets are being met"""
        self.print_step("Performance Testing")
        
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Test JSONB query performance (policy facts lookup)
            start_time = time.time()
            cursor.execute("""
                EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
                SELECT policy_basics FROM documents 
                WHERE policy_basics IS NOT NULL
                LIMIT 10
            """)
            result = cursor.fetchone()
            query_time = time.time() - start_time
            
            # Parse execution time from EXPLAIN ANALYZE
            explain_data = result[0][0]
            execution_time = explain_data.get('Execution Time', 0)
            
            self.print_result("JSONB Query Performance", 
                            execution_time < 50,  # 50ms target
                            f"Execution time: {execution_time:.2f}ms (target: <50ms)")
            
            # Test GIN index usage
            cursor.execute("""
                EXPLAIN (FORMAT JSON)
                SELECT * FROM documents 
                WHERE policy_basics @> '{"policy_type": "health"}'
            """)
            explain_result = cursor.fetchone()
            explain_text = json.dumps(explain_result[0], indent=2)
            index_used = "gin" in explain_text.lower()
            
            self.print_result("GIN Index Usage", index_used,
                            "Index scan detected" if index_used else "Full table scan")
            
            conn.close()
            return True
            
        except Exception as e:
            self.print_result("Performance Testing", False, str(e))
            return False
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        self.print_step("Cleanup Test Data")
        
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Remove test user if created
            cursor.execute("DELETE FROM users WHERE email = %s", (self.test_user_email,))
            deleted_users = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.print_result("Cleanup", True, f"Removed {deleted_users} test users")
            return True
            
        except Exception as e:
            self.print_result("Cleanup", False, str(e))
            return False

def main():
    """Run the manual testing helper"""
    print("🚀 Database Refactoring - Manual Testing Helper")
    print("=" * 60)
    
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    tester = TestHelper()
    results = []
    
    # Run all tests
    test_methods = [
        ('database_connection', tester.test_database_connection),
        ('migration_status', tester.test_migration_status),
        ('api_health', tester.test_api_health),
        ('user_registration', tester.test_user_registration),
        ('chat_functionality', tester.test_chat_functionality),
        ('performance_targets', tester.test_performance_targets),
    ]
    
    for test_name, test_method in test_methods:
        try:
            result = test_method()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ CRITICAL ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Cleanup
    tester.cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TESTING SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Database refactoring appears successful.")
    else:
        print("⚠️  Some tests failed. Please review and address issues.")
        sys.exit(1)

if __name__ == "__main__":
    main() 