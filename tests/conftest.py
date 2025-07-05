"""Test configuration with HIPAA-ready settings for MVP."""
import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv
import asyncio
from typing import AsyncGenerator, Generator, Dict, Any
import uuid
from datetime import datetime, timedelta

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def load_environment():
    """Load environment variables based on test environment."""
    # Priority order: .env.test > .env.local > .env
    env_files = [
        os.path.join(project_root, '.env.test'),
        os.path.join(project_root, '.env.local'),
        os.path.join(project_root, '.env')
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            print(f"Loaded environment from {env_file}")
            break
    else:
        print("Warning: No environment file found. Using default test configuration.")

# Load environment variables
load_environment()

# Import after environment is loaded
from db.services.user_service import UserService, get_user_service
from db.services.document_service import DocumentService, get_document_service
from db.services.storage_service import StorageService, get_storage_service
from db.services.transaction_service import TransactionService, get_transaction_service
from config.database import get_supabase_client
from db.config import SupabaseConfig, DatabaseConfig, get_base_test_config
from supabase import create_client, Client

# Import test configuration
from tests.config.test_config import get_base_test_config, TestConfig
from tests.db.helpers import get_test_client, cleanup_test_data

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def supabase_config() -> SupabaseConfig:
    """Create Supabase configuration with HIPAA-ready settings."""
    return SupabaseConfig(
        url=os.getenv("SUPABASE_TEST_URL", "http://127.0.0.1:54321"),
        service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        anon_key=os.getenv("SUPABASE_TEST_KEY"),
        jwt_secret=os.getenv("SUPABASE_JWT_SECRET"),
        encryption_key=os.getenv("SUPABASE_ENCRYPTION_KEY"),
        audit_logging=os.getenv("AUDIT_LOGGING_ENABLED", "true").lower() == "true",
        data_retention_days=int(os.getenv("DATA_RETENTION_DAYS", "365")),
        ssl_enforce=os.getenv("SSL_ENFORCE", "true").lower() == "true",
        network_restrictions=os.getenv("NETWORK_RESTRICTIONS", "true").lower() == "true",
        point_in_time_recovery=os.getenv("POINT_IN_TIME_RECOVERY", "true").lower() == "true"
    )

@pytest.fixture(scope="session")
def supabase_client() -> Client:
    """Create Supabase client for testing."""
    config = get_base_test_config()
    return config.get_client()

@pytest.fixture(scope="session")
def db_config(supabase_config: SupabaseConfig) -> DatabaseConfig:
    """Create database configuration with proper settings."""
    return DatabaseConfig(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "54322")),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        supabase=supabase_config,
        min_connections=1,
        max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "10"))
    )

@pytest.fixture
async def user_service(supabase_client):
    """Get a configured user service for testing."""
    service = await get_user_service()
    yield service

@pytest.fixture
async def document_service(supabase_client):
    """Get a configured document service for testing."""
    service = await get_document_service()
    yield service

@pytest.fixture
async def storage_service(supabase_client):
    """Get a configured storage service for testing."""
    service = await get_storage_service()
    yield service

@pytest.fixture
async def transaction_service(supabase_client):
    """Get a configured transaction service for testing."""
    service = await get_transaction_service()
    yield service

@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    """Test user data with HIPAA-compliant fields."""
    return {
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "secureTestPass123!",
        "consent_version": "1.0",
        "data_retention_accepted": True,
        "hipaa_acknowledgment": True
    }

@pytest.fixture
async def test_user(user_service, test_user_data):
    """Create a test user and clean up after test."""
    # Create test user
    user = await user_service.create_user(
        email=test_user_data["email"],
        password=test_user_data["password"],
        consent_version=test_user_data["consent_version"],
        consent_timestamp=datetime.utcnow().isoformat()
    )
    
    yield user
    
    # Cleanup: Delete test user
    if user:
        await user_service.delete_user(user["id"])

@pytest.fixture
def test_document_data() -> Dict[str, Any]:
    """Create test document data with audit fields."""
    return {
        "filename": "test_document.pdf",
        "content_type": "application/pdf",
        "encryption_enabled": os.getenv("STORAGE_ENCRYPTION_ENABLED", "true").lower() == "true",
        "audit_enabled": os.getenv("STORAGE_AUDIT_ENABLED", "true").lower() == "true",
        "metadata": {
            "uploaded_at": datetime.utcnow().isoformat(),
            "retention_period": int(os.getenv("DATA_RETENTION_DAYS", "365")),
            "encryption_version": "1.0",
            "access_history": []
        }
    }

@pytest.fixture
async def test_document(document_service, test_document_data, test_user):
    """Create a test document and clean up after test."""
    # Create test document
    document = await document_service.create_document(
        user_id=test_user["id"],
        name=test_document_data["filename"],
        content_type=test_document_data["content_type"],
        is_encrypted=test_document_data["encryption_enabled"]
    )
    
    yield document
    
    # Cleanup: Delete test document
    if document:
        await document_service.delete_document(document["id"])

@pytest.fixture(autouse=True)
def cleanup_test_data(supabase_client: Client):
    """Clean up test data after each test."""
    yield
    try:
        # Clean up test user
        supabase_client.auth.admin.delete_user(
            os.getenv("TEST_USER_EMAIL", "test@example.com")
        )
        # Clean up test documents
        supabase_client.storage.from_(os.getenv("STORAGE_BUCKET")).remove(["test_document.pdf"])
    except Exception:
        pass  # Ignore cleanup errors 

@pytest.fixture(scope="session", autouse=True)
def setup_test_env() -> None:
    """Set up test environment variables before any tests run."""
    test_env = {
        "NODE_ENV": "test",
        "SUPABASE_TEST_URL": "http://127.0.0.1:54321",
        "SUPABASE_TEST_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.OXBO4nlx4gE7qGF4e1-znHLBALmZtABh_Fd_Ai5-YNg",
        "SUPABASE_SERVICE_ROLE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
        "DOCUMENT_ENCRYPTION_KEY": "YourBase64EncodedKey==",  # For testing only
        "AUDIT_LOGGING_ENABLED": "false",  # Disable audit logging for tests
        "DB_HOST": "localhost",
        "DB_PORT": "54322",
        "DB_NAME": "postgres",
        "DB_USER": "postgres",
        "DB_PASSWORD": "postgres"
    }
    
    # Store original environment variables
    original_env = {key: os.environ.get(key) for key in test_env.keys()}
    original_jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")  # Store original JWT secret
    
    # Update environment with test values
    os.environ.update(test_env)
    
    # Ensure JWT secret is set and consistent
    if not os.environ.get("SUPABASE_JWT_SECRET"):
        if os.environ.get("JWT_SECRET"):
            os.environ["SUPABASE_JWT_SECRET"] = os.environ["JWT_SECRET"]
        else:
            # Generate a new JWT secret if none exists
            jwt_secret = os.environ.get("SUPABASE_JWT_SECRET") or os.urandom(32).hex()
            os.environ["SUPABASE_JWT_SECRET"] = jwt_secret
            os.environ["JWT_SECRET"] = jwt_secret
    
    yield
    
    # Restore original environment variables
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    
    # Restore original JWT secret
    if original_jwt_secret:
        os.environ["SUPABASE_JWT_SECRET"] = original_jwt_secret
    else:
        os.environ.pop("SUPABASE_JWT_SECRET", None)

@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Get test configuration."""
    return get_base_test_config() 