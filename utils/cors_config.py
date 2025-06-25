"""
Centralized CORS Configuration for FastAPI
"""
from typing import Dict, Any
import os

def get_cors_config() -> Dict[str, Any]:
    """Get CORS configuration for FastAPI middleware."""
    
    # Base allowed origins - include both production and preview URLs
    allowed_origins = [
        "http://localhost:3000",
        "https://insurance-navigator.vercel.app",
        "https://insurance-navigator-7ehumqaks-andrew-quintanas-projects.vercel.app"
    ]
    
    # Add any additional origins from environment
    env_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    allowed_origins.extend([origin.strip() for origin in env_origins if origin.strip()])
    
    return {
        "allow_origins": allowed_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": [
            "Content-Type",
            "Accept",
            "Authorization",
            "Origin",
            "X-Requested-With",
            "x-client-info",
            "apikey",
            "x-user-id"
        ],
        "expose_headers": ["Content-Length", "Content-Range"],
        "max_age": 7200  # 2 hours
    }

def get_cors_headers(origin: str | None = None) -> Dict[str, str]:
    """Get CORS headers for a specific origin."""
    if not origin:
        return {}
        
    config = get_cors_config()
    
    # Check if origin is allowed
    if origin in config["allow_origins"] or "*" in config["allow_origins"]:
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