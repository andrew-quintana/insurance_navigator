import pytest
from uuid import uuid4
from datetime import datetime
import json
from typing import Dict, Any
from unittest.mock import MagicMock, AsyncMock

from db.services.policy_operations import PolicyOperations
from db.services.encryption_service import EncryptionService
from db.services.policy_access_evaluator import PolicyAccessEvaluator
from db.services.access_logging_service import AccessLoggingService

class MockEncryptionService:
    async def encrypt_data(self, data: str) -> str:
        return f"encrypted_{data}"

    async def decrypt_data(self, encrypted_data: str) -> str:
        return encrypted_data.replace("encrypted_", "")

class MockDBSession:
    def __init__(self):
        self.policies = {}
        self.user_roles = {}
        self.rls_rules = {}
        self.policy_access_logs = {}

    async def find_one(self, query):
        policy_id = query.get('id')
        return self.policies.get(policy_id)

    async def insert_one(self, document):
        self.policies[document['id']] = document

    async def update_one(self, query, update):
        policy_id = query.get('id')
        if policy_id in self.policies:
            self.policies[policy_id].update(update.get('$set', {}))
            return type('Result', (), {'modified_count': 1})()
        return type('Result', (), {'modified_count': 0})()

    async def count_documents(self, query):
        return len([p for p in self.policies.values() if p['status'] == 'active'])

    async def find(self, query, projection=None):
        filtered_policies = [p for p in self.policies.values() if p['status'] == 'active']
        if projection and 'encrypted_data' in projection:
            for p in filtered_policies:
                p.pop('encrypted_data', None)
        return type('Cursor', (), {
            'skip': lambda x: type('Cursor', (), {
                'limit': lambda y: type('Cursor', (), {
                    'to_list': lambda length: filtered_policies[:length]
                })()
            })()
        })()

@pytest.fixture
def db_session():
    return MockDBSession()

@pytest.fixture
def encryption_service():
    return MockEncryptionService()

@pytest.fixture
def operations(db_session, encryption_service):
    return PolicyOperations(db_session, encryption_service)

@pytest.fixture
def sample_user_id():
    return str(uuid4())

@pytest.fixture
def admin_user_setup(db_session, sample_user_id):
    db_session.user_roles = {
        sample_user_id: {
            'roles': ['admin'],
            'permissions': ['read', 'write', 'delete', 'read_sensitive']
        }
    }
    return sample_user_id

@pytest.fixture
def reader_user_setup(db_session):
    user_id = str(uuid4())
    db_session.user_roles = {
        user_id: {
            'roles': ['reader'],
            'permissions': ['read']
        }
    }
    return user_id

@pytest.fixture
def sample_policy_data():
    return {
        'policy_number': 'POL123',
        'coverage_type': 'health',
        'ssn': '123-45-6789',
        'medical_info': {'conditions': ['condition1']},
        'financial_data': {'income': 50000}
    }

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.policies = AsyncMock()
    session.policy_access_logs = AsyncMock()
    return session

@pytest.fixture
def mock_encryption_service():
    """Create a mock encryption service."""
    service = MagicMock(spec=EncryptionService)
    service.encrypt_data = AsyncMock()
    service.decrypt_data = AsyncMock()
    return service

@pytest.fixture
def mock_access_evaluator(monkeypatch):
    """Create a mock access evaluator that always grants access."""
    evaluator = MagicMock(spec=PolicyAccessEvaluator)
    evaluator.has_access.return_value = True
    evaluator.get_rls_conditions = AsyncMock(return_value={})
    return evaluator

@pytest.fixture
def mock_access_logger():
    """Create a mock access logger."""
    logger = MagicMock(spec=AccessLoggingService)
    logger.log_access = AsyncMock()
    return logger

@pytest.fixture
def operations(mock_db_session, mock_encryption_service, mock_access_evaluator, mock_access_logger, monkeypatch):
    """Create PolicyOperations instance with mocked dependencies."""
    ops = PolicyOperations(mock_db_session, mock_encryption_service)
    monkeypatch.setattr(ops, 'access_evaluator', mock_access_evaluator)
    monkeypatch.setattr(ops, 'access_logger', mock_access_logger)
    return ops

class TestPolicyOperations:
    async def test_create_policy(self, operations, admin_user_setup, sample_policy_data):
        """Test creating a new policy with sensitive data."""
        result = await operations.create_policy(admin_user_setup, sample_policy_data)
        
        assert result['id'] is not None
        assert result['status'] == 'active'
        assert result['version'] == 1
        assert 'encrypted_data' not in result
        assert result['data']['policy_number'] == 'POL123'
        assert 'ssn' not in result['data']

    async def test_get_policy(self, operations, admin_user_setup, sample_policy_data):
        """Test retrieving a policy."""
        created = await operations.create_policy(admin_user_setup, sample_policy_data)
        result = await operations.get_policy(admin_user_setup, created['id'], include_sensitive=True)
        
        assert result['id'] == created['id']
        assert result['data']['policy_number'] == 'POL123'
        assert result['data']['ssn'] == '123-45-6789'

    async def test_get_policy_no_sensitive(self, operations, reader_user_setup, admin_user_setup, sample_policy_data):
        """Test retrieving a policy without sensitive data."""
        created = await operations.create_policy(admin_user_setup, sample_policy_data)
        result = await operations.get_policy(reader_user_setup, created['id'])
        
        assert result['id'] == created['id']
        assert result['data']['policy_number'] == 'POL123'
        assert 'ssn' not in result['data']

    async def test_update_policy(self, operations, admin_user_setup, sample_policy_data):
        """Test updating a policy."""
        created = await operations.create_policy(admin_user_setup, sample_policy_data)
        updates = {
            'policy_number': 'POL124',
            'ssn': '987-65-4321'
        }
        result = await operations.update_policy(admin_user_setup, created['id'], updates)
        
        assert result['data']['policy_number'] == 'POL124'
        assert result['version'] == 2

    async def test_delete_policy(self, operations, admin_user_setup, sample_policy_data):
        """Test deleting a policy."""
        created = await operations.create_policy(admin_user_setup, sample_policy_data)
        result = await operations.delete_policy(admin_user_setup, created['id'])
        
        assert result is True
        deleted_policy = await operations.get_policy(admin_user_setup, created['id'])
        assert deleted_policy['status'] == 'deleted'

    async def test_list_policies(self, operations, admin_user_setup, sample_policy_data):
        """Test listing policies with pagination."""
        # Create multiple policies
        for _ in range(3):
            await operations.create_policy(admin_user_setup, sample_policy_data)

        result = await operations.list_policies(admin_user_setup, page=1, page_size=2)
        
        assert len(result['items']) == 2
        assert result['total'] == 3
        assert result['total_pages'] == 2

    async def test_unauthorized_access(self, operations, reader_user_setup, sample_policy_data):
        """Test unauthorized access attempts."""
        with pytest.raises(PermissionError):
            await operations.create_policy(reader_user_setup, sample_policy_data)

    async def test_invalid_policy_access(self, operations, admin_user_setup):
        """Test accessing non-existent policy."""
        with pytest.raises(ValueError):
            await operations.get_policy(admin_user_setup, str(uuid4()))

    async def test_sensitive_data_handling(self, operations, admin_user_setup, sample_policy_data):
        """Test proper handling of sensitive data."""
        created = await operations.create_policy(admin_user_setup, sample_policy_data)
        
        # Verify sensitive data is not in regular response
        assert 'ssn' not in created['data']
        assert 'medical_info' not in created['data']
        assert 'financial_data' not in created['data']
        
        # Verify sensitive data is accessible with proper permissions
        full_policy = await operations.get_policy(admin_user_setup, created['id'], include_sensitive=True)
        assert full_policy['data']['ssn'] == '123-45-6789'
        assert 'conditions' in full_policy['data']['medical_info']

@pytest.mark.asyncio
async def test_create_policy(operations, mock_db_session, mock_access_logger, sample_policy_data):
    """Test policy creation with access logging."""
    # Setup
    policy_id = str(uuid4())
    user_id = str(uuid4())
    mock_db_session.policies.insert_one = AsyncMock()
    
    # Execute
    result = await operations.create_policy(user_id, sample_policy_data.copy())
    
    # Verify
    assert result['status'] == 'active'
    assert result['version'] == 1
    mock_db_session.policies.insert_one.assert_called_once()
    
    # Verify access logging
    mock_access_logger.log_access.assert_called_once_with(
        policy_id=result['id'],
        user_id=user_id,
        action='create',
        actor_type='user',
        actor_id=user_id,
        purpose='policy_creation',
        metadata={'version': 1}
    )

@pytest.mark.asyncio
async def test_get_policy(operations, mock_db_session, mock_access_logger):
    """Test policy retrieval with access logging."""
    # Setup
    policy_id = str(uuid4())
    user_id = str(uuid4())
    mock_policy = {
        'id': policy_id,
        'data': {'policy_number': 'POL123'},
        'encrypted_data': 'encrypted',
        'version': 1
    }
    mock_db_session.policies.find_one = AsyncMock(return_value=mock_policy)
    
    # Execute
    result = await operations.get_policy(user_id, policy_id)
    
    # Verify
    assert result['id'] == policy_id
    mock_db_session.policies.find_one.assert_called_once()
    
    # Verify access logging
    mock_access_logger.log_access.assert_called_once_with(
        policy_id=policy_id,
        user_id=user_id,
        action='read',
        actor_type='user',
        actor_id=user_id,
        purpose='policy_view',
        metadata={'include_sensitive': False}
    )

@pytest.mark.asyncio
async def test_update_policy(operations, mock_db_session, mock_access_logger):
    """Test policy update with access logging."""
    # Setup
    policy_id = str(uuid4())
    user_id = str(uuid4())
    existing_policy = {
        'id': policy_id,
        'data': {'policy_number': 'POL123'},
        'encrypted_data': 'encrypted',
        'version': 1,
        'metadata': {}
    }
    mock_db_session.policies.find_one = AsyncMock(return_value=existing_policy)
    mock_db_session.policies.update_one = AsyncMock()
    
    updates = {'coverage_type': 'dental', 'ssn': '987-65-4321'}
    
    # Execute
    await operations.update_policy(user_id, policy_id, updates)
    
    # Verify database operations
    mock_db_session.policies.find_one.assert_called_once()
    mock_db_session.policies.update_one.assert_called_once()
    
    # Verify access logging
    mock_access_logger.log_access.assert_called_with(
        policy_id=policy_id,
        user_id=user_id,
        action='update',
        actor_type='user',
        actor_id=user_id,
        purpose='policy_update',
        metadata={
            'version': 2,
            'has_sensitive_updates': True
        }
    )

@pytest.mark.asyncio
async def test_delete_policy(operations, mock_db_session, mock_access_logger):
    """Test policy deletion with access logging."""
    # Setup
    policy_id = str(uuid4())
    user_id = str(uuid4())
    mock_db_session.policies.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    
    # Execute
    result = await operations.delete_policy(user_id, policy_id)
    
    # Verify
    assert result is True
    mock_db_session.policies.update_one.assert_called_once()
    
    # Verify access logging
    mock_access_logger.log_access.assert_called_once_with(
        policy_id=policy_id,
        user_id=user_id,
        action='delete',
        actor_type='user',
        actor_id=user_id,
        purpose='policy_deletion',
        metadata={'soft_delete': True}
    )

@pytest.mark.asyncio
async def test_list_policies(operations, mock_db_session, mock_access_logger):
    """Test policy listing with access logging."""
    # Setup
    user_id = str(uuid4())
    mock_policies = [{'id': str(uuid4()), 'data': {'policy_number': f'POL{i}'}} for i in range(3)]
    mock_db_session.policies.count_documents = AsyncMock(return_value=3)
    mock_db_session.policies.find = MagicMock()
    mock_db_session.policies.find.return_value.skip = MagicMock()
    mock_db_session.policies.find.return_value.skip.return_value.limit = MagicMock()
    mock_db_session.policies.find.return_value.skip.return_value.limit.return_value.to_list = AsyncMock(
        return_value=mock_policies
    )
    
    filters = {'coverage_type': 'health'}
    
    # Execute
    result = await operations.list_policies(user_id, filters=filters, page=1, page_size=10)
    
    # Verify
    assert len(result['items']) == 3
    assert result['total'] == 3
    mock_db_session.policies.count_documents.assert_called_once()
    
    # Verify access logging
    mock_access_logger.log_access.assert_called_once_with(
        policy_id=None,
        user_id=user_id,
        action='list',
        actor_type='user',
        actor_id=user_id,
        purpose='policy_list',
        metadata={
            'filters': filters,
            'page': 1,
            'page_size': 10,
            'total_results': 3
        }
    )

@pytest.mark.asyncio
async def test_access_denied(operations, mock_access_evaluator, mock_access_logger):
    """Test access denial handling."""
    # Setup
    mock_access_evaluator.has_access.return_value = False
    user_id = str(uuid4())
    policy_id = str(uuid4())
    
    # Verify create access denied
    with pytest.raises(PermissionError):
        await operations.create_policy(user_id, {})
    mock_access_logger.log_access.assert_not_called()
    
    # Verify read access denied
    with pytest.raises(PermissionError):
        await operations.get_policy(user_id, policy_id)
    mock_access_logger.log_access.assert_not_called()
    
    # Verify update access denied
    with pytest.raises(PermissionError):
        await operations.update_policy(user_id, policy_id, {})
    mock_access_logger.log_access.assert_not_called()
    
    # Verify delete access denied
    with pytest.raises(PermissionError):
        await operations.delete_policy(user_id, policy_id)
    mock_access_logger.log_access.assert_not_called() 