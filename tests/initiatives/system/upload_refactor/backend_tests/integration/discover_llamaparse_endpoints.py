"""
Discover LlamaParse API Endpoints

This script tests various endpoint patterns to find the correct LlamaParse API structure.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_env_file(env_file_path):
    """Load environment variables from a .env file."""
    logger.info(f"Loading environment from: {env_file_path}")
    
    if not os.path.exists(env_file_path):
        logger.error(f"Environment file not found: {env_file_path}")
        return False
    
    try:
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    os.environ[key] = value
        
        logger.info("Environment variables loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error loading environment file: {e}")
        return False

async def discover_endpoints():
    """Discover LlamaParse API endpoints by testing various patterns."""
    logger.info("Starting LlamaParse API endpoint discovery...")
    
    try:
        import httpx
        
        api_key = os.getenv('LLAMAPARSE_API_KEY')
        base_url = os.getenv('LLAMAPARSE_BASE_URL', 'https://api.cloud.llamaindex.ai')
        
        if not api_key:
            logger.error("LLAMAPARSE_API_KEY not found in environment")
            return
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Test various endpoint patterns
        test_patterns = [
            # Standard REST patterns
            "/api/v1/status",
            "/api/v1/health", 
            "/api/v1/models",
            "/api/v1/parse",
            "/api/v1/documents",
            "/api/v1/jobs",
            
            # Alternative patterns
            "/v1/status",
            "/v1/health",
            "/v1/models", 
            "/v1/parse",
            "/v1/documents",
            "/v1/jobs",
            
            # Root level patterns
            "/status",
            "/health",
            "/models",
            "/parse",
            "/documents",
            "/jobs",
            
            # LlamaParse specific patterns
            "/llamaparse/v1/status",
            "/llamaparse/v1/parse",
            "/llamaparse/status",
            "/llamaparse/parse",
            
            # Cloud patterns
            "/cloud/v1/status",
            "/cloud/v1/parse",
            "/cloud/status",
            "/cloud/parse",
            
            # Alternative base URLs
            "https://api.llamaindex.ai/v1/status",
            "https://api.llamaindex.ai/v1/parse",
            "https://llamaparse.ai/api/v1/status",
            "https://llamaparse.ai/api/v1/parse",
        ]
        
        results = {}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for pattern in test_patterns:
                try:
                    if pattern.startswith('http'):
                        url = pattern
                    else:
                        url = f"{base_url}{pattern}"
                    
                    logger.info(f"Testing: {url}")
                    
                    # Try GET first, then POST for parse endpoints
                    if 'parse' in pattern.lower():
                        try:
                            response = await client.post(url, headers=headers, json={"test": "endpoint_discovery"})
                            method = "POST"
                        except:
                            response = await client.get(url, headers=headers)
                            method = "GET"
                    else:
                        response = await client.get(url, headers=headers)
                        method = "GET"
                    
                    logger.info(f"  {method} {response.status_code}")
                    
                    # Check if we got a meaningful response
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            logger.info(f"  Response: {json.dumps(response_data, indent=2)[:200]}...")
                        except:
                            logger.info(f"  Response: {response.text[:200]}...")
                    elif response.status_code in [401, 403]:
                        logger.info(f"  Authentication required - endpoint exists!")
                    elif response.status_code == 404:
                        logger.info(f"  Endpoint not found")
                    else:
                        logger.info(f"  Status: {response.status_code}")
                    
                    results[pattern] = {
                        "url": url,
                        "method": method,
                        "status_code": response.status_code,
                        "exists": response.status_code in [200, 401, 403, 422, 400],
                        "response_preview": response.text[:200] if response.status_code != 404 else None
                    }
                    
                except Exception as e:
                    logger.warning(f"  Error testing {pattern}: {e}")
                    results[pattern] = {
                        "url": pattern if not pattern.startswith('http') else f"{base_url}{pattern}",
                        "method": "N/A",
                        "status_code": "error",
                        "exists": False,
                        "error": str(e)
                    }
        
        # Find working endpoints
        working_endpoints = [pattern for pattern, result in results.items() if result.get("exists")]
        logger.info(f"\nWorking endpoints found: {len(working_endpoints)}")
        for endpoint in working_endpoints:
            logger.info(f"  ✅ {endpoint}")
        
        # Save results
        results_file = f"llamaparse_endpoint_discovery_{int(asyncio.get_event_loop().time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\nResults saved to: {results_file}")
        
        return {
            "working_endpoints": working_endpoints,
            "total_tested": len(test_patterns),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Endpoint discovery failed: {e}")
        return {"error": str(e)}

async def main():
    """Main function."""
    logger.info("Starting LlamaParse API endpoint discovery")
    
    # Load environment
    env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '.env.development')
    if not load_env_file(env_file_path):
        logger.error("Failed to load environment variables")
        return
    
    results = await discover_endpoints()
    
    if results:
        print("\n" + "=" * 60)
        print("LLAMAPARSE API ENDPOINT DISCOVERY RESULTS")
        print("=" * 60)
        print(f"Working endpoints: {len(results.get('working_endpoints', []))}")
        print(f"Total tested: {results.get('total_tested', 0)}")
        
        if results.get('working_endpoints'):
            print("\nWorking endpoints:")
            for endpoint in results['working_endpoints']:
                print(f"  ✅ {endpoint}")
        else:
            print("\n❌ No working endpoints found")
            print("This suggests the API structure is different than expected")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
