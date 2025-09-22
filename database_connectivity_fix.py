#!/usr/bin/env python3
"""
Database Connectivity Fix

This script implements fixes for the database connectivity issues
identified in the production environment.

Key findings:
1. DNS resolution issues with basic socket connections
2. asyncpg handles DNS resolution differently and works
3. Need to ensure proper DNS resolution in production environment
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_environment_configurations():
    """Create standardized environment configurations for all environments."""
    
    configs = {
        'production': {
            'name': 'Production',
            'supabase_url': 'https://znvwzkdblknkkztqyfnu.supabase.co',
            'database_host': 'db.znvwzkdblknkkztqyfnu.supabase.co',
            'database_port': 5432,
            'database_name': 'postgres',
            'database_user': 'postgres',
            'database_password': 'beqhar-qincyg-Syxxi8',
            'ssl_mode': 'require',
            'connection_timeout': 30,
            'command_timeout': 30,
            'pool_min_size': 5,
            'pool_max_size': 20
        },
        'staging': {
            'name': 'Staging',
            'supabase_url': 'https://dfgzeastcxnoqshgyotp.supabase.co',
            'database_host': 'db.dfgzeastcxnoqshgyotp.supabase.co',
            'database_port': 5432,
            'database_name': 'postgres',
            'database_user': 'postgres',
            'database_password': 'ERaZFjCEnuJsliSQ',
            'ssl_mode': 'require',
            'connection_timeout': 30,
            'command_timeout': 30,
            'pool_min_size': 5,
            'pool_max_size': 20
        },
        'development': {
            'name': 'Development',
            'supabase_url': 'http://localhost:54321',
            'database_host': 'localhost',
            'database_port': 5432,
            'database_name': 'postgres',
            'database_user': 'postgres',
            'database_password': 'postgres',
            'ssl_mode': 'prefer',
            'connection_timeout': 30,
            'command_timeout': 30,
            'pool_min_size': 2,
            'pool_max_size': 10
        }
    }
    
    return configs

def generate_connection_strings(config: Dict[str, Any]) -> Dict[str, str]:
    """Generate various connection string formats for a configuration."""
    
    base_conn = f"postgresql://{config['database_user']}:{config['database_password']}@{config['database_host']}:{config['database_port']}/{config['database_name']}"
    
    return {
        'basic': base_conn,
        'with_ssl': f"{base_conn}?sslmode={config['ssl_mode']}",
        'with_timeout': f"{base_conn}?sslmode={config['ssl_mode']}&connect_timeout={config['connection_timeout']}",
        'with_command_timeout': f"{base_conn}?sslmode={config['ssl_mode']}&connect_timeout={config['connection_timeout']}&command_timeout={config['command_timeout']}",
        'with_pool_params': f"{base_conn}?sslmode={config['ssl_mode']}&connect_timeout={config['connection_timeout']}&command_timeout={config['command_timeout']}&min_size={config['pool_min_size']}&max_size={config['pool_max_size']}"
    }

def generate_environment_variables(config: Dict[str, Any]) -> Dict[str, str]:
    """Generate environment variables for a configuration."""
    
    return {
        'ENVIRONMENT': config['name'].lower(),
        'NODE_ENV': config['name'].lower(),
        'SUPABASE_URL': config['supabase_url'],
        'SUPABASE_ANON_KEY': 'your_anon_key_here',  # Placeholder
        'SUPABASE_SERVICE_ROLE_KEY': 'your_service_role_key_here',  # Placeholder
        'DATABASE_URL': generate_connection_strings(config)['with_command_timeout'],
        'SUPABASE_DATABASE_URL': generate_connection_strings(config)['with_command_timeout'],
        'DB_HOST': config['database_host'],
        'DB_PORT': str(config['database_port']),
        'DB_NAME': config['database_name'],
        'DB_USER': config['database_user'],
        'DB_PASSWORD': config['database_password'],
        'DB_SSL_MODE': config['ssl_mode'],
        'DB_SSLMODE': config['ssl_mode'],
        'PGSSLMODE': config['ssl_mode'],
        'DB_CONNECTION_TIMEOUT': str(config['connection_timeout']),
        'DB_COMMAND_TIMEOUT': str(config['command_timeout']),
        'DB_POOL_MIN_SIZE': str(config['pool_min_size']),
        'DB_POOL_MAX_SIZE': str(config['pool_max_size'])
    }

def create_database_config_fix():
    """Create a fix for the database configuration issues."""
    
    fix_content = '''
# Database Configuration Fix
# This file contains fixes for database connectivity issues

import os
import asyncpg
from typing import Optional, Dict, Any

class DatabaseConfigFix:
    """Fixed database configuration with proper error handling."""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration with proper fallbacks."""
        
        # Get environment-specific configuration
        if self.environment == "production":
            return {
                'host': os.getenv('DB_HOST', 'db.znvwzkdblknkkztqyfnu.supabase.co'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'database': os.getenv('DB_NAME', 'postgres'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'beqhar-qincyg-Syxxi8'),
                'ssl': os.getenv('DB_SSL_MODE', 'require'),
                'command_timeout': int(os.getenv('DB_COMMAND_TIMEOUT', '30')),
                'min_size': int(os.getenv('DB_POOL_MIN_SIZE', '5')),
                'max_size': int(os.getenv('DB_POOL_MAX_SIZE', '20'))
            }
        elif self.environment == "staging":
            return {
                'host': os.getenv('DB_HOST', 'db.dfgzeastcxnoqshgyotp.supabase.co'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'database': os.getenv('DB_NAME', 'postgres'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'ERaZFjCEnuJsliSQ'),
                'ssl': os.getenv('DB_SSL_MODE', 'require'),
                'command_timeout': int(os.getenv('DB_COMMAND_TIMEOUT', '30')),
                'min_size': int(os.getenv('DB_POOL_MIN_SIZE', '5')),
                'max_size': int(os.getenv('DB_POOL_MAX_SIZE', '20'))
            }
        else:  # development
            return {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'database': os.getenv('DB_NAME', 'postgres'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'postgres'),
                'ssl': os.getenv('DB_SSL_MODE', 'prefer'),
                'command_timeout': int(os.getenv('DB_COMMAND_TIMEOUT', '30')),
                'min_size': int(os.getenv('DB_POOL_MIN_SIZE', '2')),
                'max_size': int(os.getenv('DB_POOL_MAX_SIZE', '10'))
            }
    
    async def create_connection_pool(self) -> asyncpg.Pool:
        """Create database connection pool with proper error handling."""
        
        try:
            # Try connection string first
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                return await asyncpg.create_pool(
                    database_url,
                    min_size=self.config['min_size'],
                    max_size=self.config['max_size'],
                    command_timeout=self.config['command_timeout'],
                    statement_cache_size=0,  # Fix pgbouncer prepared statement issue
                    setup=self._setup_connection
                )
            
            # Fallback to individual parameters
            return await asyncpg.create_pool(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                ssl=self.config['ssl'],
                min_size=self.config['min_size'],
                max_size=self.config['max_size'],
                command_timeout=self.config['command_timeout'],
                statement_cache_size=0,
                setup=self._setup_connection
            )
            
        except Exception as e:
            raise Exception(f"Failed to create database connection pool: {e}")
    
    async def _setup_connection(self, conn):
        """Setup connection with proper configuration."""
        # Add any connection setup logic here
        pass

# Usage example:
# config_fix = DatabaseConfigFix(environment="production")
# pool = await config_fix.create_connection_pool()
'''
    
    return fix_content

def main():
    """Main function to generate configuration fixes."""
    
    print("🔧 DATABASE CONNECTIVITY FIX GENERATOR")
    print("=" * 60)
    
    # Generate configurations for all environments
    configs = create_environment_configurations()
    
    print("\n📋 GENERATED CONFIGURATIONS:")
    print("-" * 40)
    
    for env_name, config in configs.items():
        print(f"\n{config['name']} Environment:")
        print(f"  Host: {config['database_host']}")
        print(f"  Port: {config['database_port']}")
        print(f"  Database: {config['database_name']}")
        print(f"  SSL Mode: {config['ssl_mode']}")
        
        # Generate connection strings
        conn_strings = generate_connection_strings(config)
        print(f"  Connection String: {conn_strings['with_command_timeout']}")
        
        # Generate environment variables
        env_vars = generate_environment_variables(config)
        print(f"  Environment Variables: {len(env_vars)} variables")
    
    # Create database config fix file
    fix_content = create_database_config_fix()
    
    with open('database_config_fix.py', 'w') as f:
        f.write(fix_content)
    
    print(f"\n📁 Database configuration fix saved to: database_config_fix.py")
    
    # Create environment-specific configuration files
    for env_name, config in configs.items():
        env_vars = generate_environment_variables(config)
        
        filename = f'.env.{env_name}.generated'
        with open(filename, 'w') as f:
            f.write(f"# Generated configuration for {config['name']} environment\n")
            f.write(f"# Generated on: {__import__('datetime').datetime.now()}\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        print(f"📁 {config['name']} environment variables saved to: {filename}")
    
    print("\n✅ Configuration generation complete!")
    print("\n📋 NEXT STEPS:")
    print("1. Review the generated configurations")
    print("2. Update Render environment variables with the production config")
    print("3. Test the database connectivity")
    print("4. Deploy the fixes to production")

if __name__ == "__main__":
    main()
