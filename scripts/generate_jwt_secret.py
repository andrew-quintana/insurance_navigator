#!/usr/bin/env python3
"""
Generate a secure JWT secret key for production use.
"""

import secrets
import base64
import os

def generate_jwt_secret():
    """Generate a cryptographically secure JWT secret."""
    # Generate 64 bytes of random data
    secret_bytes = secrets.token_bytes(64)
    
    # Encode as base64 for easy storage
    secret_b64 = base64.b64encode(secret_bytes).decode('utf-8')
    
    return secret_b64

def main():
    """Generate and display JWT secret."""
    secret = generate_jwt_secret()
    
    print("🔐 Generated JWT Secret Key:")
    print(f"JWT_SECRET_KEY={secret}")
    print()
    print("📋 Copy this value to your environment variables:")
    print(f"export JWT_SECRET_KEY='{secret}'")
    print()
    print("⚠️  Keep this secret secure and never commit it to version control!")

if __name__ == "__main__":
    main() 