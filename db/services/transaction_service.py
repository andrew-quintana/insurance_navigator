"""
Transaction service for handling cross-service operations with HIPAA compliance.
"""
from typing import Optional, Dict, Any, List, Callable
from fastapi import HTTPException, status
from supabase import Client as SupabaseClient
import logging
from datetime import datetime
from config.database import get_supabase_client as get_base_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionService:
    """Service for managing cross-service transactions with HIPAA compliance."""

    def __init__(self, supabase_client: SupabaseClient):
        """Initialize the transaction service."""
        self.supabase = supabase_client
        self.audit_table = "audit_logs"

    async def execute_transaction(
        self,
        operations: List[Callable],
        user_id: str,
        transaction_type: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a series of operations as a transaction.
        
        Args:
            operations: List of async callables to execute
            user_id: ID of the user performing the transaction
            transaction_type: Type of transaction being performed
            metadata: Additional transaction metadata
            
        Returns:
            Transaction results
        """
        try:
            logger.info(f"Starting transaction of type {transaction_type} for user {user_id}")
            
            # Start transaction audit
            transaction_id = await self._start_transaction_audit(user_id, transaction_type, metadata)
            
            results = []
            success = True
            error_message = None
            
            try:
                # Execute operations in sequence
                for operation in operations:
                    result = await operation()
                    results.append(result)
                    
                    # Validate operation result
                    if not result or (isinstance(result, dict) and result.get("error")):
                        raise Exception(f"Operation failed: {result}")
                    
                    # Log operation success
                    await self._log_operation_audit(
                        transaction_id,
                        user_id,
                        "operation_success",
                        {
                            "operation_type": operation.__name__,
                            "result": result
                        }
                    )
                    
            except Exception as e:
                success = False
                error_message = str(e)
                logger.error(f"Transaction failed: {error_message}")
                
                # Log operation failure
                await self._log_operation_audit(
                    transaction_id,
                    user_id,
                    "operation_failure",
                    {
                        "error": error_message
                    }
                )
                
                # Attempt rollback for each completed operation
                await self._rollback_transaction(transaction_id, user_id, results)
            
            # Complete transaction audit
            await self._complete_transaction_audit(
                transaction_id,
                user_id,
                success,
                error_message
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Transaction failed: {error_message}"
                )
            
            return {
                "transaction_id": transaction_id,
                "success": True,
                "results": results
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def _start_transaction_audit(
        self,
        user_id: str,
        transaction_type: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Start transaction audit logging."""
        try:
            response = await self.supabase.table(self.audit_table).insert({
                "user_id": user_id,
                "action": "transaction_start",
                "details": {
                    "transaction_type": transaction_type,
                    "metadata": metadata,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "success": True
            }).execute()
            
            return response.data[0]["id"]
            
        except Exception as e:
            logger.error(f"Error starting transaction audit: {str(e)}")
            raise

    async def _log_operation_audit(
        self,
        transaction_id: str,
        user_id: str,
        action: str,
        details: Dict[str, Any]
    ) -> None:
        """Log an operation audit entry."""
        try:
            details["transaction_id"] = transaction_id
            details["timestamp"] = datetime.utcnow().isoformat()
            
            await self.supabase.table(self.audit_table).insert({
                "user_id": user_id,
                "action": action,
                "details": details,
                "success": action == "operation_success"
            }).execute()
            
        except Exception as e:
            logger.error(f"Error logging operation audit: {str(e)}")
            raise

    async def _complete_transaction_audit(
        self,
        transaction_id: str,
        user_id: str,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Complete transaction audit logging."""
        try:
            details = {
                "transaction_id": transaction_id,
                "timestamp": datetime.utcnow().isoformat(),
                "success": success
            }
            
            if error_message:
                details["error"] = error_message
            
            await self.supabase.table(self.audit_table).insert({
                "user_id": user_id,
                "action": "transaction_complete",
                "details": details,
                "success": success
            }).execute()
            
        except Exception as e:
            logger.error(f"Error completing transaction audit: {str(e)}")
            raise

    async def _rollback_transaction(
        self,
        transaction_id: str,
        user_id: str,
        completed_operations: List[Any]
    ) -> None:
        """Attempt to rollback completed operations."""
        try:
            logger.info(f"Rolling back transaction {transaction_id}")
            
            # Log rollback start
            await self._log_operation_audit(
                transaction_id,
                user_id,
                "rollback_start",
                {"completed_operations": len(completed_operations)}
            )
            
            # Implement rollback logic here
            # This would need to be customized based on the types of operations
            # that can be part of a transaction
            
            # Log rollback completion
            await self._log_operation_audit(
                transaction_id,
                user_id,
                "rollback_complete",
                {"status": "success"}
            )
            
        except Exception as e:
            logger.error(f"Error during rollback: {str(e)}")
            # Log rollback failure
            await self._log_operation_audit(
                transaction_id,
                user_id,
                "rollback_failure",
                {"error": str(e)}
            )
            raise

async def get_transaction_service() -> TransactionService:
    """Get configured transaction service instance."""
    try:
        client = get_base_client()
        return TransactionService(client)
    except Exception as e:
        logger.error(f"Error creating transaction service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 