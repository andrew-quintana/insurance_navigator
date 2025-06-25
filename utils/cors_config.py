"""
Centralized CORS Configuration for FastAPI
"""
from typing import Dict, Any
import os
import re

def get_cors_config() -> Dict[str, Any]:
    """Get CORS configuration for FastAPI middleware."""
    
    # Base allowed origins - include both production and preview URLs
    allowed_origins = [
        "http://localhost:3000",
        "https://insurance-navigator.vercel.app",
        "***REMOVED***",  # Add Render API
        "https://insurance-navigator-*.vercel.app",  # More permissive pattern for Vercel previews
        "https://*-andrew-quintanas-projects.vercel.app",  # Handle all user preview URLs
        # Specific preview URLs
        "https://insurance-navigator-hr7oebcu2-andrew-quintanas-projects.vercel.app",
        "https://insurance-navigator-gdievtrsx-andrew-quintanas-projects.vercel.app",
        "https://insurance-navigator-3u3iv7xq0-andrew-quintanas-projects.vercel.app",
        "https://insurance-navigator-ajzpmcvgz-andrew-quintanas-projects.vercel.app",
        "https://insurance-navigator-cwtwocttv-andrew-quintanas-projects.vercel.app",
        "https://insurance-navigator-kkedlaqxo-andrew-quintanas-projects.vercel.app"
    ]
    
    # Add any additional origins from environment
    env_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    allowed_origins.extend([origin.strip() for origin in env_origins if origin.strip()])
    
    return {
        "allow_origins": allowed_origins,
        "allow_origin_regex": r"https://insurance-navigator-[a-zA-Z0-9-]+-andrew-quintanas-projects\.vercel\.app",  # Updated regex
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
        "allow_headers": [
            "Content-Type",
            "Accept",
            "Authorization",
            "Origin",
            "X-Requested-With",
            "x-client-info",
            "apikey",
            "x-user-id",
            "DNT",
            "User-Agent",
            "If-Modified-Since",
            "Cache-Control",
            "Range",
            "Content-Length",
            "Content-Range"
        ],
        "expose_headers": ["Content-Length", "Content-Range"],
        "max_age": 7200  # 2 hours
    }

def get_cors_headers(origin: str | None = None) -> Dict[str, str]:
    """Get CORS headers for a specific origin."""
    if not origin:
        return {}
        
    config = get_cors_config()
    
    # Check if origin matches any allowed pattern
    is_allowed = False
    
    # First check exact matches
    if origin in config["allow_origins"]:
        is_allowed = True
    else:
        # Then check wildcards
        for allowed_origin in config["allow_origins"]:
            if '*' in allowed_origin:
                pattern = allowed_origin.replace('*', '.*').replace('.', '\.')
                if re.match(pattern, origin):
                    is_allowed = True
                    break
        
        # Finally check regex pattern
        if not is_allowed and "allow_origin_regex" in config:
            pattern = re.compile(config["allow_origin_regex"])
            is_allowed = bool(pattern.match(origin))
    
    if is_allowed:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": ", ".join(config["allow_methods"]),
            "Access-Control-Allow-Headers": ", ".join(config["allow_headers"]),
            "Access-Control-Expose-Headers": ", ".join(config["expose_headers"]),
            "Access-Control-Max-Age": str(config["max_age"]),
            "Vary": "Origin"
        }
    
    return {}