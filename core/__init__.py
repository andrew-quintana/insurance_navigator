"""
Core Module - Centralized System Initialization

This module provides the centralized initialization system for the Insurance Navigator
application, implementing the dependency injection pattern and resolving import
management issues as part of Phase 1 of the Agent Integration Infrastructure Refactor.

Key Features:
- Explicit module initialization order
- Dependency injection for all core services
- Graceful error handling and validation
- Environment-specific configuration
- Health monitoring and observability
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from .database import DatabaseManager, initialize_database, close_database, get_database_manager
from .agent_integration import AgentIntegrationManager, initialize_agent_integration, close_agent_integration, get_agent_manager

logger = logging.getLogger(__name__)


class SystemManager:
    """
    Central system manager for the Insurance Navigator application.
    
    This class coordinates the initialization and lifecycle of all core services,
    ensuring proper dependency injection and error handling.
    """
    
    def __init__(self):
        self.db_manager: Optional[DatabaseManager] = None
        self.agent_manager: Optional[AgentIntegrationManager] = None
        self._initialized = False
        self._initialization_order = [
            "database",
            "agent_integration"
        ]
    
    async def initialize(self) -> None:
        """Initialize all core services in the correct order."""
        if self._initialized:
            logger.warning("System already initialized")
            return
        
        try:
            logger.info("Initializing Insurance Navigator system")
            
            # Initialize services in dependency order
            for service in self._initialization_order:
                await self._initialize_service(service)
            
            self._initialized = True
            logger.info("System initialization completed successfully")
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Shutdown all services in reverse order."""
        logger.info("Shutting down Insurance Navigator system")
        
        try:
            # Shutdown services in reverse order
            for service in reversed(self._initialization_order):
                await self._shutdown_service(service)
            
            self._initialized = False
            logger.info("System shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during system shutdown: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check on all services."""
        if not self._initialized:
            return {"status": "unhealthy", "error": "System not initialized"}
        
        health_status = {
            "status": "healthy",
            "services": {},
            "overall_status": "healthy"
        }
        
        try:
            # Check database health
            if self.db_manager:
                db_health = await self.db_manager.health_check()
                health_status["services"]["database"] = db_health
                
                if db_health["status"] != "healthy":
                    health_status["overall_status"] = "unhealthy"
            
            # Check agent integration health
            if self.agent_manager:
                agent_health = await self.agent_manager.health_check()
                health_status["services"]["agent_integration"] = agent_health
                
                if agent_health["status"] != "healthy":
                    health_status["overall_status"] = "unhealthy"
            
            health_status["status"] = health_status["overall_status"]
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "services": {},
                "overall_status": "unhealthy"
            }
    
    async def _initialize_service(self, service_name: str) -> None:
        """Initialize a specific service."""
        logger.info(f"Initializing service: {service_name}")
        
        if service_name == "database":
            self.db_manager = await initialize_database()
            logger.info("Database service initialized")
            
        elif service_name == "agent_integration":
            if not self.db_manager:
                raise RuntimeError("Database manager must be initialized before agent integration")
            self.agent_manager = await initialize_agent_integration()
            logger.info("Agent integration service initialized")
            
        else:
            raise ValueError(f"Unknown service: {service_name}")
    
    async def _shutdown_service(self, service_name: str) -> None:
        """Shutdown a specific service."""
        logger.info(f"Shutting down service: {service_name}")
        
        if service_name == "agent_integration" and self.agent_manager:
            await close_agent_integration()
            self.agent_manager = None
            logger.info("Agent integration service shutdown")
            
        elif service_name == "database" and self.db_manager:
            await close_database()
            self.db_manager = None
            logger.info("Database service shutdown")


# Global system manager instance
_system_manager: Optional[SystemManager] = None


async def get_system_manager() -> SystemManager:
    """Get the global system manager instance."""
    global _system_manager
    if _system_manager is None:
        raise RuntimeError("System manager not initialized. Call initialize_system() first.")
    return _system_manager


async def initialize_system() -> SystemManager:
    """Initialize the global system manager."""
    global _system_manager
    if _system_manager is not None:
        logger.warning("System manager already initialized")
        return _system_manager
    
    _system_manager = SystemManager()
    await _system_manager.initialize()
    return _system_manager


async def close_system() -> None:
    """Close the global system manager."""
    global _system_manager
    if _system_manager:
        await _system_manager.shutdown()
        _system_manager = None


@asynccontextmanager
async def system_context():
    """Context manager for system initialization and cleanup."""
    system = await initialize_system()
    try:
        yield system
    finally:
        await close_system()


# Convenience functions for accessing services
async def get_database() -> DatabaseManager:
    """Get the database manager."""
    system = await get_system_manager()
    if not system.db_manager:
        raise RuntimeError("Database manager not available")
    return system.db_manager


async def get_agents() -> AgentIntegrationManager:
    """Get the agent integration manager."""
    system = await get_system_manager()
    if not system.agent_manager:
        raise RuntimeError("Agent integration manager not available")
    return system.agent_manager


# Module-level initialization validation
def validate_imports() -> bool:
    """
    Validate that all required imports are available.
    
    This function should be called during module initialization to ensure
    all dependencies are properly resolved.
    """
    try:
        # Test critical imports
        import asyncpg
        import pydantic
        import logging
        
        # Test database configuration
        from .database import create_database_config
        config = create_database_config()
        
        logger.info("Import validation successful")
        return True
        
    except ImportError as e:
        logger.error(f"Import validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Validate imports on module load
if not validate_imports():
    raise RuntimeError("Core module import validation failed")
