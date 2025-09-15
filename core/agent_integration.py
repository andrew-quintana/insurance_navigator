"""
Agent Integration Manager

This module provides centralized coordination for all agent operations,
implementing the dependency injection pattern for Phase 1 of the Agent
Integration Infrastructure Refactor.

Key Features:
- Centralized agent lifecycle management
- Dependency injection for database and external services
- Graceful error handling and fallback mechanisms
- Environment-specific configuration
- Health monitoring and observability
"""

import os
import logging
from typing import Optional, Dict, Any, Type, Callable
from dataclasses import dataclass

from .database import DatabaseManager, get_database_manager


logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for agent integration."""
    use_mock: bool = False
    timeout_seconds: int = 30
    retry_attempts: int = 3
    enable_health_checks: bool = True


class AgentIntegrationManager:
    """
    Central coordinator for all agent operations.
    
    This class implements the dependency injection pattern, providing
    a single point of control for agent initialization, configuration,
    and lifecycle management.
    """
    
    def __init__(self, db_manager: DatabaseManager, config: AgentConfig = None):
        self.db_manager = db_manager
        self.config = config or AgentConfig()
        self._agents: Dict[str, Any] = {}
        self._initialized = False
        
    async def initialize(self) -> None:
        """Initialize the agent integration manager."""
        if self._initialized:
            logger.warning("Agent integration manager already initialized")
            return
        
        try:
            logger.info("Initializing agent integration manager")
            
            # Initialize core agents
            await self._initialize_core_agents()
            
            self._initialized = True
            logger.info("Agent integration manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent integration manager: {e}")
            raise
    
    async def get_agent(self, agent_name: str, agent_class: Type, **kwargs) -> Any:
        """
        Get or create an agent instance with dependency injection.
        
        Args:
            agent_name: Unique name for the agent
            agent_class: Agent class to instantiate
            **kwargs: Additional arguments for agent initialization
            
        Returns:
            Agent instance with injected dependencies
        """
        if agent_name in self._agents:
            return self._agents[agent_name]
        
        try:
            # Inject database manager and configuration
            agent_kwargs = {
                'db_manager': self.db_manager,
                'config': self.config,
                **kwargs
            }
            
            # Create agent instance
            agent = agent_class(**agent_kwargs)
            
            # Initialize agent if it has an initialize method
            if hasattr(agent, 'initialize'):
                await agent.initialize()
            
            self._agents[agent_name] = agent
            logger.info(f"Created agent: {agent_name}")
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_name}: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents and dependencies."""
        health_status = {
            "status": "healthy",
            "agents": {},
            "dependencies": {}
        }
        
        try:
            # Check database health
            db_health = await self.db_manager.health_check()
            health_status["dependencies"]["database"] = db_health
            
            if db_health["status"] != "healthy":
                health_status["status"] = "unhealthy"
            
            # Check agent health
            for agent_name, agent in self._agents.items():
                try:
                    if hasattr(agent, 'health_check'):
                        agent_health = await agent.health_check()
                    else:
                        agent_health = {"status": "unknown", "message": "No health check method"}
                    
                    health_status["agents"][agent_name] = agent_health
                    
                    if agent_health.get("status") == "unhealthy":
                        health_status["status"] = "unhealthy"
                        
                except Exception as e:
                    health_status["agents"][agent_name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    health_status["status"] = "unhealthy"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "agents": {},
                "dependencies": {}
            }
    
    async def shutdown(self) -> None:
        """Shutdown all agents and cleanup resources."""
        logger.info("Shutting down agent integration manager")
        
        # Shutdown all agents
        for agent_name, agent in self._agents.items():
            try:
                if hasattr(agent, 'shutdown'):
                    await agent.shutdown()
                logger.info(f"Shutdown agent: {agent_name}")
            except Exception as e:
                logger.error(f"Error shutting down agent {agent_name}: {e}")
        
        self._agents.clear()
        self._initialized = False
        logger.info("Agent integration manager shutdown complete")
    
    async def _initialize_core_agents(self) -> None:
        """Initialize core agents that are always needed."""
        try:
            # Import agents dynamically to avoid circular imports
            from agents.base_agent import BaseAgent
            
            # Initialize base agent registry
            logger.info("Core agents initialized")
            
        except ImportError as e:
            logger.warning(f"Could not import core agents: {e}")
            # This is expected during development when agents are not fully implemented


# Global agent integration manager instance
_agent_manager: Optional[AgentIntegrationManager] = None


async def get_agent_manager() -> AgentIntegrationManager:
    """Get the global agent integration manager instance."""
    global _agent_manager
    if _agent_manager is None:
        raise RuntimeError("Agent integration manager not initialized. Call initialize_agent_integration() first.")
    return _agent_manager


async def initialize_agent_integration() -> AgentIntegrationManager:
    """Initialize the global agent integration manager."""
    global _agent_manager
    if _agent_manager is not None:
        logger.warning("Agent integration manager already initialized")
        return _agent_manager
    
    # Get database manager
    db_manager = await get_database_manager()
    
    # Create agent configuration
    config = AgentConfig(
        use_mock=os.getenv("AGENT_MOCK_MODE", "false").lower() == "true",
        timeout_seconds=int(os.getenv("AGENT_TIMEOUT_SECONDS", "30")),
        retry_attempts=int(os.getenv("AGENT_RETRY_ATTEMPTS", "3")),
        enable_health_checks=os.getenv("AGENT_HEALTH_CHECKS", "true").lower() == "true"
    )
    
    _agent_manager = AgentIntegrationManager(db_manager, config)
    await _agent_manager.initialize()
    return _agent_manager


async def close_agent_integration() -> None:
    """Close the global agent integration manager."""
    global _agent_manager
    if _agent_manager:
        await _agent_manager.shutdown()
        _agent_manager = None


# Convenience function for getting agents
async def get_agent(agent_name: str, agent_class: Type, **kwargs) -> Any:
    """Get an agent instance from the global manager."""
    manager = await get_agent_manager()
    return await manager.get_agent(agent_name, agent_class, **kwargs)
