import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'insurance_navigator')
}

async def test_connection():
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        print('✅ Database connection successful!')
        await conn.close()
    except Exception as e:
        print(f'❌ Database connection failed: {e}')

if __name__ == '__main__':
    asyncio.run(test_connection()) 