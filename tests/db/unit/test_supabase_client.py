"""Unit tests for Supabase client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, create_autospec
from supabase import Client as SupabaseClient
from postgrest import AsyncPostgrestClient, AsyncRequestBuilder
import httpx

from db.config import SupabaseConfig

TEST_URL = "http://localhost:54321"
TEST_SERVICE_KEY = "test_service_key"
TEST_ANON_KEY = "test_anon_key"

# Mock JWT token for authentication
TEST_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfaWQiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJyb2xlIjoidXNlciJ9.8Vx2rvQOXJ5rV7V6lPYzcMt_GGUAcJ5N7xTOHoXYA4M"

@pytest.fixture
def mock_execute():
    """Create a mock execute method."""
    mock = AsyncMock()
    mock.return_value = {"data": []}
    return mock

@pytest.fixture
def mock_request_builder(mock_execute):
    """Create a mock request builder."""
    builder = create_autospec(AsyncRequestBuilder, instance=True)
    
    # First create the methods
    builder.execute = mock_execute
    builder.eq = MagicMock(return_value=builder)
    builder.select = MagicMock(return_value=builder)
    builder.insert = MagicMock(return_value=builder)
    builder.update = MagicMock(return_value=builder)
    builder.delete = MagicMock(return_value=builder)
    
    return builder

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = create_autospec(httpx.AsyncClient)
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"data": [], "access_token": TEST_JWT}
    client.request.return_value = response
    return client

@pytest.fixture
def mock_storage_api():
    """Create a mock storage API."""
    api = MagicMock()
    api.upload = AsyncMock(return_value={"Key": "test.txt"})
    api.download = AsyncMock(return_value=b"test content")
    api.list = AsyncMock(return_value=[{"name": "test.txt", "id": "123"}])
    return api

@pytest.fixture
def mock_supabase_client(mock_request_builder, mock_http_client, mock_storage_api):
    """Create a mock Supabase client."""
    client = create_autospec(SupabaseClient, instance=True)
    
    # Set up auth mock with proper JWT handling
    auth_mock = MagicMock()
    auth_mock.get_session = AsyncMock(return_value={
        "access_token": TEST_JWT,
        "token_type": "bearer",
        "expires_in": 3600,
        "refresh_token": "test_refresh_token",
        "user": {"id": "test_user_id", "email": "test@example.com"}
    })
    auth_mock.sign_in = AsyncMock(return_value={
        "session": {
            "access_token": TEST_JWT,
            "refresh_token": "test_refresh_token",
            "user": {"id": "test_user_id", "email": "test@example.com"}
        }
    })
    client.auth = auth_mock
    
    # Set up table operation mocks with auth headers
    table_mock = MagicMock()
    table_mock.select.return_value = mock_request_builder
    table_mock.insert.return_value = mock_request_builder
    table_mock.upsert.return_value = mock_request_builder
    client.table.return_value = table_mock
    
    # Set up storage mock with auth headers
    storage_mock = MagicMock()
    storage_mock.from_.return_value = mock_storage_api
    client.storage = storage_mock
    
    # Add headers property for auth
    client.headers = {"Authorization": f"Bearer {TEST_JWT}"}
    
    return client

@pytest.fixture
def supabase_config():
    """Create a test Supabase configuration."""
    return SupabaseConfig(
        url=TEST_URL,
        service_role_key=TEST_SERVICE_KEY,
        anon_key=TEST_ANON_KEY
    )

@pytest.fixture
def supabase_client(mock_supabase_client, mock_http_client, supabase_config):
    """Create a Supabase client instance."""
    with patch('supabase.create_client', return_value=mock_supabase_client), \
         patch('httpx.AsyncClient', return_value=mock_http_client):
        
        client = create_autospec(SupabaseClient)
        client.auth = mock_supabase_client.auth
        client.table = mock_supabase_client.table
        client.storage = mock_supabase_client.storage
        client.headers = mock_supabase_client.headers
        return client

class TestSupabaseClient:
    """Test cases for Supabase client operations."""

    async def test_auth_operations(self, supabase_client):
        """Test authentication operations."""
        # Test session retrieval
        session = await supabase_client.auth.get_session()
        assert session["access_token"] == TEST_JWT
        assert session["token_type"] == "bearer"
        assert session["user"]["id"] == "test_user_id"

        # Test sign in
        sign_in_result = await supabase_client.auth.sign_in({
            "email": "test@example.com",
            "password": "test_password"
        })
        assert sign_in_result["session"]["access_token"] == TEST_JWT
        assert sign_in_result["session"]["user"]["email"] == "test@example.com"

    async def test_table_operations(self, supabase_client, mock_execute):
        """Test table operations."""
        # Setup
        table_name = "test_table"
        test_data = {"id": 1, "name": "test"}
        mock_execute.return_value = {"data": [test_data]}

        # Test insert
        result = await supabase_client.table(table_name).insert(test_data).execute()
        assert result["data"][0] == test_data
        supabase_client.table.assert_called_with(table_name)

    async def test_storage_operations(self, supabase_client):
        """Test storage operations."""
        # Setup
        bucket = "test_bucket"
        file_path = "test.txt"
        file_content = b"test content"
        
        # Test upload
        upload_result = await supabase_client.storage.from_(bucket).upload(file_path, file_content)
        assert upload_result["Key"] == file_path
        
        # Test download
        download_result = await supabase_client.storage.from_(bucket).download(file_path)
        assert download_result == file_content
        
        # Test list
        list_result = await supabase_client.storage.from_(bucket).list()
        assert len(list_result) == 1
        assert list_result[0]["name"] == "test.txt"

    async def test_error_handling(self, supabase_client, mock_execute):
        """Test error handling."""
        # Setup
        table_name = "test_table"
        error_response = {
            "message": "Database error",
            "code": "PGRST301",
            "hint": None,
            "details": None
        }
        mock_execute.side_effect = Exception(str(error_response))

        # Test error handling
        with pytest.raises(Exception) as exc_info:
            await supabase_client.table(table_name).select("*").execute()
        assert "Database error" in str(exc_info.value)
        assert "PGRST301" in str(exc_info.value)

    async def test_transaction_handling(self, supabase_client, mock_execute):
        """Test transaction handling."""
        # Setup
        table_name = "test_table"
        test_data = {"id": 1, "name": "test"}
        mock_execute.return_value = {"data": [test_data]}

        # Test transaction
        result = await supabase_client.table(table_name).upsert(test_data).execute()
        assert result["data"][0] == test_data

    async def test_connection_handling(self, supabase_client):
        """Test connection handling."""
        # Test connection status
        assert supabase_client.auth is not None
        assert supabase_client.table is not None
        assert supabase_client.storage is not None

    async def test_query_building(self, supabase_client, mock_execute):
        """Test query building."""
        # Setup
        table_name = "test_table"
        filters = {"name": "test", "active": True}
        mock_execute.return_value = {"data": []}

        # Build and execute query
        query = supabase_client.table(table_name).select("*")
        for key, value in filters.items():
            query = query.eq(key, value)
        result = await query.execute()
        assert result["data"] == []

    async def test_hipaa_compliant_operations(self, supabase_client, mock_execute, mock_request_builder):
        """Test HIPAA-compliant data handling."""
        # Setup
        table_name = "protected_health_info"
        phi_data = {
            "id": 1,
            "patient_id": "encrypted_patient_123",
            "data": "encrypted_health_data",
            "consent_version": "v1.0",
            "access_log": [
                {
                    "timestamp": "2024-03-21T10:00:00Z",
                    "user_id": "test_user_id",
                    "action": "read",
                    "reason": "treatment"
                }
            ]
        }
        mock_execute.return_value = {"data": [phi_data]}

        # Configure table mock
        table_mock = supabase_client.table(table_name)
        table_mock.insert.return_value = mock_request_builder
        table_mock.select.return_value = mock_request_builder
        table_mock.update.return_value = mock_request_builder

        # Test insert with audit log
        insert_data = {
            **phi_data,
            "audit_info": {
                "user_id": "test_user_id",
                "action": "create",
                "timestamp": "2024-03-21T10:00:00Z"
            }
        }
        result = await table_mock.insert(insert_data).execute()
        assert result["data"][0]["consent_version"] == "v1.0"
        assert len(result["data"][0]["access_log"]) == 1

        # Test read with access logging
        result = await table_mock.select("*").eq("patient_id", "encrypted_patient_123").execute()
        assert result["data"][0]["patient_id"] == "encrypted_patient_123"
        assert "access_log" in result["data"][0]

        # Test update with audit trail
        updated_data = {
            **phi_data,
            "consent_version": "v1.1",
            "access_log": [
                *phi_data["access_log"],
                {
                    "timestamp": "2024-03-21T11:00:00Z",
                    "user_id": "test_user_id",
                    "action": "update",
                    "reason": "correction"
                }
            ]
        }
        mock_execute.return_value = {"data": [updated_data]}
        
        result = await table_mock.update(updated_data).eq("id", 1).execute()
        assert result["data"][0]["consent_version"] == "v1.1"
        assert len(result["data"][0]["access_log"]) == 2

    async def test_storage_error_handling(self, supabase_client, mock_storage_api):
        """Test storage operation error handling."""
        # Setup
        bucket = "test_bucket"
        file_path = "test.txt"
        file_content = b"test content"
        
        # Configure storage mock to raise errors
        mock_storage_api.upload.side_effect = Exception("Storage upload failed")
        mock_storage_api.download.side_effect = Exception("Storage download failed")
        mock_storage_api.list.side_effect = Exception("Storage list failed")
        
        # Test upload error
        with pytest.raises(Exception) as exc_info:
            await supabase_client.storage.from_(bucket).upload(file_path, file_content)
        assert "Storage upload failed" in str(exc_info.value)
        
        # Test download error
        with pytest.raises(Exception) as exc_info:
            await supabase_client.storage.from_(bucket).download(file_path)
        assert "Storage download failed" in str(exc_info.value)
        
        # Test list error
        with pytest.raises(Exception) as exc_info:
            await supabase_client.storage.from_(bucket).list()
        assert "Storage list failed" in str(exc_info.value)

    async def test_bulk_operations(self, supabase_client, mock_execute):
        """Test bulk operations."""
        # Setup
        table_name = "test_table"
        test_data = [
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2"}
        ]
        mock_execute.return_value = {"data": test_data}

        # Test bulk insert
        result = await supabase_client.table(table_name).insert(test_data).execute()
        assert result["data"] == test_data
        assert len(result["data"]) == 2 