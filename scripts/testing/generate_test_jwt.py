#!/usr/bin/env python3
"""
JWT Token Generator for Testing Production Endpoints

This script generates valid JWT tokens using the service role key
to test the production API endpoints that require authentication.
"""

import jwt
import uuid
from datetime import datetime, timedelta
import json

def generate_test_jwt_token(
    user_id: str = None,
    email: str = "test@example.com",
    role: str = "user",
    supabase_url: str = "http://localhost:54321",  # Match docker-compose SUPABASE_URL
    service_role_key: str = "***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
) -> str:
    """
    Generate a valid JWT token for testing production endpoints.
    
    Args:
        user_id: User ID (UUID string). If None, generates a random one.
        email: User email address
        role: User role
        supabase_url: Supabase URL (issuer) - must match config
        service_role_key: Service role key for signing
        
    Returns:
        Valid JWT token string
    """
    
    # Generate user ID if not provided
    if user_id is None:
        user_id = str(uuid.uuid4())
    
    # Create payload with required claims that match auth.py validation
    payload = {
        "sub": user_id,                    # Subject (user ID) - required by auth.py
        "aud": "authenticated",            # Audience - required by auth.py
        "iss": supabase_url,               # Issuer - must match config.supabase_url
        "email": email,                    # User email - optional
        "role": role,                      # User role - optional
        "iat": datetime.utcnow(),          # Issued at
        "exp": datetime.utcnow() + timedelta(hours=24),  # Expires in 24 hours
        "nbf": datetime.utcnow()          # Not valid before
    }
    
    # Sign the token with the service role key
    token = jwt.encode(
        payload,
        service_role_key,
        algorithm="HS256"
    )
    
    return token

def generate_test_tokens():
    """Generate and display test JWT tokens."""
    
    print("🔐 JWT Token Generator for Production Endpoint Testing")
    print("=" * 60)
    
    # Use the exact values from docker-compose.yml
    docker_supabase_url = "http://localhost:54321"  # From docker-compose
    docker_service_role_key = "***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
    
    # Generate tokens for different test scenarios
    test_cases = [
        {
            "name": "Default Test User",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "test@example.com",
            "role": "user"
        },
        {
            "name": "Admin Test User", 
            "user_id": "987fcdeb-51a2-43d1-9f12-345678901234",
            "email": "admin@example.com",
            "role": "admin"
        },
        {
            "name": "Random User",
            "user_id": None,  # Will generate random UUID
            "email": "random@example.com",
            "role": "user"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        
        token = generate_test_jwt_token(
            user_id=test_case["user_id"],
            email=test_case["email"],
            role=test_case["role"],
            supabase_url=docker_supabase_url,
            service_role_key=docker_service_role_key
        )
        
        print(f"User ID: {test_case['user_id'] or 'Generated'}")
        print(f"Email: {test_case['email']}")
        print(f"Role: {test_case['role']}")
        print(f"JWT Token: {token}")
        
        # Decode and show payload for verification
        try:
            decoded = jwt.decode(
                token,
                docker_service_role_key,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=docker_supabase_url
            )
            print(f"✅ Token validation successful!")
            print(f"Token Payload: {json.dumps(decoded, indent=2, default=str)}")
        except Exception as e:
            print(f"❌ Token validation error: {e}")
    
    print("\n" + "=" * 60)
    print("📋 Usage Instructions:")
    print("1. Copy the JWT token from above")
    print("2. Use in Authorization header: 'Bearer <TOKEN>'")
    print("3. Test production endpoints with valid authentication")
    print("\nExample curl command:")
    print("curl -H 'Authorization: Bearer <TOKEN>' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"filename\": \"test.pdf\", ...}' \\")
    print("     http://localhost:8000/api/v2/upload")

if __name__ == "__main__":
    generate_test_tokens()
