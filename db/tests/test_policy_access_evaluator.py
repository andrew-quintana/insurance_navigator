import pytest
from uuid import uuid4
from typing import Dict, Any
from db.services.policy_access_evaluator import PolicyAccessEvaluator

class MockDBSession:
    def __init__(self, user_roles: Dict[str, Any] = None):
        self.user_roles = user_roles or {}
        self.policies = {}
        self.rls_rules = {}

@pytest.fixture
def db_session():
    return MockDBSession()

@pytest.fixture
def evaluator(db_session):
    return PolicyAccessEvaluator(db_session)

@pytest.fixture
def sample_user_id():
    return str(uuid4())

@pytest.fixture
def sample_resource_id():
    return str(uuid4())

@pytest.fixture
def admin_user_roles(sample_user_id):
    return {
        sample_user_id: {
            'roles': ['admin'],
            'permissions': ['read', 'write', 'delete']
        }
    }

@pytest.fixture
def reader_user_roles(sample_user_id):
    return {
        sample_user_id: {
            'roles': ['reader'],
            'permissions': ['read']
        }
    }

class TestPolicyAccessEvaluator:
    def test_get_user_roles(self, evaluator, sample_user_id, admin_user_roles):
        """Test retrieving user roles."""
        evaluator.db.user_roles = admin_user_roles
        roles = evaluator.get_user_roles(sample_user_id)
        assert 'admin' in roles
        assert len(roles) == 1

    def test_has_access_admin_user(self, evaluator, sample_user_id, sample_resource_id, admin_user_roles):
        """Test that admin users have full access."""
        evaluator.db.user_roles = admin_user_roles
        assert evaluator.has_access(sample_user_id, sample_resource_id, 'read')
        assert evaluator.has_access(sample_user_id, sample_resource_id, 'write')
        assert evaluator.has_access(sample_user_id, sample_resource_id, 'delete')

    def test_has_access_reader_user(self, evaluator, sample_user_id, sample_resource_id, reader_user_roles):
        """Test that reader users have limited access."""
        evaluator.db.user_roles = reader_user_roles
        assert evaluator.has_access(sample_user_id, sample_resource_id, 'read')
        assert not evaluator.has_access(sample_user_id, sample_resource_id, 'write')
        assert not evaluator.has_access(sample_user_id, sample_resource_id, 'delete')

    def test_evaluate_policy_conditions(self, evaluator, sample_user_id, sample_resource_id):
        """Test policy condition evaluation."""
        context = {'ip_address': '192.168.1.1', 'time': '2024-03-20T10:00:00Z'}
        assert evaluator.evaluate_policy_conditions(
            sample_user_id,
            sample_resource_id,
            'read',
            context
        )

    def test_rls_check(self, evaluator, sample_user_id, sample_resource_id):
        """Test RLS integration."""
        evaluator.db.rls_rules = {
            sample_resource_id: {
                'allowed_users': [sample_user_id]
            }
        }
        assert evaluator.rls_check(sample_user_id, sample_resource_id)

    def test_has_access_with_context(self, evaluator, sample_user_id, sample_resource_id, reader_user_roles):
        """Test access check with additional context."""
        evaluator.db.user_roles = reader_user_roles
        context = {
            'ip_address': '192.168.1.1',
            'time': '2024-03-20T10:00:00Z',
            'request_metadata': {'source': 'internal'}
        }
        assert evaluator.has_access(
            sample_user_id,
            sample_resource_id,
            'read',
            context
        )

    def test_invalid_user_access(self, evaluator, sample_resource_id):
        """Test access for non-existent user."""
        invalid_user_id = str(uuid4())
        assert not evaluator.has_access(invalid_user_id, sample_resource_id, 'read')

    def test_invalid_resource_access(self, evaluator, sample_user_id, admin_user_roles):
        """Test access for non-existent resource."""
        evaluator.db.user_roles = admin_user_roles
        invalid_resource_id = str(uuid4())
        assert not evaluator.has_access(sample_user_id, invalid_resource_id, 'read') 