"""
Tests for Unified Navigator Agent.

This module provides comprehensive tests for the unified navigator agent,
including unit tests for individual components and integration tests.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from ..navigator_agent import UnifiedNavigatorAgent
from ..models import (
    UnifiedNavigatorInput,
    UnifiedNavigatorOutput,
    ToolType,
    SafetyLevel
)
from ..config import UnifiedNavigatorConfig


class TestUnifiedNavigatorAgent:
    """Test cases for UnifiedNavigatorAgent."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = UnifiedNavigatorConfig()
        config.anthropic_api_key = "test_key"
        config.web_search_config.api_key = "test_brave_key"
        return config
    
    @pytest.fixture
    def navigator_agent(self, mock_config):
        """Create navigator agent for testing."""
        with patch('agents.unified_navigator.config.get_config', return_value=mock_config):
            agent = UnifiedNavigatorAgent(use_mock=True)
            return agent
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, navigator_agent):
        """Test agent initialization."""
        assert navigator_agent.name == "unified_navigator"
        assert navigator_agent.workflow is not None
        assert hasattr(navigator_agent, 'tool_weights')
    
    @pytest.mark.asyncio
    async def test_basic_execution_mock_mode(self, navigator_agent):
        """Test basic execution in mock mode."""
        input_data = UnifiedNavigatorInput(
            user_query="What is my insurance coverage?",
            user_id="test_user_123"
        )
        
        output = await navigator_agent.execute(input_data)
        
        assert isinstance(output, UnifiedNavigatorOutput)
        assert output.user_id == "test_user_123"
        assert output.response is not None
        assert len(output.response) > 0
        assert output.tool_used in [ToolType.WEB_SEARCH, ToolType.RAG_SEARCH, ToolType.COMBINED]
    
    @pytest.mark.asyncio 
    async def test_input_sanitization_safe_query(self, navigator_agent):
        """Test input sanitization with safe query."""
        input_data = UnifiedNavigatorInput(
            user_query="What is my insurance deductible?",
            user_id="test_user_123"
        )
        
        output = await navigator_agent.execute(input_data)
        
        assert output.success
        assert output.input_safety_check.is_safe
        assert output.input_safety_check.safety_level in [SafetyLevel.SAFE, SafetyLevel.UNCERTAIN]
    
    @pytest.mark.asyncio
    async def test_input_sanitization_unsafe_query(self, navigator_agent):
        """Test input sanitization with unsafe query."""
        input_data = UnifiedNavigatorInput(
            user_query="How to hack into insurance systems?",
            user_id="test_user_123"
        )
        
        output = await navigator_agent.execute(input_data)
        
        # Should still complete but with appropriate handling
        assert isinstance(output, UnifiedNavigatorOutput)
        assert output.user_id == "test_user_123"
    
    @pytest.mark.asyncio
    async def test_tool_selection_web_search(self, navigator_agent):
        """Test tool selection for web search queries."""
        input_data = UnifiedNavigatorInput(
            user_query="What are the latest insurance regulations in 2025?",
            user_id="test_user_123"
        )
        
        output = await navigator_agent.execute(input_data)
        
        assert output.tool_used in [ToolType.WEB_SEARCH, ToolType.COMBINED]
    
    @pytest.mark.asyncio
    async def test_tool_selection_rag_search(self, navigator_agent):
        """Test tool selection for RAG search queries."""
        input_data = UnifiedNavigatorInput(
            user_query="What does my specific policy document say about coverage?",
            user_id="test_user_123"
        )
        
        output = await navigator_agent.execute(input_data)
        
        assert output.tool_used in [ToolType.RAG_SEARCH, ToolType.COMBINED]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, navigator_agent):
        """Test error handling in workflow execution."""
        input_data = UnifiedNavigatorInput(
            user_query="",  # Empty query
            user_id="test_user_123"
        )
        
        output = await navigator_agent.execute(input_data)
        
        # Should still return a valid output object
        assert isinstance(output, UnifiedNavigatorOutput)
        assert output.user_id == "test_user_123"
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, navigator_agent):
        """Test performance tracking functionality."""
        input_data = UnifiedNavigatorInput(
            user_query="What is insurance?",
            user_id="test_user_123"
        )
        
        output = await navigator_agent.execute(input_data)
        
        assert output.total_processing_time_ms > 0
        assert isinstance(output.total_processing_time_ms, float)


class TestGuardrailComponents:
    """Test cases for individual guardrail components."""
    
    @pytest.mark.asyncio
    async def test_input_sanitizer_fast_check(self):
        """Test fast safety check functionality."""
        from ..guardrails.input_sanitizer import InputSanitizer
        
        sanitizer = InputSanitizer()
        
        # Test safe query
        safe_result = sanitizer._fast_safety_check("What is my insurance coverage?")
        assert safe_result.is_safe
        assert safe_result.is_insurance_domain
        assert not safe_result.is_obviously_unsafe
        
        # Test unsafe query  
        unsafe_result = sanitizer._fast_safety_check("How to hack systems?")
        assert unsafe_result.is_obviously_unsafe
        
        await sanitizer.cleanup()
    
    @pytest.mark.asyncio
    async def test_output_sanitizer_template_rules(self):
        """Test output sanitizer template rules."""
        from ..guardrails.output_sanitizer import OutputSanitizer
        
        sanitizer = OutputSanitizer()
        
        # Test off-topic response
        off_topic_result = sanitizer._apply_template_sanitization(
            "Here's a great recipe for cookies and the weather today is nice."
        )
        assert off_topic_result["needs_replacement"]
        assert off_topic_result["reason"] == "off_topic"
        
        # Test good response
        good_result = sanitizer._apply_template_sanitization(
            "Your insurance policy covers medical expenses with a $500 deductible."
        )
        assert not good_result["needs_replacement"]
        assert good_result["reason"] == "acceptable"
        
        await sanitizer.cleanup()


class TestToolIntegration:
    """Test cases for tool integration."""
    
    @pytest.mark.asyncio
    async def test_web_search_tool_mock(self):
        """Test web search tool in mock mode."""
        from ..tools.web_search import WebSearchTool
        
        # Mock the API key to None to test mock mode
        with patch.dict(os.environ, {"BRAVE_API_KEY": ""}, clear=False):
            web_search = WebSearchTool()
            result = await web_search.search("insurance coverage")
            
            assert result.query == "insurance coverage"
            assert result.total_results == 0
            assert result.processing_time_ms >= 0
            
            await web_search.cleanup()
    
    @pytest.mark.asyncio
    async def test_rag_search_tool(self):
        """Test RAG search tool integration."""
        from ..tools.rag_search import RAGSearchTool
        
        rag_search = RAGSearchTool("test_user")
        result = await rag_search.search("insurance policy")
        
        assert result.query == "insurance policy"
        assert result.total_chunks >= 0
        assert result.processing_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_query_optimization(self):
        """Test query optimization for insurance domain."""
        from ..tools.web_search import WebSearchTool
        
        web_search = WebSearchTool()
        
        # Test query without insurance terms
        optimized = web_search._optimize_query("find doctors near me")
        assert "insurance" in optimized.lower()
        
        # Test query with insurance terms
        optimized_existing = web_search._optimize_query("find insurance doctors")
        assert "insurance" in optimized_existing.lower()


class TestConfiguration:
    """Test cases for configuration management."""
    
    def test_config_from_environment(self):
        """Test configuration loading from environment."""
        test_env = {
            "ANTHROPIC_API_KEY": "test_key",
            "BRAVE_API_KEY": "test_brave_key",
            "ANTHROPIC_MODEL": "claude-test",
            "NAVIGATOR_TIMEOUT": "60.0",
            "RAG_MAX_CHUNKS": "10"
        }
        
        with patch.dict(os.environ, test_env, clear=False):
            config = UnifiedNavigatorConfig.from_environment()
            
            assert config.anthropic_api_key == "test_key"
            assert config.anthropic_model == "claude-test"
            assert config.overall_timeout == 60.0
            assert config.web_search_config.api_key == "test_brave_key"
            assert config.rag_config.max_chunks == 10
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = UnifiedNavigatorConfig()
        config.anthropic_api_key = None
        
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
            config.validate()
    
    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = UnifiedNavigatorConfig()
        config.anthropic_api_key = "test_key"
        config.web_search_config.api_key = "test_brave_key"
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["has_anthropic_key"] is True
        assert config_dict["web_search_config"]["has_api_key"] is True
        assert "anthropic_api_key" not in config_dict  # Should not expose keys


@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring external services."""
    
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="Requires ANTHROPIC_API_KEY")
    @pytest.mark.asyncio
    async def test_real_llm_integration(self):
        """Test integration with real LLM service."""
        agent = UnifiedNavigatorAgent(use_mock=False)
        
        input_data = UnifiedNavigatorInput(
            user_query="What is insurance deductible?",
            user_id="integration_test_user"
        )
        
        output = await agent.execute(input_data)
        
        assert output.success
        assert len(output.response) > 50  # Should be substantial response
        assert output.total_processing_time_ms > 0
    
    @pytest.mark.skipif(not os.getenv("BRAVE_API_KEY"), reason="Requires BRAVE_API_KEY")
    @pytest.mark.asyncio
    async def test_real_web_search_integration(self):
        """Test integration with real Brave Search API."""
        from ..tools.web_search import WebSearchTool
        
        web_search = WebSearchTool()
        result = await web_search.search("insurance coverage types 2025")
        
        assert result.total_results > 0
        assert len(result.results) > 0
        assert all("title" in r for r in result.results)
        
        await web_search.cleanup()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])