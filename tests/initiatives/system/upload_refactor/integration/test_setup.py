import pytest
from fastapi.testclient import TestClient
from main import app
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "degraded"]
    assert "database" in response.json()
    assert "version" in response.json()

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Insurance Navigator API" in response.json()["message"]

def test_cors_headers():
    """Test CORS headers are properly set"""
    response = client.options("/", headers={"origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection using environment variables"""
    db_url = os.getenv("DATABASE_URL")
    assert db_url is not None, "DATABASE_URL environment variable not set"
    
    try:
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Test basic query
        cur.execute("SELECT 1")
        result = cur.fetchone()
        assert result[0] == 1
        
        # Test tables exist
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name IN ('users', 'documents')
        """)
        tables = [row[0] for row in cur.fetchall()]
        assert 'users' in tables, "users table not found"
        assert 'documents' in tables, "documents table not found"
        
        # Test RLS is enabled
        cur.execute("""
            SELECT tablename, rowsecurity 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename IN ('users', 'documents')
        """)
        rls_status = {row[0]: row[1] for row in cur.fetchall()}
        assert rls_status['users'], "RLS not enabled on users table"
        assert rls_status['documents'], "RLS not enabled on documents table"
        
        cur.close()
        conn.close()
    except Exception as e:
        pytest.fail(f"Database connection failed: {str(e)}") 