"""
User service module for database operations related to users.
"""
from typing import Optional, Dict, Any, Tuple, List
from fastapi import Depends, HTTPException, status
from supabase import Client as SupabaseClient, create_client
import os
import logging
import json
from datetime import datetime
from config.database import get_supabase_client as get_base_client, get_supabase_service_client
from config.auth_config import auth_config
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserService:
    """Service for managing user data and operations."""

    def __init__(self, db_client: SupabaseClient):
        """Initialize the user service."""
        self.db = db_client
        self.table = "users"
        self.roles_table = "user_roles"
        self.audit_table = "audit_logs"

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by their ID."""
        try:
            logger.info(f"Fetching user with ID: {user_id}")
            
            # Get user from database
            response = self.db.table(self.table).select("*").eq("id", user_id).execute()
            
            # Check if response has data
            if not response.data or len(response.data) == 0:
                logger.warning(f"No user found with ID {user_id}")
                return None
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            return None

    async def create_user(
        self,
        email: str,
        password: str,
        consent_version: str,
        consent_timestamp: str,
        name: str = None
    ) -> Dict[str, Any]:
        """Create a new user with backend-only authentication (no email confirmation)."""
        try:
            logger.info(f"Creating user with email: {email} (backend-only auth)")
            
            # Check if test email is allowed
            if not auth_config.is_test_email_allowed(email):
                raise ValueError(f"Test email addresses not allowed: {email}")
            
            # Get service role client for user creation
            service_client = await get_supabase_service_client()
            logger.info("Service role client obtained successfully")
            
            # Create auth user using service role with auto-confirmation
            auth_settings = auth_config.get_auth_settings()
            logger.info(f"Auth settings: {auth_settings}")
            
            auth_user = service_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": auth_settings['email_confirm'],  # Auto-confirm in development
                "email_confirm_enabled": auth_settings['email_confirm_enabled']
            })
            logger.info(f"Auth user created with ID: {auth_user.user.id}")
            
            # Create user record with HIPAA compliance fields
            user_data = {
                "id": auth_user.user.id,
                "email": email,
                "name": name or email.split("@")[0],
                "consent_version": consent_version,
                "consent_timestamp": consent_timestamp,
                "is_active": True,
                "email_confirmed": True,  # Mark as confirmed since we're bypassing email
                "created_at": datetime.now().isoformat()
            }
            logger.info(f"Inserting user data: {user_data}")
            
            result = service_client.table(self.table).insert(user_data).execute()
            logger.info(f"User record insert result: {result}")
            
            if not result.data:
                raise Exception("Failed to create user record")
            
            logger.info(f"✅ User created successfully: {email}")
            return auth_user
            
        except Exception as e:
            logger.error(f"Error in create_user: {str(e)}")
            # Cleanup on failure
            if "auth_user" in locals() and "service_client" in locals():
                try:
                    service_client.auth.admin.delete_user(auth_user.user.id)
                    logger.info("Cleaned up failed user creation")
                except Exception as cleanup_error:
                    logger.warning(f"Cleanup failed: {cleanup_error}")
            raise Exception(f"Failed to create user: {str(e)}")

    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate a user with email and password.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Dict containing user and session data
            
        Raises:
            Exception: If authentication fails
        """
        try:
            # Log authentication attempt
            logger.info(f"Attempting authentication for user: {email}")
            
            # Authenticate with Supabase
            auth_response = self.db.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not auth_response:
                raise HTTPException(status_code=401, detail="Invalid login credentials")
            
            # Get user data
            user_data = self.get_user_by_id(auth_response.user.id)
            if not user_data:
                raise HTTPException(status_code=401, detail="User not found")
            
            # Update last login
            self.db.table(self.table).update({
                "last_login": datetime.utcnow().isoformat()
            }).eq("id", auth_response.user.id).execute()
            
            # Create audit log
            self.db.table("audit_logs").insert({
                "user_id": auth_response.user.id,
                "action": "user_login",
                "details": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": True
                }
            }).execute()
            
            return {
                "user": {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email
                },
                "session": {
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "expires_at": auth_response.session.expires_at
                }
            }
            
        except Exception as e:
            # Log error
            logger.error(f"Authentication error: {str(e)}")
            
            # Create audit log for failed attempt
            if "auth_response" in locals() and auth_response and hasattr(auth_response, "user"):
                try:
                    self.db.table("audit_logs").insert({
                        "user_id": auth_response.user.id,
                        "action": "user_login",
                        "details": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "success": False,
                            "error": str(e)
                        }
                    }).execute()
                except:
                    pass  # Best effort audit logging
            
            raise HTTPException(status_code=401, detail="Invalid credentials")

    def get_user_from_token(self, token: str, refresh_token: Optional[str] = None, expires_at: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get user data from a JWT token.
        
        Args:
            token: Access token
            refresh_token: Optional refresh token. If provided, will be used to establish a full session.
            expires_at: Optional token expiration timestamp
            
        Returns:
            User data or None if token is invalid
        """
        try:
            # Set auth session with proper session data
            if refresh_token:
                self.db.auth.set_session(token, refresh_token)
            else:
                # For backward compatibility, try with just access token
                self.db.auth.set_session(token, token)  # Use access token as refresh token for compatibility
            
            # Get user from token
            user_response = self.db.auth.get_user()
            
            if not user_response:
                return None
            
            # Get user data from database
            user_data = self.get_user_by_id(user_response.user.id)
            
            # Create audit log
            self.db.table("audit_logs").insert({
                "user_id": user_response.user.id,
                "action": "token_access",
                "details": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": True,
                    "session_type": "full" if refresh_token else "access_only"
                }
            }).execute()
            
            return user_data
            
        except Exception as e:
            # Log error
            logger.error(f"Error getting user from token: {str(e)}")
            
            # Create audit log for failed attempt
            if "user_response" in locals() and user_response and hasattr(user_response.user, "id"):
                try:
                    self.db.table("audit_logs").insert({
                        "user_id": user_response.user.id,
                        "action": "token_access",
                        "details": {
                            "timestamp": datetime.utcnow().isoformat(),
                            "success": False,
                            "error": str(e),
                            "session_type": "full" if refresh_token else "access_only"
                        }
                    }).execute()
                except:
                    pass  # Best effort audit logging
            
            return None

    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a user's data.
        
        Args:
            user_id: The ID of the user to update
            update_data: Dictionary of fields to update
            
        Returns:
            Updated user data or None if update failed
            
        Raises:
            Exception: If update fails
        """
        try:
            # Remove updated_at from update data if present
            if "updated_at" in update_data:
                del update_data["updated_at"]
            
            # Update user record
            result = self.db.table(self.table).update(update_data).eq("id", user_id).execute()
            
            if not result.data:
                return None
            
            # Create audit log
            self.db.table("audit_logs").insert({
                "user_id": user_id,
                "action": "user_update",
                "details": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": True,
                    "fields_updated": list(update_data.keys())
                }
            }).execute()
            
            return result.data[0]
            
        except Exception as e:
            # Log error
            try:
                self.db.table("audit_logs").insert({
                    "user_id": user_id,
                    "action": "user_update",
                    "details": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "success": False,
                        "error": str(e),
                        "fields_attempted": list(update_data.keys())
                    }
                }).execute()
            except:
                pass  # Best effort audit logging
            
            raise Exception(f"Failed to update user: {str(e)}")

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        try:
            logger.info(f"Deleting user: {user_id}")
            result = self.db.table(self.table).delete().eq("id", user_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return False

    def search_users(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for users based on filters."""
        try:
            logger.info(f"Searching users with filters: {filters}")
            query = self.db.table(self.table).select("*")
            for key, value in filters.items():
                query = query.eq(key, value)
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return []

    def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Get roles for a user."""
        try:
            logger.info(f"Fetching roles for user: {user_id}")
            result = self.db.table(self.roles_table).select("role").eq("user_id", user_id).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting roles for user {user_id}: {str(e)}")
            return []

    def update_user_roles(self, user_id: str, roles: List[str], action: str = "add") -> bool:
        """Update roles for a user."""
        try:
            logger.info(f"Adding roles {roles} for user: {user_id}")
            
            if action == "add":
                # Add new roles
                role_data = [{"user_id": user_id, "role": role} for role in roles]
                self.db.table(self.roles_table).insert(role_data).execute()
            elif action == "remove":
                # Remove specified roles
                self.db.table(self.roles_table).delete().eq("user_id", user_id).in_("role", roles).execute()
            elif action == "set":
                # Replace all roles
                self.db.table(self.roles_table).delete().eq("user_id", user_id).execute()
                if roles:
                    role_data = [{"user_id": user_id, "role": role} for role in roles]
                    self.db.table(self.roles_table).insert(role_data).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating roles for user {user_id}: {str(e)}")
            return False

    def create_audit_log(
        self,
        user_id: str,
        action: str,
        details: Dict[str, Any],
        success: bool = True
    ) -> Dict[str, Any]:
        """Create an audit log entry."""
        try:
            log_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "action": action,
                "details": details,
                "success": success,
                "created_at": datetime.utcnow().isoformat()
            }
            result = self.db.table(self.audit_table).insert(log_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            raise Exception(f"Failed to create audit log: {str(e)}")

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user by setting is_active to false.
        
        Args:
            user_id: The ID of the user to deactivate
            
        Returns:
            bool: True if deactivation was successful, False otherwise
        """
        try:
            # Update user record
            result = self.db.table(self.table).update({
                "is_active": False
            }).eq("id", user_id).execute()
            
            if not result.data:
                return False
            
            # Create audit log
            self.db.table("audit_logs").insert({
                "user_id": user_id,
                "action": "user_deactivate",
                "details": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": True
                }
            }).execute()
            
            return True
            
        except Exception as e:
            # Log error
            try:
                self.db.table("audit_logs").insert({
                    "user_id": user_id,
                    "action": "user_deactivate",
                    "details": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "success": False,
                        "error": str(e)
                    }
                }).execute()
            except:
                pass  # Best effort audit logging
            
            return False

async def get_user_service() -> UserService:
    """Get configured user service instance."""
    try:
        client = await get_base_client()
        return UserService(client)
    except Exception as e:
        logger.error(f"Error creating user service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
