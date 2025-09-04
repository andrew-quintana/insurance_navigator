"""Environment test configuration."""
import os
import sys
from pathlib import Path
import pytest
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before and after each test."""
    # Store original environment
    original_env = dict(os.environ)
    
    # Clear environment variables before test
    for key in list(os.environ.keys()):
        if key.startswith(('SUPABASE_', 'NEXT_PUBLIC_SUPABASE_')):
            del os.environ[key]
    
    yield
    
    # Restore original environment after test
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def env_paths():
    """Get paths to environment files."""
    return {
        'development': os.path.join(project_root, '.env.development'),
        'staging': os.path.join(project_root, '.env.staging'),
        'production': os.path.join(project_root, '.env.production')
    }

@pytest.fixture
def load_test_env():
    """Fixture to load a specific environment file."""
    def _load_env(env_file: str):
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            return True
        return False
    return _load_env 