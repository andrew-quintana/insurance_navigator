# Security Configuration Guide

## Overview

The Insurance Navigator system uses a layered security configuration approach that prioritizes environment variables over configuration files for better security practices.

## Configuration Priority

The system follows this priority order (highest to lowest):

1. **Environment Variables** (`.env` file) - **RECOMMENDED for production**
2. **Configuration File** (`config/config.yaml`) - For default values
3. **Hardcoded Defaults** - Fallback values

## Security Environment Variables

### JWT Configuration

```bash
# Required for production - NEVER commit this to version control
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars-long

# Optional - defaults to HS256
JWT_ALGORITHM=HS256

# Optional - defaults to 30 minutes  
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Security Settings

```bash
# Input validation (default: true)
SECURITY_VALIDATE_INPUTS=true

# Output sanitization (default: true)
SECURITY_SANITIZE_OUTPUTS=true

# Maximum token limit (default: 4096)
SECURITY_MAX_TOKEN_LIMIT=4096
```

## Setup Instructions

### Development Environment

1. Copy the template:
   ```bash
   cp .env.template.updated .env
   ```

2. Update the `.env` file with your values:
   ```bash
   # Generate a secure JWT secret (32+ characters)
   JWT_SECRET_KEY=your-generated-secret-key-here
   ```

### Production Environment

1. **NEVER** commit `.env` files to version control
2. Set environment variables directly on your server/container
3. Use a secure key management system for secrets
4. Consider using different values per environment:

```bash
# Production values
JWT_SECRET_KEY=production-secret-key-256-bits-minimum
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# Development values  
JWT_SECRET_KEY=development-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Security Benefits

### ✅ Environment Variables (.env)
- **Never committed to version control**
- **Environment-specific configuration**
- **Secure secret management**
- **12-Factor App compliance**
- **Easy rotation of secrets**

### ❌ Configuration Files (config.yaml)
- Visible in version control
- Same values across environments
- Risk of accidental secret exposure
- Harder to manage secrets

## Migration from config.yaml

If you were previously using `config.yaml` for security settings:

1. Move sensitive values to `.env` file
2. Keep non-sensitive defaults in `config.yaml`
3. Update your deployment to use environment variables

### Before (❌ Less Secure)
```yaml
# config.yaml - committed to git
authentication:
  jwt:
    algorithm: "HS256"  
    access_token_expire_minutes: 30
```

### After (✅ More Secure)
```bash
# .env - NOT committed to git
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Security Warnings

The system will warn you when using default/fallback values:

```
🚨 SECURITY WARNING: Using default JWT secret key. 
Set JWT_SECRET_KEY environment variable for production!
```

## Best Practices

1. **Use strong JWT secrets** (256+ bits, random)
2. **Different secrets per environment**
3. **Regular secret rotation**
4. **Monitor for security warnings**
5. **Use proper secret management tools in production**

## Testing Configuration

Test your security configuration:

```python
from utils.security_config import get_security_config

config = get_security_config()
print(f"Algorithm: {config.jwt_algorithm}")
print(f"Token Expiry: {config.access_token_expire_minutes} minutes")
print(f"Validation: {config.validate_inputs}")
```

This approach ensures your security configuration follows industry best practices while maintaining flexibility for different deployment environments. 