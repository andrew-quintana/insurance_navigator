"""Policy operations service."""

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import json
import logging

from .policy_access_evaluator import PolicyAccessEvaluator
from .encryption_key_manager import EncryptionKeyManager
from .access_logging_service import AccessLoggingService

logger = logging.getLogger(__name__)

class PolicyOperations:
    """Handles CRUD operations for policies with encryption and access control."""

    def __init__(
        self,
        db_session,
        access_evaluator: PolicyAccessEvaluator,
        encryption_service: EncryptionKeyManager,
        access_logger: AccessLoggingService
    ):
        """Initialize the policy operations service.
        
        Args:
            db_session: Database session
            access_evaluator: Policy access evaluator instance
            encryption_service: Encryption service instance
            access_logger: Access logging service instance
        """
        self.db = db_session
        self.access_evaluator = access_evaluator
        self.encryption_service = encryption_service
        self.access_logger = access_logger

    async def create_policy(
        self,
        user_id: str,
        policy_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new policy.
        
        Args:
            user_id: UUID of the user creating the policy
            policy_data: Policy data to store
            metadata: Optional metadata about the policy
            
        Returns:
            The created policy with non-sensitive data
        """
        # Check write access
        if not self.access_evaluator.has_access(user_id, None, 'write'):
            raise PermissionError("User does not have write access")

        try:
            # Separate sensitive and non-sensitive data
            sensitive_data = {
                'ssn': policy_data.pop('ssn', None),
                'medical_info': policy_data.pop('medical_info', None),
                'financial_data': policy_data.pop('financial_data', None)
            }

            # Encrypt sensitive data
            encrypted_data = await self.encryption_service.encrypt_data(
                json.dumps(sensitive_data)
            )

            # Create policy record
            policy_id = str(uuid4())
            policy = {
                'id': policy_id,
                'data': policy_data,
                'encrypted_data': encrypted_data,
                'metadata': metadata or {},
                'created_at': datetime.utcnow().isoformat(),
                'created_by': user_id,
                'version': 1
            }

            await self.db.policies.insert_one(policy)

            # Log the creation
            await self.access_logger.log_access(
                policy_id=policy_id,
                user_id=user_id,
                action='create',
                actor_type='user',
                actor_id=user_id,
                purpose='policy_creation',
                metadata={'version': 1}
            )

            # Return policy without sensitive data
            return {
                'id': policy_id,
                'data': policy_data,
                'metadata': metadata or {},
                'created_at': policy['created_at'],
                'version': 1
            }
        except Exception as e:
            logger.error(f"Failed to create policy: {str(e)}")
            raise RuntimeError(f"Failed to create policy: {str(e)}")

    async def get_policy(
        self,
        user_id: str,
        policy_id: str,
        include_sensitive: bool = False
    ) -> Dict[str, Any]:
        """Get a policy by ID.
        
        Args:
            user_id: UUID of the user requesting the policy
            policy_id: UUID of the policy to retrieve
            include_sensitive: Whether to include sensitive data
            
        Returns:
            The requested policy
        """
        # Check read access
        if not self.access_evaluator.has_access(user_id, policy_id, 'read'):
            raise PermissionError("User does not have read access")

        try:
            # Get policy
            policy = await self.db.policies.find_one({'id': policy_id})
            if not policy:
                raise ValueError(f"Policy {policy_id} not found")

            # Log the access
            await self.access_logger.log_access(
                policy_id=policy_id,
                user_id=user_id,
                action='read',
                actor_type='user',
                actor_id=user_id,
                purpose='policy_retrieval'
            )

            # Return policy data
            result = {
                'id': policy['id'],
                'data': policy['data'],
                'metadata': policy.get('metadata', {}),
                'created_at': policy['created_at'],
                'version': policy['version']
            }

            # Include sensitive data if requested and authorized
            if include_sensitive:
                if not self.access_evaluator.has_access(user_id, policy_id, 'read_sensitive'):
                    raise PermissionError("User does not have access to sensitive data")
                
                encrypted_data = policy.get('encrypted_data')
                if encrypted_data:
                    sensitive_data = json.loads(
                        await self.encryption_service.decrypt_data(encrypted_data)
                    )
                    result['sensitive_data'] = sensitive_data

            return result
        except Exception as e:
            logger.error(f"Failed to get policy {policy_id}: {str(e)}")
            raise RuntimeError(f"Failed to get policy: {str(e)}")

    async def update_policy(
        self,
        user_id: str,
        policy_id: str,
        updates: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update an existing policy.
        
        Args:
            user_id: The UUID of the user updating the policy
            policy_id: The UUID of the policy to update
            updates: The updates to apply to the policy
            metadata: Optional metadata updates
            
        Returns:
            The updated policy with non-sensitive data
        """
        # Check write access
        if not self.access_evaluator.has_access(user_id, policy_id, 'write'):
            raise PermissionError("User does not have write access")

        try:
            # Get existing policy
            existing_policy = await self.db.policies.find_one({'id': policy_id})
            if not existing_policy:
                raise ValueError(f"Policy {policy_id} not found")

            # Separate sensitive and non-sensitive updates
            sensitive_updates = {
                'ssn': updates.pop('ssn', None),
                'medical_info': updates.pop('medical_info', None),
                'financial_data': updates.pop('financial_data', None)
            }

            # If there are sensitive updates, decrypt existing, update, and re-encrypt
            if any(sensitive_updates.values()):
                existing_encrypted = existing_policy.get('encrypted_data')
                if existing_encrypted:
                    existing_sensitive = json.loads(
                        await self.encryption_service.decrypt_data(existing_encrypted)
                    )
                    existing_sensitive.update(sensitive_updates)
                    encrypted_data = await self.encryption_service.encrypt_data(
                        json.dumps(existing_sensitive)
                    )
                else:
                    encrypted_data = await self.encryption_service.encrypt_data(
                        json.dumps(sensitive_updates)
                    )
            else:
                encrypted_data = existing_policy.get('encrypted_data')

            # Prepare update record
            new_version = existing_policy['version'] + 1
            update_record = {
                'data': {**existing_policy['data'], **updates},
                'encrypted_data': encrypted_data,
                'metadata': {**existing_policy.get('metadata', {}), **(metadata or {})},
                'updated_at': datetime.utcnow().isoformat(),
                'updated_by': user_id,
                'version': new_version
            }

            # Update in database
            await self.db.policies.update_one(
                {'id': policy_id},
                {'$set': update_record}
            )

            # Log the update
            await self.access_logger.log_access(
                policy_id=policy_id,
                user_id=user_id,
                action='update',
                actor_type='user',
                actor_id=user_id,
                purpose='policy_update',
                metadata={
                    'version': new_version,
                    'has_sensitive_updates': any(sensitive_updates.values())
                }
            )

            # Return updated policy without sensitive data
            return await self.get_policy(user_id, policy_id)
        except Exception as e:
            raise RuntimeError(f"Failed to update policy: {str(e)}")

    async def delete_policy(
        self,
        user_id: str,
        policy_id: str
    ) -> bool:
        """Delete a policy.
        
        Args:
            user_id: UUID of the user deleting the policy
            policy_id: UUID of the policy to delete
            
        Returns:
            True if deleted successfully
        """
        # Check delete access
        if not self.access_evaluator.has_access(user_id, policy_id, 'delete'):
            raise PermissionError("User does not have delete access")

        try:
            # Get policy to verify it exists
            policy = await self.db.policies.find_one({'id': policy_id})
            if not policy:
                raise ValueError(f"Policy {policy_id} not found")

            # Delete from database
            result = await self.db.policies.delete_one({'id': policy_id})

            # Log the deletion
            await self.access_logger.log_access(
                policy_id=policy_id,
                user_id=user_id,
                action='delete',
                actor_type='user',
                actor_id=user_id,
                purpose='policy_deletion'
            )

            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete policy {policy_id}: {str(e)}")
            raise RuntimeError(f"Failed to delete policy: {str(e)}")

    async def list_policies(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List policies with pagination.
        
        Args:
            user_id: UUID of the user requesting the list
            filters: Optional filters to apply
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Dict containing policies and pagination info
        """
        try:
            # Build query
            query = filters or {}
            
            # Calculate pagination
            skip = (page - 1) * page_size
            
            # Get total count
            total = await self.db.policies.count_documents(query)
            
            # Get policies
            policies = await self.db.policies.find(query) \
                .sort('created_at', -1) \
                .skip(skip) \
                .limit(page_size) \
                .to_list(None)
            
            # Filter out sensitive data
            filtered_policies = []
            for policy in policies:
                if self.access_evaluator.has_access(user_id, policy['id'], 'read'):
                    filtered_policies.append({
                        'id': policy['id'],
                        'data': policy['data'],
                        'metadata': policy.get('metadata', {}),
                        'created_at': policy['created_at'],
                        'version': policy['version']
                    })
            
            return {
                'items': filtered_policies,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"Failed to list policies: {str(e)}")
            raise RuntimeError(f"Failed to list policies: {str(e)}") 