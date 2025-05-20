from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID, uuid4
import logging
import json

logger = logging.getLogger(__name__)

class AccessLoggingService:
    """
    Service for handling all access logging operations in the system.
    Provides comprehensive audit trail for all policy-related operations.
    """
    
    def __init__(self, db_session):
        """
        Initialize the access logging service.
        
        Args:
            db_session: Database session or connection
        """
        self.db = db_session

    async def log_access(
        self,
        policy_id: str,
        user_id: str,
        action: str,
        actor_type: str,
        actor_id: str,
        purpose: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log an access event to the policy_access_logs table.
        
        Args:
            policy_id: UUID of the policy being accessed
            user_id: UUID of the user the access is being performed for
            action: Type of action being performed (e.g., 'read', 'write', 'delete')
            actor_type: Type of actor performing the action ('user' or 'agent')
            actor_id: UUID of the actor performing the action
            purpose: Purpose of the access (e.g., 'policy_review', 'claim_processing')
            metadata: Optional additional metadata about the access
            
        Returns:
            The created access log entry
            
        Raises:
            ValueError: If required parameters are invalid
            RuntimeError: If logging fails
        """
        try:
            # Validate actor_type
            if actor_type not in ['user', 'agent']:
                raise ValueError("actor_type must be either 'user' or 'agent'")

            # Create log entry
            log_entry = {
                'id': str(uuid4()),
                'policy_id': policy_id,
                'user_id': user_id,
                'action': action,
                'actor_type': actor_type,
                'actor_id': actor_id,
                'timestamp': datetime.utcnow().isoformat(),
                'purpose': purpose,
                'metadata': metadata or {}
            }

            # Insert into database
            await self.db.policy_access_logs.insert_one(log_entry)
            
            logger.info(
                f"Access logged - Policy: {policy_id}, User: {user_id}, "
                f"Action: {action}, Actor: {actor_type}:{actor_id}"
            )

            return log_entry
        except Exception as e:
            logger.error(
                f"Failed to log access - Policy: {policy_id}, User: {user_id}, "
                f"Action: {action}, Error: {str(e)}"
            )
            raise RuntimeError(f"Failed to log access: {str(e)}")

    async def get_access_history(
        self,
        policy_id: Optional[str] = None,
        user_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Retrieve access history with optional filtering.
        
        Args:
            policy_id: Optional policy ID to filter by
            user_id: Optional user ID to filter by
            actor_id: Optional actor ID to filter by
            action: Optional action type to filter by
            start_date: Optional start date (ISO format) for time range
            end_date: Optional end date (ISO format) for time range
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Dict containing access logs and pagination info
        """
        try:
            # Build query
            query = {}
            if policy_id:
                query['policy_id'] = policy_id
            if user_id:
                query['user_id'] = user_id
            if actor_id:
                query['actor_id'] = actor_id
            if action:
                query['action'] = action
            
            # Add date range if specified
            if start_date or end_date:
                query['timestamp'] = {}
                if start_date:
                    query['timestamp']['$gte'] = start_date
                if end_date:
                    query['timestamp']['$lte'] = end_date

            # Calculate pagination
            skip = (page - 1) * page_size

            # Execute query
            total = await self.db.policy_access_logs.count_documents(query)
            logs = await self.db.policy_access_logs.find(
                query
            ).sort(
                'timestamp', -1
            ).skip(skip).limit(page_size).to_list(length=page_size)

            return {
                'items': logs,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"Failed to retrieve access history: {str(e)}")
            raise RuntimeError(f"Failed to retrieve access history: {str(e)}")

    async def get_user_access_summary(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of access patterns for a specific user.
        
        Args:
            user_id: The user ID to get summary for
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            
        Returns:
            Dict containing access summary statistics
        """
        try:
            # Build match stage
            match_stage = {'user_id': user_id}
            if start_date or end_date:
                match_stage['timestamp'] = {}
                if start_date:
                    match_stage['timestamp']['$gte'] = start_date
                if end_date:
                    match_stage['timestamp']['$lte'] = end_date

            # Aggregate pipeline
            pipeline = [
                {'$match': match_stage},
                {'$group': {
                    '_id': {
                        'action': '$action',
                        'actor_type': '$actor_type'
                    },
                    'count': {'$sum': 1},
                    'policies': {'$addToSet': '$policy_id'},
                    'last_access': {'$max': '$timestamp'}
                }},
                {'$group': {
                    '_id': None,
                    'total_accesses': {'$sum': '$count'},
                    'unique_policies': {'$sum': {'$size': '$policies'}},
                    'action_breakdown': {'$push': {
                        'action': '$_id.action',
                        'actor_type': '$_id.actor_type',
                        'count': '$count',
                        'last_access': '$last_access'
                    }}
                }}
            ]

            # Execute aggregation
            results = await self.db.policy_access_logs.aggregate(pipeline).to_list(length=1)
            
            if not results:
                return {
                    'total_accesses': 0,
                    'unique_policies': 0,
                    'action_breakdown': []
                }

            return results[0]
        except Exception as e:
            logger.error(f"Failed to get user access summary: {str(e)}")
            raise RuntimeError(f"Failed to get user access summary: {str(e)}")

    async def get_policy_access_summary(
        self,
        policy_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of access patterns for a specific policy.
        
        Args:
            policy_id: The policy ID to get summary for
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            
        Returns:
            Dict containing access summary statistics
        """
        try:
            # Build match stage
            match_stage = {'policy_id': policy_id}
            if start_date or end_date:
                match_stage['timestamp'] = {}
                if start_date:
                    match_stage['timestamp']['$gte'] = start_date
                if end_date:
                    match_stage['timestamp']['$lte'] = end_date

            # Aggregate pipeline
            pipeline = [
                {'$match': match_stage},
                {'$group': {
                    '_id': {
                        'action': '$action',
                        'actor_type': '$actor_type'
                    },
                    'count': {'$sum': 1},
                    'users': {'$addToSet': '$user_id'},
                    'last_access': {'$max': '$timestamp'}
                }},
                {'$group': {
                    '_id': None,
                    'total_accesses': {'$sum': '$count'},
                    'unique_users': {'$sum': {'$size': '$users'}},
                    'action_breakdown': {'$push': {
                        'action': '$_id.action',
                        'actor_type': '$_id.actor_type',
                        'count': '$count',
                        'last_access': '$last_access'
                    }}
                }}
            ]

            # Execute aggregation
            results = await self.db.policy_access_logs.aggregate(pipeline).to_list(length=1)
            
            if not results:
                return {
                    'total_accesses': 0,
                    'unique_users': 0,
                    'action_breakdown': []
                }

            return results[0]
        except Exception as e:
            logger.error(f"Failed to get policy access summary: {str(e)}")
            raise RuntimeError(f"Failed to get policy access summary: {str(e)}") 