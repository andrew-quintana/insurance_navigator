"""
User service for database operations with Supabase PostgreSQL.
Handles user registration, authentication, and role management.
"""

import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
import jwt
import asyncpg

from .db_pool import get_db_pool, get_db_session
from ..config import config
from utils.security_config import get_security_config

logger = logging.getLogger(__name__)

# Security configuration
security_config = get_security_config()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = security_config.jwt_secret_key
ALGORITHM = security_config.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = security_config.access_token_expire_minutes

class UserService:
    """Service for user-related database operations."""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async def create_user(
        self, 
        email: str, 
        password: str, 
        full_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new user in the database."""
        try:
            # Hash password
            hashed_password = self.pwd_context.hash(password)
            user_id = uuid.uuid4()
            
            pool = await get_db_pool()
            
            async with pool.acquire() as conn:
                async with conn.transaction():
                    # Check if user already exists
                    existing_user = await conn.fetchrow(
                        "SELECT id FROM auth.users WHERE email = $1",
                        email
                    )
                    
                    if existing_user:
                        raise ValueError("User with this email already exists")
                    
                    # Insert new user into auth.users
                    await conn.execute(
                        """
                        INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, confirmed_at)
                        VALUES ($1, $2, $3, NOW(), NOW())
                        """,
                        user_id, email, hashed_password
                    )
                    
                    # Create user profile
                    await conn.execute(
                        """
                        INSERT INTO public.user_profiles (user_id, full_name, metadata)
                        VALUES ($1, $2, $3)
                        """,
                        user_id, full_name, json.dumps(metadata or {})
                    )
                    
                    # Get default role ID
                    role_row = await conn.fetchrow(
                        "SELECT id FROM public.roles WHERE name = 'user'"
                    )
                    
                    if role_row:
                        # Assign default role
                        await conn.execute(
                            """
                            INSERT INTO public.user_roles (user_id, role_id)
                            VALUES ($1, $2)
                            ON CONFLICT (user_id, role_id) DO NOTHING
                            """,
                            user_id, role_row['id']
                        )
                    
                    # Get complete user data
                    user_data = await conn.fetchrow(
                        """
                        SELECT 
                            u.id,
                            u.email,
                            p.full_name,
                            p.created_at,
                            p.metadata,
                            array_agg(r.name) as roles
                        FROM auth.users u
                        JOIN public.user_profiles p ON p.user_id = u.id
                        LEFT JOIN public.user_roles ur ON ur.user_id = u.id
                        LEFT JOIN public.roles r ON r.id = ur.role_id
                        WHERE u.id = $1
                        GROUP BY u.id, u.email, p.full_name, p.created_at, p.metadata
                        """,
                        user_id
                    )
                    
                    logger.info(f"Created user: {email} with ID: {user_id}")
                    
                    return {
                        "id": str(user_data["id"]),
                        "email": user_data["email"],
                        "full_name": user_data["full_name"],
                        "created_at": user_data["created_at"],
                        "roles": user_data["roles"] or []
                    }
                
        except Exception as e:
            logger.error(f"Failed to create user {email}: {str(e)}")
            raise
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password and return JWT token and user data."""
        try:
            pool = await get_db_pool()
            
            async with pool.acquire() as conn:
                # Get user with password hash
                user_row = await conn.fetchrow(
                    """
                    SELECT 
                        u.id,
                        u.email,
                        u.encrypted_password,
                        p.full_name,
                        p.last_login,
                        array_agg(r.name) as roles
                    FROM auth.users u
                    JOIN public.user_profiles p ON p.user_id = u.id
                    LEFT JOIN public.user_roles ur ON ur.user_id = u.id
                    LEFT JOIN public.roles r ON r.id = ur.role_id
                    WHERE u.email = $1
                    GROUP BY u.id, u.email, u.encrypted_password, p.full_name, p.last_login
                    """,
                    email
                )
                
                if not user_row:
                    logger.warning(f"Authentication failed - user not found: {email}")
                    return None
                
                # Verify password
                if not self.pwd_context.verify(password, user_row["encrypted_password"]):
                    logger.warning(f"Authentication failed - invalid password: {email}")
                    return None
                
                # Update last login time
                await conn.execute(
                    "UPDATE public.user_profiles SET last_login = NOW() WHERE user_id = $1",
                    user_row["id"]
                )
                
                user_data = {
                    "id": str(user_row["id"]),
                    "email": user_row["email"],
                    "full_name": user_row["full_name"],
                    "last_login": user_row["last_login"],
                    "roles": user_row["roles"] or []
                }
                
                # Create JWT token
                access_token = self.create_access_token(user_data)
                
                logger.info(f"User authenticated successfully: {email}")
                
                return {
                    "access_token": access_token,
                    "user": user_data
                }
                
        except Exception as e:
            logger.error(f"Authentication error for {email}: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        try:
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                user_row = await conn.fetchrow(
                    """
                    SELECT u.id, u.email, p.full_name, p.created_at, p.updated_at, 
                           p.last_login, p.metadata
                    FROM auth.users u
                    JOIN public.user_profiles p ON p.user_id = u.id
                    WHERE u.email = $1 AND u.confirmed_at IS NOT NULL
                    """,
                    email
                )
                
                if not user_row:
                    return None
                
                # Get user roles
                user_roles = await self._get_user_roles(conn, user_row["id"])
                
                return {
                    "id": str(user_row["id"]),
                    "email": user_row["email"],
                    "full_name": user_row["full_name"],
                    "created_at": user_row["created_at"],
                    "updated_at": user_row["updated_at"],
                    "last_login": user_row["last_login"],
                    "metadata": json.loads(user_row["metadata"]) if user_row["metadata"] else {},
                    "roles": user_roles
                }
                
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                user_row = await conn.fetchrow(
                    """
                    SELECT u.id, u.email, p.full_name, p.created_at, p.updated_at, 
                           p.last_login, p.metadata
                    FROM auth.users u
                    JOIN public.user_profiles p ON p.user_id = u.id
                    WHERE u.id = $1 AND u.confirmed_at IS NOT NULL
                    """,
                    uuid.UUID(user_id)
                )
                
                if not user_row:
                    return None
                
                # Get user roles
                user_roles = await self._get_user_roles(conn, user_row["id"])
                
                return {
                    "id": str(user_row["id"]),
                    "email": user_row["email"],
                    "full_name": user_row["full_name"],
                    "created_at": user_row["created_at"],
                    "updated_at": user_row["updated_at"],
                    "last_login": user_row["last_login"],
                    "metadata": json.loads(user_row["metadata"]) if user_row["metadata"] else {},
                    "roles": user_roles
                }
                
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            return None
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update user information."""
        try:
            pool = await get_db_pool()
            
            # Prepare update fields
            allowed_fields = ['full_name', 'metadata']
            update_fields = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not update_fields:
                raise ValueError("No valid fields to update")
            
            # Build dynamic update query
            set_clauses = []
            values = []
            param_count = 1
            
            for field, value in update_fields.items():
                set_clauses.append(f"{field} = ${param_count}")
                values.append(value)
                param_count += 1
            
            # Add updated_at
            set_clauses.append(f"updated_at = ${param_count}")
            values.append(datetime.utcnow())
            param_count += 1
            
            # Add user_id to values
            values.append(uuid.UUID(user_id))
            
            async with pool.get_connection() as conn:
                # Update user profile
                updated_row = await conn.fetchrow(
                    f"""
                    UPDATE public.user_profiles
                    SET {', '.join(set_clauses)}
                    WHERE user_id = ${param_count}
                    RETURNING id, full_name, updated_at, metadata
                    """,
                    *values
                )
                
                if not updated_row:
                    return None
                
                return {
                    "id": str(updated_row["id"]),
                    "full_name": updated_row["full_name"],
                    "updated_at": updated_row["updated_at"],
                    "metadata": json.loads(updated_row["metadata"]) if updated_row["metadata"] else {}
                }
                
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            raise
    
    async def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign a role to a user."""
        try:
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                # Get role ID
                role_row = await conn.fetchrow(
                    "SELECT id FROM roles WHERE name = $1",
                    role_name
                )
                
                if not role_row:
                    raise ValueError(f"Role '{role_name}' not found")
                
                # Assign role (ignore if already assigned)
                await conn.execute(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id, role_id) DO NOTHING
                    """,
                    uuid.UUID(user_id), role_row["id"]
                )
                
                logger.info(f"Assigned role '{role_name}' to user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error assigning role {role_name} to user {user_id}: {str(e)}")
            return False
    
    async def remove_role(self, user_id: str, role_name: str) -> bool:
        """Remove a role from a user."""
        try:
            pool = await get_db_pool()
            
            async with pool.get_connection() as conn:
                # Get role ID
                role_row = await conn.fetchrow(
                    "SELECT id FROM roles WHERE name = $1",
                    role_name
                )
                
                if not role_row:
                    return False
                
                # Remove role assignment
                result = await conn.execute(
                    "DELETE FROM user_roles WHERE user_id = $1 AND role_id = $2",
                    uuid.UUID(user_id), role_row["id"]
                )
                
                logger.info(f"Removed role '{role_name}' from user {user_id}")
                return "DELETE" in result
                
        except Exception as e:
            logger.error(f"Error removing role {role_name} from user {user_id}: {str(e)}")
            return False
    
    async def _get_user_roles(self, conn: asyncpg.Connection, user_id: uuid.UUID) -> List[str]:
        """Get all roles for a user."""
        role_rows = await conn.fetch(
            """
            SELECT r.name 
            FROM roles r 
            JOIN user_roles ur ON r.id = ur.role_id 
            WHERE ur.user_id = $1
            """,
            user_id
        )
        return [row["name"] for row in role_rows]
    
    async def _assign_default_role(self, conn: asyncpg.Connection, user_id: uuid.UUID) -> None:
        """Assign default 'user' role to new user."""
        try:
            # Get 'user' role ID
            role_row = await conn.fetchrow(
                "SELECT id FROM roles WHERE name = 'user'"
            )
            
            if role_row:
                await conn.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
                    user_id, role_row["id"]
                )
                logger.info(f"Assigned default 'user' role to user {user_id}")
            else:
                logger.warning("Default 'user' role not found in database")
                
        except Exception as e:
            logger.error(f"Error assigning default role to user {user_id}: {str(e)}")
            # Don't raise - user creation should still succeed
    
    # Authentication helper methods
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token for user."""
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user_data["email"],
            "user_id": user_data["id"],
            "roles": user_data.get("roles", []),
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise ValueError("Invalid token")
    
    async def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate user session token and return user data."""
        try:
            payload = self.verify_token(token)
            email = payload.get("sub")
            
            if not email:
                return None
            
            # Get fresh user data from database
            user_data = await self.get_user_by_email(email)
            if not user_data or not user_data["is_active"]:
                return None
            
            return user_data
            
        except ValueError:
            return None

    async def register_user(self, email: str, password: str, full_name: str) -> str:
        """Register a new user and return JWT token (expected by main.py)."""
        try:
            # Create user in database
            user_data = await self.create_user(email, password, full_name)
            
            # Create and return JWT token
            token = self.create_access_token(user_data)
            return token
            
        except Exception as e:
            logger.error(f"Failed to register user {email}: {str(e)}")
            raise

    async def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user data from JWT token (expected by main.py)."""
        return await self.validate_session(token)

# Global user service instance
user_service = UserService()

async def get_user_service() -> UserService:
    """Get the global user service instance."""
    return user_service 