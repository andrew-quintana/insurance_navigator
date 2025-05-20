"""Policy access evaluation service."""

from typing import Dict, Any, Optional
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

class PolicyAccessEvaluator:
    """Evaluates access permissions for policies."""

    def __init__(self, db_session):
        """Initialize the policy access evaluator.
        
        Args:
            db_session: Database session for access checks
        """
        self.db = db_session

    def has_access(
        self,
        user_id: str,
        resource_id: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if a user has access to perform an action.
        
        Args:
            user_id: UUID of the user
            resource_id: UUID of the resource
            action: Type of action ('read', 'write', 'delete')
            context: Optional additional context for the access check
            
        Returns:
            True if access is granted, False otherwise
        """
        try:
            # Get user roles and permissions
            user_roles = self.db.user_roles.get(user_id, {})
            
            # Admin users have full access
            if 'admin' in user_roles.get('roles', []):
                return True
            
            # Check if user has required permission
            if action not in user_roles.get('permissions', []):
                return False
            
            # Check resource-specific access
            resource_access = self.db.resource_access.get(resource_id, {})
            if not resource_access:
                return False
            
            # Check time-based restrictions
            if context and 'time' in context:
                access_time = datetime.fromisoformat(context['time'])
                if not self._check_time_restrictions(access_time, resource_access):
                    return False
            
            # Check IP-based restrictions
            if context and 'ip_address' in context:
                if not self._check_ip_restrictions(context['ip_address'], resource_access):
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Access check failed - User: {user_id}, Resource: {resource_id}, Error: {str(e)}")
            return False

    def _check_time_restrictions(
        self,
        access_time: datetime,
        resource_access: Dict[str, Any]
    ) -> bool:
        """Check time-based access restrictions.
        
        Args:
            access_time: Time of access attempt
            resource_access: Resource access configuration
            
        Returns:
            True if time restrictions are met
        """
        restrictions = resource_access.get('time_restrictions', {})
        if not restrictions:
            return True
        
        # Convert to UTC for comparison
        utc_time = access_time.astimezone(pytz.UTC)
        
        # Check allowed hours
        if 'allowed_hours' in restrictions:
            start_hour = restrictions['allowed_hours']['start']
            end_hour = restrictions['allowed_hours']['end']
            current_hour = utc_time.hour
            
            if not (start_hour <= current_hour <= end_hour):
                return False
        
        return True

    def _check_ip_restrictions(
        self,
        ip_address: str,
        resource_access: Dict[str, Any]
    ) -> bool:
        """Check IP-based access restrictions.
        
        Args:
            ip_address: IP address of the request
            resource_access: Resource access configuration
            
        Returns:
            True if IP restrictions are met
        """
        restrictions = resource_access.get('ip_restrictions', {})
        if not restrictions:
            return True
        
        # Check allowed IP ranges
        allowed_ips = restrictions.get('allowed_ips', [])
        if allowed_ips and ip_address not in allowed_ips:
            return False
        
        # Check blocked IP ranges
        blocked_ips = restrictions.get('blocked_ips', [])
        if ip_address in blocked_ips:
            return False
        
        return True 