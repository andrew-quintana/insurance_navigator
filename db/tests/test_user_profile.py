import os
import asyncio
import pytest
import asyncpg
from dotenv import load_dotenv
from datetime import date
import uuid

load_dotenv()

@pytest.fixture
async def db_conn():
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'insurance_navigator')
    )
    yield conn
    await conn.close()

@pytest.mark.asyncio
async def test_user_profile_crud(db_conn):
    user_id = str(uuid.uuid4())
    email = f"testuser_{user_id[:8]}@example.com"
    # Insert
    insert_sql = '''
        INSERT INTO users (id, email, hashed_password, full_name, date_of_birth, sex, height_cm, weight_kg, blood_type, allergies, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
        RETURNING *
    '''
    allergies = '["peanuts", "latex"]'
    user = await db_conn.fetchrow(insert_sql, user_id, email, 'testpassword', "Test User", date(1990, 1, 1), "male", 180, 75, "O+", allergies)
    assert user['email'] == email
    # Retrieve
    select_sql = 'SELECT * FROM users WHERE id = $1'
    user2 = await db_conn.fetchrow(select_sql, user_id)
    assert str(user2['id']) == user_id
    # Update
    update_sql = 'UPDATE users SET weight_kg = $1 WHERE id = $2 RETURNING *'
    user3 = await db_conn.fetchrow(update_sql, 80, user_id)
    assert user3['weight_kg'] == 80
    # Delete
    delete_sql = 'DELETE FROM users WHERE id = $1'
    await db_conn.execute(delete_sql, user_id)
    user4 = await db_conn.fetchrow(select_sql, user_id)
    assert user4 is None 