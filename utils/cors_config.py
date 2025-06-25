"""
Simplified CORS Configuration following Supabase's approach
"""
from typing import Dict

def get_cors_headers() -> Dict[str, str]:
    """Get basic CORS headers following Supabase's pattern."""
    return {
        'Access-Control-Allow-Origin': '*',  # For MVP, we'll use * and handle credentials separately
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-user-id',
        'Access-Control-Max-Age': '7200'  # 2 hours
    }

def get_cors_headers_with_credentials(origin: str) -> Dict[str, str]:
    """Get CORS headers for endpoints that require credentials."""
    return {
        'Access-Control-Allow-Origin': origin,  # Must be specific origin when credentials are allowed
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-user-id',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Max-Age': '7200',  # 2 hours
        'Vary': 'Origin'  # Important for caching
    }