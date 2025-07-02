"""Validate Row Level Security (RLS) policies in the database."""
import asyncio
import logging
import sys
from datetime import datetime
import uuid
import json
import pytest
from typing import Dict, List
import asyncpg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RLSValidator:
    """Validator for Row Level Security policies."""

    def __init__(self, db_config: Dict[str, str]):
        """Initialize the validator."""
        self.db_config = db_config
        self.conn = None
        self.test_users = {}

    async def connect(self):
        """Connect to the database."""
        try:
            self.conn = await asyncpg.connect(**self.db_config)
            logger.info('Connected to database')
        except Exception as e:
            logger.error(f'Failed to connect to database: {str(e)}')
            sys.exit(1)

    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
            logger.info('Database connection closed')

    async def setup_test_users(self):
        """Set up test users with different roles."""
        logger.info('Setting up test users...')
        
        roles = ['regular_user', 'admin', 'support']
        
        for role in roles:
            user_id = str(uuid.uuid4())
            email = f'rls_test_{role}_{user_id[:8]}@example.com'
            
            # Create user
            await self.conn.execute('''
                INSERT INTO users (id, email, full_name, roles)
                VALUES ($1, $2, $3, $4)
            ''', user_id, email, f'RLS Test {role.title()}', [role])
            
            self.test_users[role] = {
                'id': user_id,
                'email': email
            }
        
        logger.info('Test users created')

    async def validate_users_table(self):
        """Validate RLS policies on users table."""
        logger.info('Validating users table RLS...')
        
        results = []
        
        # Test cases for users table
        test_cases = [
            {
                'name': 'Regular user can only view own profile',
                'role': 'regular_user',
                'query': 'SELECT * FROM users',
                'expected_count': 1
            },
            {
                'name': 'Regular user cannot modify other profiles',
                'role': 'regular_user',
                'query': '''
                    UPDATE users 
                    SET full_name = 'Hacked Name' 
                    WHERE id != $1
                    RETURNING id
                ''',
                'should_fail': True
            },
            {
                'name': 'Admin can view all users',
                'role': 'admin',
                'query': 'SELECT * FROM users',
                'min_count': len(self.test_users)
            },
            {
                'name': 'Support can view user profiles but not modify',
                'role': 'support',
                'query': 'SELECT * FROM users',
                'min_count': len(self.test_users)
            },
            {
                'name': 'Support cannot modify users',
                'role': 'support',
                'query': '''
                    UPDATE users 
                    SET full_name = 'Support Modified' 
                    WHERE id = $1
                    RETURNING id
                ''',
                'should_fail': True
            }
        ]
        
        for test in test_cases:
            try:
                # Set role for test
                user_id = self.test_users[test['role']]['id']
                await self.conn.execute(f"SET LOCAL ROLE {test['role']}")
                await self.conn.execute("SET LOCAL app.current_user_id = $1", user_id)
                
                if test.get('should_fail', False):
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await self.conn.fetch(test['query'], user_id)
                    results.append({
                        'test': test['name'],
                        'status': 'PASSED',
                        'details': 'Operation correctly denied'
                    })
                else:
                    rows = await self.conn.fetch(test['query'])
                    if 'expected_count' in test:
                        assert len(rows) == test['expected_count']
                    if 'min_count' in test:
                        assert len(rows) >= test['min_count']
                    results.append({
                        'test': test['name'],
                        'status': 'PASSED',
                        'details': f'Retrieved {len(rows)} rows'
                    })
                
            except Exception as e:
                results.append({
                    'test': test['name'],
                    'status': 'FAILED',
                    'details': str(e)
                })
            
            # Reset role
            await self.conn.execute("RESET ROLE")
            await self.conn.execute("RESET app.current_user_id")
        
        return results

    async def validate_documents_table(self):
        """Validate RLS policies on documents table."""
        logger.info('Validating documents table RLS...')
        
        results = []
        
        # Create test documents
        test_docs = []
        for role, user in self.test_users.items():
            doc_id = str(uuid.uuid4())
            await self.conn.execute('''
                INSERT INTO documents (
                    id, user_id, filename, content_type, status, 
                    storage_path, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''',
                doc_id,
                user['id'],
                f'test_doc_{role}.pdf',
                'application/pdf',
                'completed',
                f'documents/{user["id"]}/test.pdf',
                datetime.utcnow()
            )
            test_docs.append({
                'id': doc_id,
                'user_id': user['id'],
                'role': role
            })
        
        # Test cases for documents table
        test_cases = [
            {
                'name': 'Regular user can only view own documents',
                'role': 'regular_user',
                'query': 'SELECT * FROM documents',
                'expected_count': 1
            },
            {
                'name': 'Regular user cannot access other documents',
                'role': 'regular_user',
                'query': '''
                    SELECT * FROM documents 
                    WHERE user_id != $1
                ''',
                'expected_count': 0
            },
            {
                'name': 'Admin can view all documents',
                'role': 'admin',
                'query': 'SELECT * FROM documents',
                'min_count': len(test_docs)
            },
            {
                'name': 'Support can view but not modify documents',
                'role': 'support',
                'query': 'SELECT * FROM documents',
                'min_count': len(test_docs)
            },
            {
                'name': 'Support cannot delete documents',
                'role': 'support',
                'query': '''
                    DELETE FROM documents 
                    WHERE id = $1
                    RETURNING id
                ''',
                'should_fail': True
            }
        ]
        
        for test in test_cases:
            try:
                # Set role for test
                user_id = self.test_users[test['role']]['id']
                await self.conn.execute(f"SET LOCAL ROLE {test['role']}")
                await self.conn.execute("SET LOCAL app.current_user_id = $1", user_id)
                
                if test.get('should_fail', False):
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await self.conn.fetch(test['query'], test_docs[0]['id'])
                    results.append({
                        'test': test['name'],
                        'status': 'PASSED',
                        'details': 'Operation correctly denied'
                    })
                else:
                    rows = await self.conn.fetch(test['query'])
                    if 'expected_count' in test:
                        assert len(rows) == test['expected_count']
                    if 'min_count' in test:
                        assert len(rows) >= test['min_count']
                    results.append({
                        'test': test['name'],
                        'status': 'PASSED',
                        'details': f'Retrieved {len(rows)} rows'
                    })
                
            except Exception as e:
                results.append({
                    'test': test['name'],
                    'status': 'FAILED',
                    'details': str(e)
                })
            
            # Reset role
            await self.conn.execute("RESET ROLE")
            await self.conn.execute("RESET app.current_user_id")
        
        return results

    async def validate_conversations_table(self):
        """Validate RLS policies on conversations table."""
        logger.info('Validating conversations table RLS...')
        
        results = []
        
        # Create test conversations
        test_convos = []
        for role, user in self.test_users.items():
            convo_id = str(uuid.uuid4())
            await self.conn.execute('''
                INSERT INTO conversations (
                    id, user_id, created_at, title
                )
                VALUES ($1, $2, $3, $4)
            ''',
                convo_id,
                user['id'],
                datetime.utcnow(),
                f'Test Conversation for {role}'
            )
            test_convos.append({
                'id': convo_id,
                'user_id': user['id'],
                'role': role
            })
        
        # Test cases for conversations table
        test_cases = [
            {
                'name': 'Regular user can only view own conversations',
                'role': 'regular_user',
                'query': 'SELECT * FROM conversations',
                'expected_count': 1
            },
            {
                'name': 'Regular user cannot access other conversations',
                'role': 'regular_user',
                'query': '''
                    SELECT * FROM conversations 
                    WHERE user_id != $1
                ''',
                'expected_count': 0
            },
            {
                'name': 'Admin can view all conversations',
                'role': 'admin',
                'query': 'SELECT * FROM conversations',
                'min_count': len(test_convos)
            },
            {
                'name': 'Support can view conversations for support',
                'role': 'support',
                'query': 'SELECT * FROM conversations',
                'min_count': len(test_convos)
            },
            {
                'name': 'Support cannot delete conversations',
                'role': 'support',
                'query': '''
                    DELETE FROM conversations 
                    WHERE id = $1
                    RETURNING id
                ''',
                'should_fail': True
            }
        ]
        
        for test in test_cases:
            try:
                # Set role for test
                user_id = self.test_users[test['role']]['id']
                await self.conn.execute(f"SET LOCAL ROLE {test['role']}")
                await self.conn.execute("SET LOCAL app.current_user_id = $1", user_id)
                
                if test.get('should_fail', False):
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await self.conn.fetch(test['query'], test_convos[0]['id'])
                    results.append({
                        'test': test['name'],
                        'status': 'PASSED',
                        'details': 'Operation correctly denied'
                    })
                else:
                    rows = await self.conn.fetch(test['query'])
                    if 'expected_count' in test:
                        assert len(rows) == test['expected_count']
                    if 'min_count' in test:
                        assert len(rows) >= test['min_count']
                    results.append({
                        'test': test['name'],
                        'status': 'PASSED',
                        'details': f'Retrieved {len(rows)} rows'
                    })
                
            except Exception as e:
                results.append({
                    'test': test['name'],
                    'status': 'FAILED',
                    'details': str(e)
                })
            
            # Reset role
            await self.conn.execute("RESET ROLE")
            await self.conn.execute("RESET app.current_user_id")
        
        return results

    def generate_report(self, results: Dict[str, List[Dict]]):
        """Generate RLS validation report."""
        logger.info('Generating RLS validation report...')
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0
            },
            'results': results
        }
        
        # Calculate summary
        for table_results in results.values():
            for test in table_results:
                report['summary']['total_tests'] += 1
                if test['status'] == 'PASSED':
                    report['summary']['passed'] += 1
                else:
                    report['summary']['failed'] += 1
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'rls_validation_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f'Report saved to {report_file}')
        
        # Print summary
        logger.info('\nRLS Validation Summary:')
        logger.info('=' * 50)
        logger.info(f"Total Tests: {report['summary']['total_tests']}")
        logger.info(f"Passed: {report['summary']['passed']}")
        logger.info(f"Failed: {report['summary']['failed']}")
        
        return report['summary']['failed'] == 0

async def main():
    """Main execution function."""
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 54321,
        'user': 'postgres',
        'password': 'postgres',
        'database': 'postgres'
    }
    
    # Initialize validator
    validator = RLSValidator(db_config)
    
    try:
        # Run validation
        await validator.connect()
        await validator.setup_test_users()
        
        results = {
            'users_table': await validator.validate_users_table(),
            'documents_table': await validator.validate_documents_table(),
            'conversations_table': await validator.validate_conversations_table()
        }
        
        success = validator.generate_report(results)
        
        await validator.close()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f'RLS validation failed: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main()) 