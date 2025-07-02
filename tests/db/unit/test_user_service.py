"""Unit tests for user service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from db.services.user_service import UserService

@pytest.fixture
def sample_user_data():
    """Create sample user data."""
    return {
        'id': str(uuid.uuid4()),
        'email': 'test@example.com',
        'name': 'Test User',
        'roles': ['user']
    }

@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    client = MagicMock()
    
    # Mock table operations
    table = MagicMock()
    table.select = MagicMock(return_value=table)
    table.insert = MagicMock(return_value=table)
    table.update = MagicMock(return_value=table)
    table.delete = MagicMock(return_value=table)
    table.eq = MagicMock(return_value=table)
    table.execute = AsyncMock()
    client.table = MagicMock(return_value=table)
    
    return client

@pytest.fixture
def user_service(mock_supabase):
    """Create a UserService instance with mocked dependencies."""
    service = UserService(mock_supabase)
    service.db = mock_supabase  # Ensure the service uses our mock
    return service

class TestUserService:
    """Test cases for the UserService class."""

    async def test_get_user_by_id(self, user_service, mock_supabase, sample_user_data):
        """Test getting a user by ID."""
        # Setup
        table = mock_supabase.table.return_value
        table.execute.return_value = {"data": [sample_user_data]}

        # Execute
        user = await user_service.get_user_by_id(sample_user_data['id'])

        # Verify
        assert user == sample_user_data
        mock_supabase.table.assert_called_with("users")
        table.select.assert_called_with("*")
        table.eq.assert_called_with("id", sample_user_data['id'])

    async def test_update_user(self, user_service, mock_supabase, sample_user_data):
        """Test updating a user."""
        # Setup
        update_data = {'name': 'Updated Name'}
        table = mock_supabase.table.return_value
        updated_user = {**sample_user_data, **update_data}
        table.execute.return_value = {"data": [updated_user]}

        # Execute
        updated_user = await user_service.update_user(sample_user_data['id'], update_data)

        # Verify
        assert updated_user['name'] == update_data['name']
        mock_supabase.table.assert_called_with("users")
        table.update.assert_called_with(update_data)
        table.eq.assert_called_with("id", sample_user_data['id'])

    async def test_delete_user(self, user_service, mock_supabase, sample_user_data):
        """Test deleting a user."""
        # Setup
        table = mock_supabase.table.return_value
        table.execute.return_value = {"data": [{"id": sample_user_data['id']}]}

        # Execute
        success = await user_service.delete_user(sample_user_data['id'])

        # Verify
        assert success is True
        mock_supabase.table.assert_called_with("users")
        table.delete.assert_called()
        table.eq.assert_called_with("id", sample_user_data['id'])

    async def test_search_users(self, user_service, mock_supabase):
        """Test searching users."""
        # Setup
        filters = {'email': 'test@example.com'}
        table = mock_supabase.table.return_value
        table.execute.side_effect = [
            {"data": [{"id": "1", "email": "test@example.com"}]},  # First call
            {"data": []},  # Second call (no results)
            {"data": [{"id": "1", "email": "test@example.com"}]}  # Third call
        ]

        # Test successful search
        users = await user_service.search_users(filters)
        assert len(users) == 1
        assert users[0]["email"] == filters["email"]

        # Test no results
        users = await user_service.search_users({'email': 'nonexistent@example.com'})
        assert len(users) == 0

        # Test error handling
        table.execute.side_effect = Exception("Database error")
        users = await user_service.search_users(filters)
        assert len(users) == 0

    async def test_get_user_roles(self, user_service, mock_supabase, sample_user_data):
        """Test getting user roles."""
        # Setup
        table = mock_supabase.table.return_value
        table.execute.return_value = {"data": [{"role": "admin"}, {"role": "user"}]}

        # Execute
        roles = await user_service.get_user_roles(sample_user_data['id'])

        # Verify
        assert len(roles) == 2
        assert "admin" in [r["role"] for r in roles]
        assert "user" in [r["role"] for r in roles]
        mock_supabase.table.assert_called_with("user_roles")
        table.select.assert_called_with("role")
        table.eq.assert_called_with("user_id", sample_user_data['id'])

    async def test_update_user_roles(self, user_service, mock_supabase, sample_user_data):
        """Test updating user roles."""
        # Setup
        new_roles = ["admin"]
        table = mock_supabase.table.return_value
        table.execute.return_value = {"data": [{"role": role} for role in new_roles]}

        # Execute
        success = await user_service.update_user_roles(sample_user_data['id'], new_roles, "add")

        # Verify
        assert success is True
        mock_supabase.table.assert_called_with("user_roles")
        table.delete.assert_called()
        table.eq.assert_called_with("user_id", sample_user_data['id'])
        table.insert.assert_called_with([{"user_id": sample_user_data['id'], "role": role} for role in new_roles]) 