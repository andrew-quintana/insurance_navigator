import asyncio
import os
import asyncpg
from dotenv import load_dotenv
from datetime import date
import uuid

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'insurance_navigator')
}

async def insert_test_user():
    conn = await asyncpg.connect(**DB_CONFIG)
    user_id = str(uuid.uuid4())
    email = f"testuser_{user_id[:8]}@example.com"
    sql = '''
        INSERT INTO users (
            id, email, hashed_password, full_name, date_of_birth, sex, height_cm, weight_kg, blood_type, allergies, created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW()
        ) RETURNING *
    '''
    values = [
        user_id,
        email,
        'testpassword',
        "Test User",
        date(1990, 1, 1),
        "male",
        180,
        75,
        "O+",
        "[\"peanuts\", \"latex\"]"
    ]
    user = await conn.fetchrow(sql, *values)
    print("Inserted user:", dict(user))
    await conn.close()

if __name__ == '__main__':
    asyncio.run(insert_test_user()) 