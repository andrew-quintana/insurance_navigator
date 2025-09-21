#!/usr/bin/env python3
"""
Cleanup script to remove duplicate data from production database
that could cause conflicts when testing uploads from frontend UI.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

async def cleanup_duplicates():
    """Clean up duplicate data from production database."""
    
    # Connect to production database with proper SSL and pgbouncer settings
    conn = await asyncpg.connect(
        '${DATABASE_URL}