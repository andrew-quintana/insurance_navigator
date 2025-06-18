#!/usr/bin/env python3

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def check_users():
    load_dotenv()
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0, 
        server_settings={'jit': 'off'}
    )
    
    # Check existing user IDs from documents
    users = await conn.fetch('SELECT DISTINCT user_id FROM documents LIMIT 5')
    print('Existing user IDs:')
    for user in users:
        print(f'  {user["user_id"]}')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_users()) 

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def check_users():
    load_dotenv()
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0, 
        server_settings={'jit': 'off'}
    )
    
    # Check existing user IDs from documents
    users = await conn.fetch('SELECT DISTINCT user_id FROM documents LIMIT 5')
    print('Existing user IDs:')
    for user in users:
        print(f'  {user["user_id"]}')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_users()) 