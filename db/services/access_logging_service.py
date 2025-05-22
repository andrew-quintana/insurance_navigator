from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
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
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get access history with optional filters using Postgres."""
        try:
            # Build SQL query and parameters
            sql = "SELECT * FROM policy_access_logs WHERE TRUE"
            params = []
            if policy_id:
                sql += " AND policy_id = $%d" % (len(params) + 1)
                params.append(policy_id)
            if user_id:
                sql += " AND user_id = $%d" % (len(params) + 1)
                params.append(user_id)
            if action:
                sql += " AND action = $%d" % (len(params) + 1)
                params.append(action)
            if start_time:
                sql += " AND timestamp >= $%d" % (len(params) + 1)
                params.append(start_time)
            if end_time:
                sql += " AND timestamp <= $%d" % (len(params) + 1)
                params.append(end_time)
            sql += " ORDER BY timestamp DESC LIMIT $%d" % (len(params) + 1)
            params.append(limit)

            rows = await self.db.fetch_with_retry(sql, *params)
            # Convert asyncpg.Record to dict
            logs = [dict(row) for row in rows]
            return logs
        except Exception as e:
            logger.error(f"Failed to retrieve access history: {str(e)}")
            raise RuntimeError(f"Failed to retrieve access history: {str(e)}")

    async def get_user_activity(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get activity summary for a user.
        
        Args:
            user_id: UUID of the user
            start_time: Optional start time for the summary
            end_time: Optional end time for the summary
            
        Returns:
            Activity summary dictionary
        """
        try:
            # Build time range query
            query = {'user_id': user_id}
            if start_time or end_time:
                query['timestamp'] = {}
                if start_time:
                    query['timestamp']['$gte'] = start_time.isoformat()
                if end_time:
                    query['timestamp']['$lte'] = end_time.isoformat()

            # Get activity counts
            pipeline = [
                {'$match': query},
                {
                    '$group': {
                        '_id': {
                            'action': '$action',
                            'actor_type': '$actor_type'
                        },
                        'count': {'$sum': 1}
                    }
                }
            ]
            
            activity_counts = await self.db.policy_access_logs \
                .aggregate(pipeline) \
                .to_list(None)

            # Format results
            summary = {
                'user_id': user_id,
                'period': {
                    'start': start_time.isoformat() if start_time else None,
                    'end': end_time.isoformat() if end_time else None
                },
                'activity_counts': {
                    f"{item['_id']['action']}_{item['_id']['actor_type']}": item['count']
                    for item in activity_counts
                }
            }

            return summary
        except Exception as e:
            logger.error(f"Failed to get user activity summary: {str(e)}")
            raise RuntimeError(f"Failed to get user activity summary: {str(e)}")

    async def cleanup_old_logs(
        self,
        retention_days: int = 90
    ) -> int:
        """Clean up old access logs.
        
        Args:
            retention_days: Number of days to retain logs
            
        Returns:
            Number of deleted log entries
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            result = await self.db.policy_access_logs.delete_many({
                'timestamp': {'$lt': cutoff_date.isoformat()}
            })
            
            deleted_count = result.deleted_count
            logger.info(f"Cleaned up {deleted_count} old access logs")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to clean up old access logs: {str(e)}")
            raise RuntimeError(f"Failed to clean up old access logs: {str(e)}")

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