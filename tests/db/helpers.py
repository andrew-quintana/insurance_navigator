"""
Helper functions for database testing and verification.
"""

import os
import json
import logging
from typing import Dict, Optional, Tuple, List, Any
import requests
from supabase import Client, create_client
import psycopg2
from psycopg2.extensions import connection as PgConnection
from tests.config.test_config import get_base_test_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseVerificationError(Exception):
    """Custom exception for Supabase verification errors."""
    pass

def verify_supabase_connection(
    url: Optional[str] = None,
    anon_key: Optional[str] = None,
    service_role_key: Optional[str] = None,
    db_password: Optional[str] = None
) -> Tuple[bool, Dict[str, bool], str]:
    """
    Comprehensive verification of Supabase connection including both API and direct database access.
    
    Args:
        url: Supabase project URL
        anon_key: Supabase anon key
        service_role_key: Supabase service role key
        db_password: Database password for direct connection
    
    Returns:
        Tuple containing:
        - Overall success status (bool)
        - Detailed status dict for each component
        - Detailed message string
        
    Raises:
        SupabaseVerificationError: If verification fails due to invalid credentials or configuration
    """
    logger.info("Starting Supabase connection verification")
    logger.info(f"URL: {url}")
    logger.info(f"Anon key: {'*' * len(anon_key) if anon_key else None}")
    logger.info(f"Service role key: {'*' * len(service_role_key) if service_role_key else None}")
    
    # Initialize result tracking
    status = {
        "env_vars_present": False,
        "url_valid": False,
        "api_anon_access": False,
        "api_service_access": False,
        "db_direct_access": False
    }
    messages = []
    
    try:
        # 1. Verify environment variables and input validation
        # Check both standard and test-specific environment variables
        url = url or os.getenv("SUPABASE_TEST_URL") or os.getenv("SUPABASE_URL")
        anon_key = anon_key or os.getenv("SUPABASE_TEST_KEY") or os.getenv("SUPABASE_ANON_KEY")
        service_role_key = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        db_password = db_password or os.getenv("DB_PASSWORD", "postgres")
        
        logger.info("After environment variable resolution:")
        logger.info(f"URL: {url}")
        logger.info(f"Anon key: {'*' * len(anon_key) if anon_key else None}")
        logger.info(f"Service role key: {'*' * len(service_role_key) if service_role_key else None}")
        
        # Validate required parameters
        if not all([url, anon_key, service_role_key]):
            error_msg = "Missing required parameters. URL, anon key, and service role key are required."
            logger.error(error_msg)
            raise SupabaseVerificationError(error_msg)
            
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            error_msg = f"Invalid URL format: {url}"
            logger.error(error_msg)
            raise SupabaseVerificationError(error_msg)
            
        # Validate key formats (basic check)
        if len(anon_key) < 8 or len(service_role_key) < 8:
            error_msg = "Invalid key format: keys must be at least 8 characters long"
            logger.error(error_msg)
            raise SupabaseVerificationError(error_msg)
            
        status["env_vars_present"] = True
        messages.append("✓ Environment variables present")
        
        # 2. Verify URL accessibility
        try:
            logger.info(f"Testing URL accessibility: {url}")
            # Simple health check
            response = requests.get(f"{url}/rest/v1/", 
                                 headers={"apikey": anon_key},
                                 timeout=5)
            logger.info(f"URL health check response status: {response.status_code}")
            # Accept both 404 (standard) and 200 (more permissive) responses
            if response.status_code in (404, 200):
                status["url_valid"] = True
                messages.append("✓ Supabase URL is accessible")
            else:
                error_msg = f"Supabase URL returned unexpected status code: {response.status_code}"
                logger.error(error_msg)
                raise SupabaseVerificationError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to access Supabase URL: {str(e)}"
            logger.error(error_msg)
            raise SupabaseVerificationError(error_msg)
        
        # 3. Test anonymous API access
        try:
            logger.info("Testing anonymous API access")
            supabase_anon = create_client(url, anon_key)
            # Try a simple query that should work with anon key
            result = supabase_anon.table("users").select("count").execute()
            status["api_anon_access"] = True
            messages.append("✓ Anonymous API access working")
        except Exception as e:
            error_msg = f"Anonymous API access failed: {str(e)}"
            logger.error(error_msg)
            raise SupabaseVerificationError(error_msg)
        
        # 4. Test service role API access
        try:
            logger.info("Testing service role API access")
            supabase_admin = create_client(url, service_role_key)
            # Try an admin-only operation
            result = supabase_admin.table("users").select("*").execute()
            status["api_service_access"] = True
            messages.append("✓ Service role API access working")
        except Exception as e:
            error_msg = f"Service role API access failed: {str(e)}"
            logger.error(error_msg)
            raise SupabaseVerificationError(error_msg)
        
        # 5. Test direct database connection
        try:
            logger.info("Testing direct database connection")
            # Parse connection details from URL
            if "localhost" in url or "127.0.0.1" in url:
                host = "localhost"
                port = 54321  # Default local Supabase PostgreSQL port
            else:
                # For production/staging, extract host from URL
                host = url.split("//")[1].split(".")[0]
                port = 5432  # Default PostgreSQL port
                
            logger.info(f"Connecting to database at {host}:{port}")
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password=db_password,
                host=host,
                port=port
            )
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
            conn.close()
            status["db_direct_access"] = True
            messages.append("✓ Direct database connection working")
        except Exception as e:
            error_msg = f"Direct database connection failed: {str(e)}"
            logger.error(error_msg)
            raise SupabaseVerificationError(error_msg)
            
        # Generate detailed report
        success = all(status.values())
        if success:
            messages.append("\n✓ All verification checks passed!")
        else:
            failed = [k for k, v in status.items() if not v]
            messages.append(f"\n! Some checks failed: {', '.join(failed)}")
            
        return success, status, "\n".join(messages)
        
    except SupabaseVerificationError:
        # Re-raise SupabaseVerificationError without wrapping
        raise
    except Exception as e:
        # Wrap other exceptions in SupabaseVerificationError
        error_msg = f"Verification failed with error: {str(e)}"
        logger.error(error_msg)
        raise SupabaseVerificationError(error_msg)

def get_supabase_client(
    url: Optional[str] = None,
    key: Optional[str] = None,
    use_service_role: bool = False
) -> Client:
    """
    Get a configured Supabase client with proper error handling.
    
    Args:
        url: Supabase project URL
        key: Supabase key (anon or service role)
        use_service_role: Whether to use service role key instead of anon key
        
    Returns:
        Configured Supabase client
        
    Raises:
        ValueError: If required parameters are missing
        SupabaseVerificationError: If client creation fails or parameters are invalid
    """
    logger.info("Creating Supabase client")
    
    try:
        # Get configuration
        config = get_base_test_config().supabase
        
        # Use provided values or fall back to config
        url = url or config.url
        if use_service_role:
            key = key or config.service_role_key
        else:
            key = key or config.anon_key
            
        logger.info(f"URL: {url}")
        logger.info(f"Key: {'*' * len(key) if key else None}")
        logger.info(f"Use service role: {use_service_role}")
    
        if not url or not key:
            error_msg = (
                "Missing required configuration. Ensure SUPABASE_TEST_URL/SUPABASE_URL and "
                f"{'SUPABASE_SERVICE_ROLE_KEY' if use_service_role else 'SUPABASE_TEST_KEY/SUPABASE_ANON_KEY'} "
                "are set."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            error_msg = f"Invalid URL format: {url}"
            logger.error(error_msg)
            raise SupabaseVerificationError(error_msg)
            
        # Validate key format (basic check)
        if len(key) < 8:
            error_msg = "Invalid key format: key must be at least 8 characters long"
            logger.error(error_msg)
            raise SupabaseVerificationError(error_msg)
            
        # Validate URL accessibility
        try:
            logger.info(f"Testing URL accessibility: {url}")
            response = requests.get(f"{url}/rest/v1/", 
                                 headers={"apikey": key},
                                 timeout=5)
            logger.info(f"URL health check response status: {response.status_code}")
            if response.status_code not in (404, 200):
                error_msg = f"Supabase URL returned unexpected status code: {response.status_code}"
                logger.error(error_msg)
                raise SupabaseVerificationError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to access Supabase URL: {str(e)}"
            logger.error(error_msg)
            raise SupabaseVerificationError(error_msg)
            
        return create_client(url, key)
    except Exception as e:
        if isinstance(e, SupabaseVerificationError):
            raise
        error_msg = f"Failed to create Supabase client: {str(e)}"
        logger.error(error_msg)
        raise SupabaseVerificationError(error_msg)

async def cleanup_test_data(client: Client, test_data: Dict[str, List[str]]) -> None:
    """Clean up test data after tests while preserving audit logs."""
    try:
        # Clean up users
        if test_data.get("user_ids"):
            await client.table("users").delete().in_("id", test_data["user_ids"]).execute()
        
        # Clean up documents
        if test_data.get("document_ids"):
            await client.table("documents").delete().in_("id", test_data["document_ids"]).execute()
            
            # Clean up associated encryption keys
            await client.table("encryption_keys").delete().in_("document_id", test_data["document_ids"]).execute()
        
        # Clean up storage
        if test_data.get("storage_paths"):
            for path in test_data["storage_paths"]:
                try:
                    await client.storage.from_("documents").remove([path])
                except Exception:
                    pass  # Ignore storage cleanup errors
                    
        # Note: We intentionally preserve audit_logs for compliance verification
        
    except Exception as e:
        print(f"Warning: Error during test cleanup: {str(e)}")
        # Don't raise the error to avoid affecting test results

async def create_test_user(client: Client, test_data: Dict[str, List[str]], **user_data) -> Dict:
    """Create a test user and track for cleanup."""
    try:
        response = await client.auth.sign_up({
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        user_id = response.user.id
        test_data["user_ids"].append(user_id)
        
        # Add additional user data if provided
        if additional_data := {k: v for k, v in user_data.items() if k not in ["email", "password"]}:
            await client.table("users").update(additional_data).eq("id", user_id).execute()
        
        return response.user
    except Exception as e:
        print(f"Warning: Error creating test user: {str(e)}")
        raise

async def create_test_document(client: Client, test_data: Dict[str, List[str]], **doc_data) -> Dict:
    """Create a test document and track for cleanup."""
    try:
        response = await client.table("documents").insert(doc_data).execute()
        document = response.data[0]
        
        test_data["document_ids"].append(document["id"])
        if storage_path := doc_data.get("storage_path"):
            test_data["storage_paths"].append(storage_path)
        
        return document
    except Exception as e:
        print(f"Warning: Error creating test document: {str(e)}")
        raise

async def upload_test_file(client: Client, test_data: Dict[str, List[str]], bucket: str, file_path: str, content: bytes) -> str:
    """Upload a test file to storage and track for cleanup."""
    try:
        await client.storage.from_(bucket).upload(file_path, content)
        test_data["storage_paths"].append(file_path)
        return file_path
    except Exception as e:
        print(f"Warning: Error uploading test file: {str(e)}")
        raise

def get_test_client(use_service_role: bool = False) -> Client:
    """
    Get a configured Supabase client for testing.
    
    Args:
        use_service_role: Whether to use service role key instead of anon key
        
    Returns:
        Configured Supabase test client
    """
    try:
        # Get configuration
        config = get_base_test_config().supabase
        
        # Use service role key if requested
        key = config.service_role_key if use_service_role else config.anon_key
        
        # Create client with appropriate key
        client = get_supabase_client(
            url=config.url,
            key=key,
            use_service_role=use_service_role
        )
        
        # For service role, set auth header on the postgrest client
        if use_service_role:
            # Set service role headers
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "X-Client-Info": "supabase-py/0.0.1",
                "Content-Type": "application/json"
            }
            
            # Set headers for all clients
            client.postgrest.headers.update(headers)
            client.auth.session = {"access_token": key}
            
            # Set additional options
            client.postgrest.auth(key)
            client.postgrest.schema("public")
            
            # Set role header
            client.postgrest.headers["X-Supabase-Role"] = "service_role"
        
        return client
    except Exception as e:
        raise Exception(f"Failed to create Supabase client: {str(e)}")
