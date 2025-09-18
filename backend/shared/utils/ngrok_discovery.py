"""
Ngrok URL Discovery Utility

This module provides utilities to dynamically discover the current ngrok URL
at runtime, rather than relying on hardcoded values or environment variables
that might be stale.
"""

import os
import requests
import logging
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def get_ngrok_url() -> Optional[str]:
    """
    Dynamically discover the current ngrok URL by querying the ngrok API.
    
    Returns:
        str: The current ngrok HTTPS URL, or None if not available
    """
    try:
        # Try to get URL from ngrok API
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            for tunnel in data.get("tunnels", []):
                if tunnel.get("proto") == "https":
                    url = tunnel.get("public_url")
                    if url:
                        logger.info(f"Discovered ngrok URL: {url}")
                        return url
    except requests.RequestException as e:
        logger.debug(f"Failed to query ngrok API: {e}")
    
    # Fallback to environment variable
    ngrok_url = os.getenv("NGROK_URL")
    if ngrok_url:
        logger.info(f"Using ngrok URL from environment: {ngrok_url}")
        return ngrok_url
    
    logger.warning("No ngrok URL discovered")
    return None

def get_api_base_url() -> str:
    """
    Get the appropriate API base URL for the current environment.
    
    Returns:
        str: The API base URL (ngrok URL in dev, production URL in prod)
    """
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "development":
        # Try to get ngrok URL dynamically
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            return ngrok_url
        
        # Fallback to localhost
        logger.warning("Ngrok not available, falling back to localhost")
        return "http://localhost:8000"
    else:
        # Production environment
        return os.getenv("API_BASE_URL", "https://insurance-navigator.onrender.com")

def get_webhook_base_url() -> str:
    """
    Get the appropriate webhook base URL for the current environment.
    
    Returns:
        str: The webhook base URL (ngrok URL in dev, production URL in prod)
    """
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "development":
        # Try to get ngrok URL dynamically
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            return ngrok_url
        
        # Fallback to localhost
        logger.warning("Ngrok not available for webhooks, falling back to localhost")
        return "http://localhost:8000"
    else:
        # Production environment
        return os.getenv("WEBHOOK_BASE_URL", "https://insurance-navigator.onrender.com")

def is_ngrok_available() -> bool:
    """
    Check if ngrok is currently running and accessible.
    
    Returns:
        bool: True if ngrok is available, False otherwise
    """
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_ngrok_dashboard_url() -> str:
    """
    Get the ngrok dashboard URL for monitoring.
    
    Returns:
        str: The ngrok dashboard URL
    """
    return "http://localhost:4040"
