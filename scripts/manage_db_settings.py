#!/usr/bin/env python3
"""
Database Settings Management Script
Handles configuration of database settings across different environments
"""
import os
import sys
import json
import argparse
from typing import Dict, Any
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_db_connection(env: str) -> psycopg2.extensions.connection:
    """Get database connection for the specified environment."""
    # Load environment-specific connection details
    connection_params = {
        'development': {
            'dbname': 'postgres',
            'user': 'postgres',
            'password': 'postgres',
            'host': 'localhost',
            'port': '54322'  # Updated port for local Supabase
        },
        'staging': {
            'dbname': os.getenv('STAGING_DB_NAME', 'postgres'),
            'user': os.getenv('STAGING_DB_USER', 'postgres'),
            'password': os.getenv('STAGING_DB_PASSWORD', ''),
            'host': os.getenv('STAGING_DB_HOST', ''),
            'port': os.getenv('STAGING_DB_PORT', '5432')
        },
        'production': {
            'dbname': os.getenv('PROD_DB_NAME', 'postgres'),
            'user': os.getenv('PROD_DB_USER', 'postgres'),
            'password': os.getenv('PROD_DB_PASSWORD', ''),
            'host': os.getenv('PROD_DB_HOST', ''),
            'port': os.getenv('PROD_DB_PORT', '5432')
        }
    }
    
    params = connection_params.get(env)
    if not params:
        raise ValueError(f"Unknown environment: {env}")
    
    return psycopg2.connect(**params)

def update_app_settings(conn: psycopg2.extensions.connection, settings: Dict[str, Any]) -> None:
    """Update application settings in the database."""
    with conn.cursor() as cur:
        for key, value in settings.items():
            cur.execute("""
                INSERT INTO app_settings (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE
                SET value = EXCLUDED.value,
                    updated_at = NOW()
            """, (key, str(value)))
    conn.commit()

def main():
    parser = argparse.ArgumentParser(description='Manage database settings')
    parser.add_argument('--env', required=True, choices=['development', 'staging', 'production'],
                      help='Target environment')
    parser.add_argument('--action', required=True, choices=['update', 'verify'],
                      help='Action to perform')
    parser.add_argument('--settings', type=str,
                      help='JSON string of settings to update')
    
    args = parser.parse_args()
    
    try:
        conn = get_db_connection(args.env)
        
        if args.action == 'update':
            if not args.settings:
                raise ValueError("--settings is required for update action")
            
            settings = json.loads(args.settings)
            update_app_settings(conn, settings)
            print(f"✅ Successfully updated settings for {args.env} environment")
            
        elif args.action == 'verify':
            # Verify database connection and settings table
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM app_settings")
                count = cur.fetchone()[0]
                print(f"✅ Successfully connected to {args.env} database")
                print(f"Found {count} settings in app_settings table")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main() 