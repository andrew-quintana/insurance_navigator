import pytest
from datetime import datetime, timedelta
from uuid import uuid4
import json
from unittest.mock import MagicMock, AsyncMock

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

@pytest.mark.asyncio
async def test_log_access(logging_service, mock_db_session, sample_log_entry):
    """Test logging an access event."""
    # Setup
    mock_db_session.policy_access_logs.insert_one = AsyncMock(return_value=None)
    
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
    mock_db_session.policy_access_logs.insert_one.assert_called_once()

@pytest.mark.asyncio
async def test_log_access_invalid_actor_type(logging_service):
    """Test logging with invalid actor type."""
    with pytest.raises(ValueError) as exc_info:
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
async def test_get_access_history(logging_service, mock_db_session, sample_log_entry):
    """Test retrieving access history."""
    # Setup
    mock_db_session.policy_access_logs.count_documents = AsyncMock(return_value=1)
    mock_db_session.policy_access_logs.find = MagicMock()
    mock_db_session.policy_access_logs.find.return_value.sort = MagicMock()
    mock_db_session.policy_access_logs.find.return_value.sort.return_value.skip = MagicMock()
    mock_db_session.policy_access_logs.find.return_value.sort.return_value.skip.return_value.limit = MagicMock()
    mock_db_session.policy_access_logs.find.return_value.sort.return_value.skip.return_value.limit.return_value.to_list = AsyncMock(
        return_value=[sample_log_entry]
    )
    
    # Execute
    result = await logging_service.get_access_history(
        policy_id=sample_log_entry['policy_id'],
        user_id=sample_log_entry['user_id'],
        start_date=(datetime.utcnow() - timedelta(days=1)).isoformat(),
        end_date=datetime.utcnow().isoformat()
    )
    
    # Verify
    assert result['total'] == 1
    assert result['page'] == 1
    assert result['items'] == [sample_log_entry]
    mock_db_session.policy_access_logs.count_documents.assert_called_once()
    mock_db_session.policy_access_logs.find.assert_called_once()

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
async def test_empty_access_history(logging_service, mock_db_session):
    """Test retrieving empty access history."""
    # Setup
    mock_db_session.policy_access_logs.count_documents = AsyncMock(return_value=0)
    mock_db_session.policy_access_logs.find = MagicMock()
    mock_db_session.policy_access_logs.find.return_value.sort = MagicMock()
    mock_db_session.policy_access_logs.find.return_value.sort.return_value.skip = MagicMock()
    mock_db_session.policy_access_logs.find.return_value.sort.return_value.skip.return_value.limit = MagicMock()
    mock_db_session.policy_access_logs.find.return_value.sort.return_value.skip.return_value.limit.return_value.to_list = AsyncMock(
        return_value=[]
    )
    
    # Execute
    result = await logging_service.get_access_history()
    
    # Verify
    assert result['total'] == 0
    assert result['items'] == []
    assert result['total_pages'] == 0

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