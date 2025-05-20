from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import json

from .policy_access_evaluator import PolicyAccessEvaluator
from .encryption_service import EncryptionService

class PolicyOperations:
    """
    Handles CRUD operations for policies with integrated access control and encryption.
    """
    def __init__(self, db_session, encryption_service: EncryptionService):
        self.db = db_session
        self.encryption_service = encryption_service
        self.access_evaluator = PolicyAccessEvaluator(db_session)

    async def create_policy(
        self,
        user_id: str,
        policy_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new policy with encrypted sensitive data.
        Args:
            user_id: The UUID of the user creating the policy.
            policy_data: The policy data to be stored.
            metadata: Optional metadata for the policy.
        Returns:
            The created policy with non-sensitive data.
        """
        # Check write access
        if not self.access_evaluator.has_access(user_id, None, 'write'):
            raise PermissionError("User does not have write access")

        try:
            # Generate new policy ID
            policy_id = str(uuid4())
            
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

            # Prepare policy record
            policy_record = {
                'id': policy_id,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': user_id,
                'data': policy_data,
                'encrypted_data': encrypted_data,
                'metadata': metadata or {},
                'version': 1,
                'status': 'active'
            }

            # Store in database
            await self.db.policies.insert_one(policy_record)

            # Return non-sensitive data
            return {k: v for k, v in policy_record.items() if k != 'encrypted_data'}
        except Exception as e:
            raise RuntimeError(f"Failed to create policy: {str(e)}")

    async def get_policy(
        self,
        user_id: str,
        policy_id: str,
        include_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve a policy by ID.
        Args:
            user_id: The UUID of the user requesting the policy.
            policy_id: The UUID of the policy to retrieve.
            include_sensitive: Whether to include decrypted sensitive data.
        Returns:
            The policy data.
        """
        # Check read access
        if not self.access_evaluator.has_access(user_id, policy_id, 'read'):
            raise PermissionError("User does not have read access")

        try:
            # Retrieve policy from database
            policy = await self.db.policies.find_one({'id': policy_id})
            if not policy:
                raise ValueError(f"Policy {policy_id} not found")

            # Handle sensitive data if requested
            if include_sensitive and self.access_evaluator.has_access(user_id, policy_id, 'read_sensitive'):
                encrypted_data = policy.get('encrypted_data')
                if encrypted_data:
                    sensitive_data = json.loads(
                        await self.encryption_service.decrypt_data(encrypted_data)
                    )
                    policy['data'].update(sensitive_data)

            # Remove encrypted data from response
            policy.pop('encrypted_data', None)
            return policy
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve policy: {str(e)}")

    async def update_policy(
        self,
        user_id: str,
        policy_id: str,
        updates: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing policy.
        Args:
            user_id: The UUID of the user updating the policy.
            policy_id: The UUID of the policy to update.
            updates: The updates to apply to the policy.
            metadata: Optional metadata updates.
        Returns:
            The updated policy with non-sensitive data.
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
            update_record = {
                'data': {**existing_policy['data'], **updates},
                'encrypted_data': encrypted_data,
                'metadata': {**existing_policy.get('metadata', {}), **(metadata or {})},
                'updated_at': datetime.utcnow().isoformat(),
                'updated_by': user_id,
                'version': existing_policy['version'] + 1
            }

            # Update in database
            await self.db.policies.update_one(
                {'id': policy_id},
                {'$set': update_record}
            )

            # Return updated policy without sensitive data
            return await self.get_policy(user_id, policy_id)
        except Exception as e:
            raise RuntimeError(f"Failed to update policy: {str(e)}")

    async def delete_policy(self, user_id: str, policy_id: str) -> bool:
        """
        Delete a policy by ID.
        Args:
            user_id: The UUID of the user deleting the policy.
            policy_id: The UUID of the policy to delete.
        Returns:
            True if successful, raises exception otherwise.
        """
        # Check delete access
        if not self.access_evaluator.has_access(user_id, policy_id, 'delete'):
            raise PermissionError("User does not have delete access")

        try:
            # Soft delete by updating status
            result = await self.db.policies.update_one(
                {'id': policy_id},
                {
                    '$set': {
                        'status': 'deleted',
                        'deleted_at': datetime.utcnow().isoformat(),
                        'deleted_by': user_id
                    }
                }
            )
            if result.modified_count == 0:
                raise ValueError(f"Policy {policy_id} not found")
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete policy: {str(e)}")

    async def list_policies(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        List policies with pagination and filtering.
        Args:
            user_id: The UUID of the user requesting the list.
            filters: Optional filters to apply.
            page: Page number (1-based).
            page_size: Number of items per page.
        Returns:
            Dict containing policies and pagination info.
        """
        try:
            # Base query
            query = {'status': 'active'}
            
            # Apply filters
            if filters:
                query.update(filters)

            # Add RLS conditions
            rls_conditions = await self.access_evaluator.get_rls_conditions(user_id)
            if rls_conditions:
                query.update(rls_conditions)

            # Calculate pagination
            skip = (page - 1) * page_size

            # Execute query
            total = await self.db.policies.count_documents(query)
            policies = await self.db.policies.find(
                query,
                {'encrypted_data': 0}  # Exclude encrypted data
            ).skip(skip).limit(page_size).to_list(length=page_size)

            return {
                'items': policies,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        except Exception as e:
            raise RuntimeError(f"Failed to list policies: {str(e)}") 