#!/usr/bin/env python3
"""
Test JWT authentication for upload pipeline.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jose import jwt, JWTError

# Test token from main API server
token = "***REMOVED***.eyJzdWIiOiI0MDg3OGE2YS0xNmUxLTRjMGYtODViZC00MWQ3OTE4NTY4MTciLCJlbWFpbCI6InRlc3RfdXNlckBleGFtcGxlLmNvbSIsImV4cCI6MTc1ODE0NjM5MiwiaWF0IjoxNzU4MDU5OTkyLCJpc3MiOiJpbnN1cmFuY2UtbmF2aWdhdG9yLW1pbmltYWwtYXV0aCIsImF1ZCI6Imluc3VyYW5jZS1uYXZpZ2F0b3ItdXNlcnMifQ.ynzZNwMtri3m2hN1j0IxHM34hL9B8PtFI9qp96YyPTI"

print("Testing JWT token validation...")

# Test 1: Decode without any verification
try:
    payload = jwt.decode(token, options={"verify_signature": False})
    print("✅ Decode without verification: SUCCESS")
    print(f"   Payload: {payload}")
except Exception as e:
    print(f"❌ Decode without verification: FAILED - {e}")

# Test 2: Decode with correct secret but no verification
try:
    payload = jwt.decode(token, "improved-minimal-dev-secret-key", algorithms=["HS256"], options={"verify_signature": False})
    print("✅ Decode with secret, no verification: SUCCESS")
    print(f"   Payload: {payload}")
except Exception as e:
    print(f"❌ Decode with secret, no verification: FAILED - {e}")

# Test 3: Decode with correct secret and minimal verification
try:
    payload = jwt.decode(token, "improved-minimal-dev-secret-key", algorithms=["HS256"], options={"verify_aud": False, "verify_iss": False})
    print("✅ Decode with secret, minimal verification: SUCCESS")
    print(f"   Payload: {payload}")
except Exception as e:
    print(f"❌ Decode with secret, minimal verification: FAILED - {e}")

# Test 4: Decode with correct secret and full verification
try:
    payload = jwt.decode(token, "improved-minimal-dev-secret-key", algorithms=["HS256"])
    print("✅ Decode with secret, full verification: SUCCESS")
    print(f"   Payload: {payload}")
except Exception as e:
    print(f"❌ Decode with secret, full verification: FAILED - {e}")

# Test 5: Try with different secret
try:
    payload = jwt.decode(token, "super-secret-jwt-token-with-at-least-32-characters-long", algorithms=["HS256"], options={"verify_signature": False})
    print("✅ Decode with env secret, no verification: SUCCESS")
    print(f"   Payload: {payload}")
except Exception as e:
    print(f"❌ Decode with env secret, no verification: FAILED - {e}")
