import os
import re
import json
import pytest
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import warnings

def get_supabase_projects():
    """Get Supabase project information from CLI"""
    try:
        result = subprocess.run(['supabase', 'projects', 'list', '-o', 'json'], 
                              capture_output=True, text=True, check=True)
        projects = json.loads(result.stdout)
        
        # Create a dict of project info by name
        project_info = {}
        for project in projects:
            name = project['name']
            project_info[name] = {
                'id': project['id'],
                'db_host': project['database']['host'],
                'region': project['region']
            }
        return project_info
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        pytest.skip(f"Failed to get Supabase project info: {str(e)}")

def load_env_file(env_name: str) -> dict:
    """Load environment variables from a specific .env file"""
    env_path = Path('.') / env_name
    print(f"Loading environment file: {env_path}")
    if not env_path.exists():
        pytest.skip(f"Environment file {env_path} not found")
    
    load_dotenv(env_path)
    return dict(os.environ)

def is_env_var_reference(value: str) -> bool:
    """Check if a value is an environment variable reference like ${XXXXXX_API_KEY}"""
    return bool(re.match(r'^\${[A-Z][A-Z0-9_]+}$', value))

def validate_env_var_format(var_name: str, value: str, allow_ref: bool = True) -> bool:
    """Validate environment variable format and content"""
    if allow_ref and is_env_var_reference(value):
        # Valid environment variable reference
        return True
    
    if var_name.endswith('_API_KEY') or var_name.endswith('_KEY'):
        # Should be either a JWT token or env var reference
        return is_env_var_reference(value) or re.match(r'^ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$', value)
    
    if var_name.endswith('_URL'):
        # URL can be an env var reference or actual URL
        return is_env_var_reference(value) or re.match(r'^https?://', value)
    
    if var_name.endswith('_PASSWORD'):
        # Password can be an env var reference or actual password
        return is_env_var_reference(value) or len(value) >= 8
    
    return True

def load_base_env():
    """Load base environment variables from .env.base"""
    base_env_path = Path(__file__).parent.parent.parent / '.env.base'
    if not base_env_path.exists():
        raise FileNotFoundError(".env.base file not found. Please create it with base configuration.")
    
    # Load base environment
    load_dotenv(base_env_path)
    return dict(os.environ)

def get_base_api_keys():
    """Get API keys from base environment"""
    base_env = load_base_env()
    return {
        'anon_key': base_env.get('NEXT_PUBLIC_SUPABASE_ANON_KEY'),
        'service_role_key': base_env.get('SUPABASE_SERVICE_ROLE_KEY'),
        'jwt_secret': base_env.get('SUPABASE_JWT_SECRET')
    }

def check_supabase_urls(env_vars: dict, project_info: dict = None, is_local: bool = False):
    """Verify Supabase URLs and keys are present"""
    # Check required keys exist
    assert 'NEXT_PUBLIC_SUPABASE_ANON_KEY' in env_vars, "Missing NEXT_PUBLIC_SUPABASE_ANON_KEY"
    assert 'SUPABASE_SERVICE_ROLE_KEY' in env_vars, "Missing SUPABASE_SERVICE_ROLE_KEY"
    assert 'SUPABASE_URL' in env_vars, "Missing SUPABASE_URL"

    project_url = env_vars.get('SUPABASE_URL', '')
    # For hosted environments, verify against actual project
    project_id = project_url.split('//')[1].split('.')[0]

    if is_local:
        assert project_url == 'http://127.0.0.1:54321', \
            "Local Supabase URL should be http://127.0.0.1:54321"
        assert project_id == '127', \
            "Local Supabase URL should be 127"
    elif env_vars.get('NODE_ENV') == 'staging':
        assert project_id == project_info['insurance-navigator-staging']['id'], \
            f"Project URL {project_url} doesn't match the known staging project"
    elif env_vars.get('NODE_ENV') == 'production':
        assert project_id == project_info['insurance-navigator']['id'], \
            f"Project URL {project_url} doesn't match the known production project"

def check_database_urls(env_vars: dict, project_info: dict = None, is_local: bool = False):
    """Verify database URLs are present and match project"""
    print("\n=== Database URL Check Debug ===")
    print(f"is_local: {is_local}")
    print(f"project_info: {project_info}")
    print(f"SUPABASE_DATABASE_URL: {env_vars.get('SUPABASE_DATABASE_URL')}")
    print(f"SUPABASE_POOLER_URL: {env_vars.get('SUPABASE_POOLER_URL')}")
    print(f"SUPABASE_SESSION_POOLER_URL: {env_vars.get('SUPABASE_SESSION_POOLER_URL')}")
    print(f"SUPABASE_DB_HOST: {env_vars.get('SUPABASE_DB_HOST')}")
    
    # Check required URLs exist
    assert 'SUPABASE_DATABASE_URL' in env_vars, "Missing SUPABASE_DATABASE_URL"
    assert 'SUPABASE_POOLER_URL' in env_vars, "Missing SUPABASE_POOLER_URL"
    assert 'SUPABASE_SESSION_POOLER_URL' in env_vars, "Missing SUPABASE_SESSION_POOLER_URL"

    if is_local:
        print("Checking local development URLs...")
        # Local development URLs
        assert env_vars.get('SUPABASE_DATABASE_URL') == f'postgresql://postgres:postgres@127.0.0.1:54322/postgres', \
            "Local SUPABASE_DATABASE_URL should use port 54322"
        assert env_vars.get('SUPABASE_POOLER_URL') == f'postgresql://postgres:postgres@127.0.0.1:54321/postgres', \
            "Local pooler URL should use port 54321"
        assert env_vars.get('SUPABASE_SESSION_POOLER_URL') == f'postgresql://postgres:postgres@127.0.0.1:54321/postgres', \
            "Local session pooler URL should use port 54321"
    elif env_vars.get('NODE_ENV') == 'staging':
        # Get project info based on DB host
        db_host = env_vars.get('DB_HOST', '')
        assert project_info['insurance-navigator-staging']['db_host'] == db_host, f"DB host {db_host} doesn't match any known Supabase projects"
    elif env_vars.get('NODE_ENV') == 'production':
        db_host = env_vars.get('DB_HOST', '')
        assert project_info['insurance-navigator']['db_host'] == db_host, f"DB host {db_host} doesn't match any known Supabase projects"

def check_edge_function_compatibility(env_vars: dict, project_info: dict = None, is_local: bool = False):
    """Verify environment has required edge function configuration"""
    # Check required variables exist
    assert 'SUPABASE_JWT_SECRET' in env_vars, "Missing SUPABASE_JWT_SECRET"
    assert 'SUPABASE_SERVICE_ROLE_KEY' in env_vars, "Missing SUPABASE_SERVICE_ROLE_KEY"
    
    if not is_local and project_info:
        assert 'SUPABASE_POOLER_URL' in env_vars, "Edge functions require SUPABASE_POOLER_URL"

def test_development_environment():
    """Test development environment configuration"""
    env_vars = load_env_file('.env.development')
    
    # Verify development-specific values
    assert env_vars.get('SUPABASE_DB_HOST') == '127.0.0.1'
    assert env_vars.get('SUPABASE_DB_PORT') == '54322'
    assert env_vars.get('SUPABASE_DB_PASSWORD') == 'postgres'

    # Run standard checks
    check_supabase_urls(env_vars, is_local=True)
    check_database_urls(env_vars, is_local=True)
    check_edge_function_compatibility(env_vars, is_local=True)

def test_staging_environment():
    """Test staging environment configuration"""
    env_vars = load_env_file('.env.staging')
    projects = get_supabase_projects()
    
    # Get staging project info
    staging_project = projects.get('insurance-navigator-staging')
    assert staging_project, "Staging project not found in Supabase projects"
    
    # Check Supabase configuration against actual project
    check_supabase_urls(env_vars, projects)
    check_database_urls(env_vars, projects)
    check_edge_function_compatibility(env_vars, projects)
    
    # Verify staging-specific values match actual project
    assert env_vars.get('DB_PORT') == '5432'
    assert env_vars.get('NEXT_PUBLIC_SUPABASE_URL') == f"https://{staging_project['id']}.supabase.co", \
        "NEXT_PUBLIC_SUPABASE_URL doesn't match Supabase project"

def test_production_environment():
    """Test production environment configuration"""
    env_vars = load_env_file('.env.production')
    projects = get_supabase_projects()
    
    # Get production project info
    prod_project = projects.get('insurance-navigator')
    assert prod_project, "Production project not found in Supabase projects"
    
    # Check Supabase configuration against actual project
    check_supabase_urls(env_vars, projects)
    check_database_urls(env_vars, projects)
    check_edge_function_compatibility(env_vars, projects)
    
    # Verify production-specific values match actual project
    assert env_vars.get('NEXT_PUBLIC_SUPABASE_URL') == f"https://{prod_project['id']}.supabase.co", \
        "NEXT_PUBLIC_SUPABASE_URL doesn't match Supabase project"
    
    # Verify production security requirements
    db_password = env_vars.get('DB_PASSWORD', '')
    # Check password length
    if len(db_password) < 16:
        warnings.warn(f"Production database password should be at least 16 characters when it's {len(db_password)}", UserWarning)
    if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{16,}$', db_password):
        warnings.warn("Production password should contain uppercase, lowercase, numbers, and special characters", UserWarning)
    
    # Verify SSL is required
    #assert 'sslmode=require' in env_vars.get('DATABASE_URL', ''), "Production should require SSL"
    #assert 'sslmode=require' in env_vars.get('SUPABASE_POOLER_URL', ''), "Production pooler should require SSL" 