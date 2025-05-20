from typing import Any, Dict, List, Optional
from datetime import datetime
import pytz

class PolicyAccessEvaluator:
    """
    Evaluates whether a user has access to a given policy or resource based on roles, policy conditions, and RLS integration.
    """
    def __init__(self, db_session):
        """
        Initialize the evaluator with a database session or connection.
        """
        self.db = db_session

    def has_access(self, user_id: str, resource_id: str, action: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if the user has access to perform an action on a resource.
        Args:
            user_id: The UUID of the user.
            resource_id: The UUID of the resource (e.g., policy).
            action: The action to check (e.g., 'read', 'write', 'delete').
            context: Optional context for advanced policy checks.
        Returns:
            True if access is granted, False otherwise.
        """
        try:
            # Get user roles and check if they have the required permissions
            roles = self.get_user_roles(user_id)
            if not roles:
                return False

            # Check RLS policies
            if not self.rls_check(user_id, resource_id):
                return False

            # Get permissions for the roles
            user_data = self.db.user_roles.get(user_id, {})
            allowed_permissions = user_data.get('permissions', [])
            
            # Check if the action is allowed
            if action not in allowed_permissions:
                return False

            # Evaluate additional policy conditions if context is provided
            if context and not self.evaluate_policy_conditions(user_id, resource_id, action, context):
                return False

            return True
        except Exception as e:
            # Log the error and return False for security
            print(f"Error checking access: {str(e)}")
            return False

    def get_user_roles(self, user_id: str, resource_id: Optional[str] = None) -> List[str]:
        """
        Retrieve all roles a user has for a given resource.
        Args:
            user_id: The UUID of the user.
            resource_id: Optional resource UUID to filter roles.
        Returns:
            List of role names.
        """
        try:
            user_data = self.db.user_roles.get(user_id, {})
            return user_data.get('roles', [])
        except Exception as e:
            print(f"Error retrieving user roles: {str(e)}")
            return []

    def evaluate_policy_conditions(self, user_id: str, resource_id: str, action: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Evaluate custom policy conditions for access control.
        Args:
            user_id: The UUID of the user.
            resource_id: The UUID of the resource.
            action: The action to check.
            context: Optional context for advanced checks.
        Returns:
            True if conditions are met, False otherwise.
        """
        if not context:
            return True

        try:
            # Check IP address restrictions if specified
            if 'ip_address' in context:
                allowed_ips = self.db.policies.get('allowed_ips', ['192.168.1.1'])  # Example allowed IPs
                if context['ip_address'] not in allowed_ips:
                    return False

            # Check time-based restrictions if specified
            if 'time' in context:
                try:
                    access_time = datetime.fromisoformat(context['time'].replace('Z', '+00:00'))
                    # Example: Only allow access during business hours (9 AM to 5 PM UTC)
                    hour = access_time.hour
                    if not (9 <= hour < 17):
                        return False
                except ValueError:
                    return False

            # Check request metadata if specified
            if 'request_metadata' in context:
                metadata = context['request_metadata']
                # Example: Only allow internal requests
                if metadata.get('source') != 'internal':
                    return False

            return True
        except Exception as e:
            print(f"Error evaluating policy conditions: {str(e)}")
            return False

    def rls_check(self, user_id: str, resource_id: str) -> bool:
        """
        Integrate with Row Level Security (RLS) to enforce database-level access control.
        Args:
            user_id: The UUID of the user.
            resource_id: The UUID of the resource.
        Returns:
            True if RLS allows access, False otherwise.
        """
        try:
            # Check if resource exists and has RLS rules
            resource_rules = self.db.rls_rules.get(resource_id)
            if not resource_rules:
                return False

            # Check if user is in allowed users list
            allowed_users = resource_rules.get('allowed_users', [])
            return user_id in allowed_users
        except Exception as e:
            print(f"Error checking RLS: {str(e)}")
            return False 