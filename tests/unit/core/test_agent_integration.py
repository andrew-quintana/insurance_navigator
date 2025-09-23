"""
Unit tests for core agent integration module.

Tests the AgentIntegrationManager class and related functionality including:
- Agent lifecycle management
- Dependency injection
- Health checking
- Error handling and recovery
- Configuration management
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, Optional

from core.agent_integration import (
    AgentIntegrationManager,
    AgentConfig,
    get_agent_manager,
    initialize_agent_integration,
    close_agent_integration,
    get_agent
)


class MockAgent:
    """Mock agent for testing."""
    
    def __init__(self, name: str = "test_agent", should_fail: bool = False, **kwargs):
        self.name = name
        self.should_fail = should_fail
        self.db_manager = kwargs.get('db_manager')
        self.config = kwargs.get('config')
        self.initialized = False
        self.shutdown_called = False
    
    async def initialize(self):
        """Mock initialization."""
        if self.should_fail:
            raise Exception("Agent initialization failed")
        self.initialized = True
    
    async def shutdown(self):
        """Mock shutdown."""
        self.shutdown_called = True
    
    async def health_check(self):
        """Mock health check."""
        return {
            "status": "unhealthy" if self.should_fail else "healthy",
            "message": "Agent is working" if not self.should_fail else "Agent failed"
        }


class TestAgentConfig:
    """Test AgentConfig dataclass."""
    
    def test_agent_config_creation(self):
        """Test basic agent config creation."""
        config = AgentConfig()
        
        assert config.use_mock is False
        assert config.timeout_seconds == 30
        assert config.retry_attempts == 3
        assert config.enable_health_checks is True
    
    def test_agent_config_custom_values(self):
        """Test agent config with custom values."""
        config = AgentConfig(
            use_mock=True,
            timeout_seconds=60,
            retry_attempts=5,
            enable_health_checks=False
        )
        
        assert config.use_mock is True
        assert config.timeout_seconds == 60
        assert config.retry_attempts == 5
        assert config.enable_health_checks is False


class TestAgentIntegrationManager:
    """Test AgentIntegrationManager class."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        mock_manager = AsyncMock()
        mock_manager.health_check.return_value = {"status": "healthy"}
        return mock_manager
    
    @pytest.fixture
    def agent_config(self):
        """Create an agent configuration."""
        return AgentConfig(
            use_mock=False,
            timeout_seconds=30,
            retry_attempts=3,
            enable_health_checks=True
        )
    
    @pytest.fixture
    def agent_manager(self, mock_db_manager, agent_config):
        """Create an AgentIntegrationManager instance."""
        return AgentIntegrationManager(mock_db_manager, agent_config)
    
    def test_agent_manager_initialization(self, agent_manager, mock_db_manager, agent_config):
        """Test agent manager initialization."""
        assert agent_manager.db_manager == mock_db_manager
        assert agent_manager.config == agent_config
        assert agent_manager._agents == {}
        assert agent_manager._initialized is False
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, agent_manager):
        """Test successful agent manager initialization."""
        with patch.object(agent_manager, '_initialize_core_agents') as mock_init_core:
            await agent_manager.initialize()
            
            assert agent_manager._initialized is True
            mock_init_core.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, agent_manager):
        """Test initialization when already initialized."""
        agent_manager._initialized = True
        
        with patch.object(agent_manager, '_initialize_core_agents') as mock_init_core:
            await agent_manager.initialize()
            
            mock_init_core.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, agent_manager):
        """Test initialization failure."""
        with patch.object(agent_manager, '_initialize_core_agents') as mock_init_core:
            mock_init_core.side_effect = Exception("Core agents failed")
            
            with pytest.raises(Exception, match="Core agents failed"):
                await agent_manager.initialize()
            
            assert agent_manager._initialized is False
    
    @pytest.mark.asyncio
    async def test_get_agent_new_agent(self, agent_manager):
        """Test getting a new agent."""
        agent_manager._initialized = True
        
        result = await agent_manager.get_agent("test_agent", MockAgent, custom_param="value")
        
        assert "test_agent" in agent_manager._agents
        agent = agent_manager._agents["test_agent"]
        assert isinstance(agent, MockAgent)
        assert agent.name == "test_agent"
        assert agent.db_manager == agent_manager.db_manager
        assert agent.config == agent_manager.config
        assert agent.initialized is True
    
    @pytest.mark.asyncio
    async def test_get_agent_existing_agent(self, agent_manager):
        """Test getting an existing agent."""
        agent_manager._initialized = True
        existing_agent = MockAgent("existing")
        agent_manager._agents["existing_agent"] = existing_agent
        
        result = await agent_manager.get_agent("existing_agent", MockAgent)
        
        assert result == existing_agent
    
    @pytest.mark.asyncio
    async def test_get_agent_agent_creation_failure(self, agent_manager):
        """Test agent creation failure."""
        agent_manager._initialized = True
        
        with pytest.raises(Exception, match="Agent creation failed"):
            await agent_manager.get_agent("failing_agent", MockAgent, should_fail=True)
    
    @pytest.mark.asyncio
    async def test_get_agent_without_initialize_method(self, agent_manager):
        """Test getting agent without initialize method."""
        agent_manager._initialized = True
        
        class SimpleAgent:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
        
        result = await agent_manager.get_agent("simple_agent", SimpleAgent)
        
        assert "simple_agent" in agent_manager._agents
        agent = agent_manager._agents["simple_agent"]
        assert isinstance(agent, SimpleAgent)
        assert agent.kwargs["db_manager"] == agent_manager.db_manager
        assert agent.kwargs["config"] == agent_manager.config
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, agent_manager):
        """Test health check when all agents are healthy."""
        agent_manager._initialized = True
        
        # Add healthy agents
        healthy_agent1 = MockAgent("healthy1")
        healthy_agent2 = MockAgent("healthy2")
        agent_manager._agents["agent1"] = healthy_agent1
        agent_manager._agents["agent2"] = healthy_agent2
        
        result = await agent_manager.health_check()
        
        assert result["status"] == "healthy"
        assert "agents" in result
        assert "dependencies" in result
        assert result["dependencies"]["database"]["status"] == "healthy"
        assert result["agents"]["agent1"]["status"] == "healthy"
        assert result["agents"]["agent2"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy_database(self, agent_manager, mock_db_manager):
        """Test health check when database is unhealthy."""
        agent_manager._initialized = True
        mock_db_manager.health_check.return_value = {"status": "unhealthy", "error": "DB down"}
        
        result = await agent_manager.health_check()
        
        assert result["status"] == "unhealthy"
        assert result["dependencies"]["database"]["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy_agent(self, agent_manager):
        """Test health check when agent is unhealthy."""
        agent_manager._initialized = True
        
        # Add unhealthy agent
        unhealthy_agent = MockAgent("unhealthy", should_fail=True)
        agent_manager._agents["unhealthy_agent"] = unhealthy_agent
        
        result = await agent_manager.health_check()
        
        assert result["status"] == "unhealthy"
        assert result["agents"]["unhealthy_agent"]["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_health_check_agent_without_health_check(self, agent_manager):
        """Test health check with agent that has no health check method."""
        agent_manager._initialized = True
        
        class NoHealthCheckAgent:
            def __init__(self, **kwargs):
                pass
        
        agent = NoHealthCheckAgent()
        agent_manager._agents["no_health_agent"] = agent
        
        result = await agent_manager.health_check()
        
        assert result["status"] == "healthy"
        assert result["agents"]["no_health_agent"]["status"] == "unknown"
        assert "No health check method" in result["agents"]["no_health_agent"]["message"]
    
    @pytest.mark.asyncio
    async def test_health_check_agent_exception(self, agent_manager):
        """Test health check when agent raises exception."""
        agent_manager._initialized = True
        
        class ExceptionAgent:
            async def health_check(self):
                raise Exception("Health check failed")
        
        agent = ExceptionAgent()
        agent_manager._agents["exception_agent"] = agent
        
        result = await agent_manager.health_check()
        
        assert result["status"] == "unhealthy"
        assert result["agents"]["exception_agent"]["status"] == "unhealthy"
        assert "Health check failed" in result["agents"]["exception_agent"]["error"]
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, agent_manager, mock_db_manager):
        """Test health check when manager raises exception."""
        agent_manager._initialized = True
        mock_db_manager.health_check.side_effect = Exception("Manager error")
        
        result = await agent_manager.health_check()
        
        assert result["status"] == "unhealthy"
        assert "Manager error" in result["error"]
        assert result["agents"] == {}
        assert result["dependencies"] == {}
    
    @pytest.mark.asyncio
    async def test_shutdown_success(self, agent_manager):
        """Test successful shutdown."""
        agent_manager._initialized = True
        
        # Add agents
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")
        agent_manager._agents["agent1"] = agent1
        agent_manager._agents["agent2"] = agent2
        
        await agent_manager.shutdown()
        
        assert agent_manager._initialized is False
        assert agent_manager._agents == {}
        assert agent1.shutdown_called is True
        assert agent2.shutdown_called is True
    
    @pytest.mark.asyncio
    async def test_shutdown_agent_without_shutdown_method(self, agent_manager):
        """Test shutdown with agent that has no shutdown method."""
        agent_manager._initialized = True
        
        class NoShutdownAgent:
            def __init__(self, **kwargs):
                pass
        
        agent = NoShutdownAgent()
        agent_manager._agents["no_shutdown_agent"] = agent
        
        # Should not raise exception
        await agent_manager.shutdown()
        
        assert agent_manager._initialized is False
        assert agent_manager._agents == {}
    
    @pytest.mark.asyncio
    async def test_shutdown_agent_exception(self, agent_manager):
        """Test shutdown when agent raises exception."""
        agent_manager._initialized = True
        
        class ExceptionAgent:
            async def shutdown(self):
                raise Exception("Shutdown failed")
        
        agent = ExceptionAgent()
        agent_manager._agents["exception_agent"] = agent
        
        # Should not raise exception, but log error
        await agent_manager.shutdown()
        
        assert agent_manager._initialized is False
        assert agent_manager._agents == {}
    
    @pytest.mark.asyncio
    async def test_initialize_core_agents_success(self, agent_manager):
        """Test successful core agents initialization."""
        with patch('core.agent_integration.BaseAgent') as mock_base_agent:
            await agent_manager._initialize_core_agents()
            
            # Should not raise exception
            assert True
    
    @pytest.mark.asyncio
    async def test_initialize_core_agents_import_error(self, agent_manager):
        """Test core agents initialization with import error."""
        with patch('core.agent_integration.BaseAgent', side_effect=ImportError("Module not found")):
            # Should not raise exception, just log warning
            await agent_manager._initialize_core_agents()
            
            assert True


class TestGlobalAgentIntegration:
    """Test global agent integration functions."""
    
    @pytest.mark.asyncio
    async def test_initialize_agent_integration_success(self):
        """Test successful agent integration initialization."""
        mock_db_manager = AsyncMock()
        
        with patch('core.agent_integration.get_database_manager', return_value=mock_db_manager):
            with patch.dict(os.environ, {
                'AGENT_MOCK_MODE': 'false',
                'AGENT_TIMEOUT_SECONDS': '60',
                'AGENT_RETRY_ATTEMPTS': '5',
                'AGENT_HEALTH_CHECKS': 'true'
            }):
                manager = await initialize_agent_integration()
                
                assert isinstance(manager, AgentIntegrationManager)
                assert manager.db_manager == mock_db_manager
                assert manager.config.use_mock is False
                assert manager.config.timeout_seconds == 60
                assert manager.config.retry_attempts == 5
                assert manager.config.enable_health_checks is True
    
    @pytest.mark.asyncio
    async def test_initialize_agent_integration_already_initialized(self):
        """Test agent integration initialization when already initialized."""
        mock_manager = AsyncMock()
        
        with patch('core.agent_integration._agent_manager', mock_manager):
            result = await initialize_agent_integration()
            
            assert result == mock_manager
    
    @pytest.mark.asyncio
    async def test_get_agent_manager_not_initialized(self):
        """Test getting agent manager when not initialized."""
        with patch('core.agent_integration._agent_manager', None):
            with pytest.raises(RuntimeError, match="Agent integration manager not initialized"):
                await get_agent_manager()
    
    @pytest.mark.asyncio
    async def test_get_agent_manager_success(self):
        """Test getting initialized agent manager."""
        mock_manager = AsyncMock()
        
        with patch('core.agent_integration._agent_manager', mock_manager):
            result = await get_agent_manager()
            
            assert result == mock_manager
    
    @pytest.mark.asyncio
    async def test_close_agent_integration(self):
        """Test closing agent integration."""
        mock_manager = AsyncMock()
        
        with patch('core.agent_integration._agent_manager', mock_manager):
            await close_agent_integration()
            
            mock_manager.shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_agent_integration_none(self):
        """Test closing agent integration when manager is None."""
        with patch('core.agent_integration._agent_manager', None):
            await close_agent_integration()  # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_get_agent_global(self):
        """Test getting agent from global manager."""
        mock_manager = AsyncMock()
        mock_agent = MockAgent("global_agent")
        mock_manager.get_agent.return_value = mock_agent
        
        with patch('core.agent_integration.get_agent_manager', return_value=mock_manager):
            result = await get_agent("global_agent", MockAgent, param="value")
            
            assert result == mock_agent
            mock_manager.get_agent.assert_called_once_with("global_agent", MockAgent, param="value")


class TestAgentIntegrationIntegration:
    """Integration tests for AgentIntegrationManager."""
    
    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self):
        """Test complete agent lifecycle."""
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy"}
        
        config = AgentConfig()
        manager = AgentIntegrationManager(mock_db_manager, config)
        
        # Initialize
        await manager.initialize()
        assert manager._initialized is True
        
        # Create agents
        agent1 = await manager.get_agent("agent1", MockAgent)
        agent2 = await manager.get_agent("agent2", MockAgent)
        
        assert agent1.initialized is True
        assert agent2.initialized is True
        assert agent1.db_manager == mock_db_manager
        assert agent1.config == config
        
        # Health check
        health = await manager.health_check()
        assert health["status"] == "healthy"
        assert "agent1" in health["agents"]
        assert "agent2" in health["agents"]
        
        # Shutdown
        await manager.shutdown()
        assert manager._initialized is False
        assert manager._agents == {}
        assert agent1.shutdown_called is True
        assert agent2.shutdown_called is True
    
    @pytest.mark.asyncio
    async def test_agent_dependency_injection(self):
        """Test agent dependency injection."""
        mock_db_manager = AsyncMock()
        config = AgentConfig(use_mock=True, timeout_seconds=60)
        manager = AgentIntegrationManager(mock_db_manager, config)
        await manager.initialize()
        
        # Create agent with custom parameters
        agent = await manager.get_agent(
            "test_agent", 
            MockAgent, 
            custom_param="custom_value"
        )
        
        # Verify dependencies were injected
        assert agent.db_manager == mock_db_manager
        assert agent.config == config
        assert agent.initialized is True
    
    @pytest.mark.asyncio
    async def test_multiple_agent_management(self):
        """Test managing multiple agents."""
        mock_db_manager = AsyncMock()
        mock_db_manager.health_check.return_value = {"status": "healthy"}
        
        manager = AgentIntegrationManager(mock_db_manager, AgentConfig())
        await manager.initialize()
        
        # Create multiple agents
        agents = []
        for i in range(5):
            agent = await manager.get_agent(f"agent_{i}", MockAgent)
            agents.append(agent)
        
        # Verify all agents are managed
        assert len(manager._agents) == 5
        for i in range(5):
            assert f"agent_{i}" in manager._agents
            assert manager._agents[f"agent_{i}"] == agents[i]
        
        # Health check all agents
        health = await manager.health_check()
        assert health["status"] == "healthy"
        assert len(health["agents"]) == 5
        
        # Shutdown all agents
        await manager.shutdown()
        for agent in agents:
            assert agent.shutdown_called is True


if __name__ == "__main__":
    pytest.main([__file__])
