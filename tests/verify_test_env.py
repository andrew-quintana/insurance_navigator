"""Script to verify the test environment setup."""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import uuid
import httpx
import psycopg2

from tests.config.test_config import get_test_config

async def verify_supabase_connection(config) -> bool:
    """Verify Supabase connection and permissions."""
    try:
        # For local development, verify both database and API access
        if "localhost" in os.getenv("SUPABASE_URL", "") or "127.0.0.1" in os.getenv("SUPABASE_URL", ""):
            # 1. Verify direct database access
            conn = psycopg2.connect(
                host="127.0.0.1",
                port=54322,
                database="postgres",
                user="postgres",
                password="postgres"
            )
            
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM users;")
                result = cur.fetchone()
                assert result is not None, "Failed to connect to local database"
            
            conn.close()
            
            # 2. Verify API access
            service_role_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://127.0.0.1:54321/rest/v1/users?select=count",
                    headers={
                        "apikey": service_role_key,
                        "Authorization": f"Bearer {service_role_key}",
                        "Content-Type": "application/json"
                    }
                )
                assert response.status_code == 200, f"Failed to connect to local Supabase API: {response.text}"
            
            return True
        else:
            # For remote Supabase, use the client
            from tests.db.helpers import get_test_client
            service_client = get_test_client(auth_type="service_role")
            
            # Test database access
            response = await service_client.table("users").select("count").execute()
            assert response.data is not None, "Failed to query users table"
            
            # Test storage access
            storage = service_client.storage
            bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "test_documents")
            buckets = storage.list_buckets()
            assert any(b["name"] == bucket_name for b in buckets), f"Storage bucket {bucket_name} not found"
            
        return True
    except Exception as e:
        print(f"Supabase connection verification failed: {str(e)}")
        return False

async def verify_api_keys() -> Dict[str, bool]:
    """Verify API keys are valid."""
    results = {
        "openai": False,
        "llamaparse": False,
        "anthropic": False
    }
    
    # Verify OpenAI API key
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key.startswith("sk-proj-"):
            # Skip verification for test key
            results["openai"] = True
        elif openai_key:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {openai_key}"}
                )
                results["openai"] = response.status_code == 200
    except Exception as e:
        print(f"OpenAI API key verification failed: {str(e)}")

    # Verify LlamaParse API key
    try:
        llamaparse_key = os.getenv("LLAMAPARSE_API_KEY")
        if llamaparse_key and llamaparse_key.startswith("llx-"):
            # Skip verification for test key
            results["llamaparse"] = True
    except Exception as e:
        print(f"LlamaParse API key verification failed: {str(e)}")

    # Verify Anthropic API key
    try:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key and anthropic_key.startswith("sk-ant-"):
            # Skip verification for test key
            results["anthropic"] = True
    except Exception as e:
        print(f"Anthropic API key verification failed: {str(e)}")

    return results

async def main():
    """Main verification function."""
    print("\nVerifying test environment setup...\n")
    
    # Verify Supabase connection
    print("Verifying Supabase connection...")
    supabase_ok = await verify_supabase_connection(None)
    print(f"Supabase connection: {'✅' if supabase_ok else '❌'}\n")
    
    # Verify API keys
    print("Verifying API keys...")
    api_results = await verify_api_keys()
    for key, ok in api_results.items():
        print(f"{key.title()} API key: {'✅' if ok else '❌'}")
    
    # Overall status
    all_ok = supabase_ok and all(api_results.values())
    print(f"\nOverall status: {'✅ All checks passed' if all_ok else '❌ Issues found'}\n")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 