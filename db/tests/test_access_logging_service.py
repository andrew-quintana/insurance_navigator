import pytest
from datetime import datetime, timedelta, date
from uuid import uuid4
import json
from unittest.mock import MagicMock, AsyncMock
import os
import asyncio
from db.services.db_pool import DatabasePool
from db.services.access_logging_service import AccessLoggingService

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.policy_access_logs = AsyncMock()
    return session

@pytest.fixture
def logging_service(mock_db_session):
    """Create an instance of AccessLoggingService with a mock session."""
    return AccessLoggingService(mock_db_session)

@pytest.fixture
async def db_pool():
    dsn = os.getenv("DATABASE_URL")
    pool = DatabasePool(dsn)
    await pool.initialize()
    yield pool
    await pool.close()

@pytest.fixture
def sample_log_entry():
    """Create a sample log entry."""
    return {
        'id': str(uuid4()),
        'policy_id': str(uuid4()),
        'user_id': str(uuid4()),
        'action': 'read',
        'actor_type': 'user',
        'actor_id': str(uuid4()),
        'timestamp': datetime.utcnow().isoformat(),
        'purpose': 'policy_review',
        'metadata': {'source': 'web_portal'}
    }

@pytest.fixture
def access_logging_service(db_pool):
    return AccessLoggingService(db_pool)

@pytest.mark.asyncio
async def test_log_access(logging_service, mock_db_session, sample_log_entry):
    """Test logging an access event."""
    # Setup
    mock_db_session.execute_with_retry = AsyncMock(return_value=None)

    # Execute
    result = await logging_service.log_access(
        policy_id=sample_log_entry['policy_id'],
        user_id=sample_log_entry['user_id'],
        action=sample_log_entry['action'],
        actor_type=sample_log_entry['actor_type'],
        actor_id=sample_log_entry['actor_id'],
        purpose=sample_log_entry['purpose'],
        metadata=sample_log_entry['metadata']
    )

    # Verify
    assert result['policy_id'] == sample_log_entry['policy_id']
    assert result['user_id'] == sample_log_entry['user_id']
    assert result['action'] == sample_log_entry['action']
    assert result['actor_type'] == sample_log_entry['actor_type']
    assert result['purpose'] == sample_log_entry['purpose']
    assert result['metadata'] == sample_log_entry['metadata']
    mock_db_session.execute_with_retry.assert_called_once()

@pytest.mark.asyncio
async def test_log_access_invalid_actor_type(logging_service):
    """Test logging with invalid actor type."""
    with pytest.raises(RuntimeError) as exc_info:
        await logging_service.log_access(
            policy_id=str(uuid4()),
            user_id=str(uuid4()),
            action='read',
            actor_type='invalid',
            actor_id=str(uuid4()),
            purpose='test',
            metadata={}
        )
    assert "actor_type must be either 'user' or 'agent'" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_access_history(access_logging_service, sample_log_entry, db_pool):
    # Insert a policy record to satisfy FK constraint
    insert_policy_sql = '''
        INSERT INTO policy_records (
            policy_id, summary, structured_metadata, raw_policy_path, encrypted_policy_data, encryption_key_id, source_type, coverage_start_date, coverage_end_date, created_at, updated_at, version
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW(), 1
        )
    '''
    await db_pool.execute_with_retry(
        insert_policy_sql,
        sample_log_entry['policy_id'],
        json.dumps({}),  # summary
        json.dumps({}),  # structured_metadata
        '/dev/null',
        json.dumps({}),  # encrypted_policy_data
        None,  # encryption_key_id
        'uploaded',  # source_type
        date.today(),  # coverage_start_date
        date.today(),  # coverage_end_date
    )
    # Insert a sample log entry
    insert_sql = '''
        INSERT INTO policy_access_logs (id, policy_id, user_id, action, actor_type, actor_id, timestamp, purpose, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    '''
    ts = datetime.fromisoformat(sample_log_entry['timestamp'])
    print(f"Inserted log timestamp: {ts.isoformat()}")
    await db_pool.execute_with_retry(
        insert_sql,
        sample_log_entry['id'],
        sample_log_entry['policy_id'],
        sample_log_entry['user_id'],
        sample_log_entry['action'],
        sample_log_entry['actor_type'],
        sample_log_entry['actor_id'],
        ts,
        sample_log_entry['purpose'],
        json.dumps(sample_log_entry['metadata'])
    )
    # Retrieve access history
    result = await access_logging_service.get_access_history(
        policy_id=sample_log_entry['policy_id'],
        user_id=sample_log_entry['user_id'],
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow()
    )
    print(f"Query results: {result}")
    assert any(str(log['policy_id']) == sample_log_entry['policy_id'] for log in result)
    # Cleanup
    await db_pool.execute_with_retry(
        "DELETE FROM policy_access_logs WHERE id = $1",
        sample_log_entry['id']
    )
    await db_pool.execute_with_retry(
        "DELETE FROM policy_records WHERE policy_id = $1",
        sample_log_entry['policy_id']
    )

@pytest.mark.asyncio
async def test_get_user_access_summary(logging_service, mock_db_session):
    """Test getting user access summary."""
    # Setup
    summary_result = {
        'total_accesses': 10,
        'unique_policies': 3,
        'action_breakdown': [
            {
                'action': 'read',
                'actor_type': 'user',
                'count': 7,
                'last_access': datetime.utcnow().isoformat()
            },
            {
                'action': 'write',
                'actor_type': 'user',
                'count': 3,
                'last_access': datetime.utcnow().isoformat()
            }
        ]
    }
    mock_db_session.policy_access_logs.aggregate = MagicMock()
    mock_db_session.policy_access_logs.aggregate.return_value.to_list = AsyncMock(
        return_value=[summary_result]
    )
    
    # Execute
    result = await logging_service.get_user_access_summary(
        user_id=str(uuid4()),
        start_date=(datetime.utcnow() - timedelta(days=30)).isoformat(),
        end_date=datetime.utcnow().isoformat()
    )
    
    # Verify
    assert result == summary_result
    mock_db_session.policy_access_logs.aggregate.assert_called_once()

@pytest.mark.asyncio
async def test_get_policy_access_summary(logging_service, mock_db_session):
    """Test getting policy access summary."""
    # Setup
    summary_result = {
        'total_accesses': 15,
        'unique_users': 5,
        'action_breakdown': [
            {
                'action': 'read',
                'actor_type': 'user',
                'count': 10,
                'last_access': datetime.utcnow().isoformat()
            },
            {
                'action': 'write',
                'actor_type': 'agent',
                'count': 5,
                'last_access': datetime.utcnow().isoformat()
            }
        ]
    }
    mock_db_session.policy_access_logs.aggregate = MagicMock()
    mock_db_session.policy_access_logs.aggregate.return_value.to_list = AsyncMock(
        return_value=[summary_result]
    )
    
    # Execute
    result = await logging_service.get_policy_access_summary(
        policy_id=str(uuid4()),
        start_date=(datetime.utcnow() - timedelta(days=7)).isoformat(),
        end_date=datetime.utcnow().isoformat()
    )
    
    # Verify
    assert result == summary_result
    mock_db_session.policy_access_logs.aggregate.assert_called_once()

@pytest.mark.asyncio
async def test_empty_access_history(access_logging_service, db_pool):
    """Test retrieving empty access history from the real database."""
    # Insert a policy record to satisfy FK constraint (but do not insert any logs)
    policy_id = str(uuid4())
    insert_policy_sql = '''
        INSERT INTO policy_records (
            policy_id, summary, structured_metadata, raw_policy_path, encrypted_policy_data, encryption_key_id, source_type, coverage_start_date, coverage_end_date, created_at, updated_at, version
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW(), 1
        )
    '''
    await db_pool.execute_with_retry(
        insert_policy_sql,
        policy_id,
        json.dumps({}),
        json.dumps({}),
        '/dev/null',
        json.dumps({}),
        None,
        'uploaded',
        date.today(),
        date.today(),
    )
    # Query for logs (should be empty)
    result = await access_logging_service.get_access_history(
        policy_id=policy_id,
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow()
    )
    print(f"Empty access history query results: {result}")
    assert result == []
    # Cleanup
    await db_pool.execute_with_retry(
        "DELETE FROM policy_records WHERE policy_id = $1",
        policy_id
    )

@pytest.mark.asyncio
async def test_empty_user_summary(logging_service, mock_db_session):
    """Test getting empty user access summary."""
    # Setup
    mock_db_session.policy_access_logs.aggregate = MagicMock()
    mock_db_session.policy_access_logs.aggregate.return_value.to_list = AsyncMock(
        return_value=[]
    )
    
    # Execute
    result = await logging_service.get_user_access_summary(user_id=str(uuid4()))
    
    # Verify
    assert result['total_accesses'] == 0
    assert result['unique_policies'] == 0
    assert result['action_breakdown'] == []

@pytest.mark.asyncio
async def test_empty_policy_summary(logging_service, mock_db_session):
    """Test getting empty policy access summary."""
    # Setup
    mock_db_session.policy_access_logs.aggregate = MagicMock()
    mock_db_session.policy_access_logs.aggregate.return_value.to_list = AsyncMock(
        return_value=[]
    )
    
    # Execute
    result = await logging_service.get_policy_access_summary(policy_id=str(uuid4()))
    
    # Verify
    assert result['total_accesses'] == 0
    assert result['unique_users'] == 0
    assert result['action_breakdown'] == []

@pytest.mark.asyncio
async def test_log_access_integration(access_logging_service, db_pool, sample_log_entry):
    # Insert a policy record to satisfy FK constraint
    insert_policy_sql = '''
        INSERT INTO policy_records (
            policy_id, summary, structured_metadata, raw_policy_path, encrypted_policy_data, encryption_key_id, source_type, coverage_start_date, coverage_end_date, created_at, updated_at, version
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW(), 1
        )
    '''
    await db_pool.execute_with_retry(
        insert_policy_sql,
        sample_log_entry['policy_id'],
        json.dumps({}),
        json.dumps({}),
        '/dev/null',
        json.dumps({}),
        None,
        'uploaded',
        date.today(),
        date.today(),
    )
    # Call log_access
    await access_logging_service.log_access(
        policy_id=sample_log_entry['policy_id'],
        user_id=sample_log_entry['user_id'],
        action=sample_log_entry['action'],
        actor_type=sample_log_entry['actor_type'],
        actor_id=sample_log_entry['actor_id'],
        purpose=sample_log_entry['purpose'],
        metadata=sample_log_entry['metadata']
    )
    # Verify the log is present
    result = await access_logging_service.get_access_history(
        policy_id=sample_log_entry['policy_id'],
        user_id=sample_log_entry['user_id'],
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow()
    )
    print(f"log_access integration query results: {result}")
    assert any(str(log['policy_id']) == sample_log_entry['policy_id'] for log in result)
    # Cleanup
    await db_pool.execute_with_retry(
        "DELETE FROM policy_access_logs WHERE policy_id = $1 AND user_id = $2",
        sample_log_entry['policy_id'],
        sample_log_entry['user_id']
    )
    await db_pool.execute_with_retry(
        "DELETE FROM policy_records WHERE policy_id = $1",
        sample_log_entry['policy_id']
    ) 