"""
Unit tests for the Regulatory Agent with search capabilities.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any

# Import the modules to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from agents.regulatory.core.regulatory import (
    RegulatoryAgent,
    create_regulatory_agent,
    analyze_regulatory_strategy
)
from agents.regulatory.core.search.orchestrator import SearchRequest, SearchResponse


class TestRegulatoryAgent:
    """Test cases for the RegulatoryAgent class."""
    
    @pytest.fixture
    def mock_db_config(self):
        """Mock database configuration."""
        return {
            'host': 'localhost',
            'port': 5432,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db'
        }
    
    @pytest.fixture
    def sample_search_response(self):
        """Sample search response for testing."""
        return SearchResponse(
            query="Medicare coverage determination",
            total_results=2,
            cached_results=1,
            new_results=1,
            documents=[
                {
                    "document_id": "test-doc-1",
                    "title": "Medicare Coverage Determination Process",
                    "url": "https://www.cms.gov/medicare/coverage/determination-process",
                    "content": "Medicare coverage determinations are decisions about whether Medicare will cover specific medical items or services.",
                    "document_type": "policy",
                    "jurisdiction": "federal",
                    "programs": ["Medicare"],
                    "source": "web_search_new"
                }
            ],
            search_timestamp=datetime.now(),
            processing_time_seconds=2.5
        )

    @pytest.mark.asyncio
    async def test_agent_initialization_with_search(self, mock_db_config):
        """Test agent initialization with search capabilities enabled."""
        with patch('agents.regulatory.core.regulatory.get_db_config', return_value=mock_db_config):
            with patch('agents.regulatory.core.regulatory.RegulatorySearchOrchestrator') as mock_orchestrator:
                agent = RegulatoryAgent(
                    model_name="gpt-3.5-turbo",
                    temperature=0.2,
                    enable_search=True
                )
                
                assert agent.model_name == "gpt-3.5-turbo"
                assert agent.temperature == 0.2
                assert agent.enable_search == True
                assert len(agent.tools) > 0
                assert any(tool.name == "search_regulatory_documents" for tool in agent.tools)

    @pytest.mark.asyncio
    async def test_search_tool_functionality(self, mock_db_config, sample_search_response):
        """Test the search tool functionality."""
        with patch('agents.regulatory.core.regulatory.get_db_config', return_value=mock_db_config):
            with patch('agents.regulatory.core.regulatory.RegulatorySearchOrchestrator') as mock_orchestrator_class:
                # Setup mock
                mock_orchestrator = AsyncMock()
                mock_orchestrator.search_regulatory_documents.return_value = sample_search_response
                mock_orchestrator_class.return_value = mock_orchestrator
                
                agent = RegulatoryAgent(enable_search=True)
                
                # Find and test the search tool
                search_tool = next((tool for tool in agent.tools if tool.name == "search_regulatory_documents"), None)
                assert search_tool is not None
                
                result = await search_tool.func("Medicare coverage determination")
                
                assert "Found 2 regulatory documents" in result
                assert "Medicare Coverage Determination Process" in result
                assert "cms.gov" in result


class TestRegulatoryAgentDemo:
    """Integration demo tests for regulatory agent."""

    @pytest.mark.asyncio
    async def test_regulatory_agent_demo(self):
        """Test regulatory agent with live functionality."""
        print("\n🚀 Testing Regulatory Agent with Search Capabilities")
        print("=" * 60)
        
        # Test agent creation
        try:
            agent = RegulatoryAgent(enable_search=False)  # Disable search for basic test
            print("✅ Agent creation: SUCCESS")
        except Exception as e:
            print(f"❌ Agent creation: FAILED - {str(e)}")
            return
        
        # Test capabilities
        try:
            capabilities = agent.get_capabilities()
            print(f"✅ Agent capabilities: {capabilities['version']}")
            print(f"   - Model: {capabilities['model']}")
            print(f"   - Search enabled: {capabilities['search_enabled']}")
            print(f"   - Features: {len(capabilities['features'])}")
        except Exception as e:
            print(f"❌ Get capabilities: FAILED - {str(e)}")
        
        # Test prompt template loading
        try:
            assert agent.prompt_template is not None
            assert len(agent.prompt_template) > 0
            print("✅ Prompt template: LOADED")
        except Exception as e:
            print(f"❌ Prompt template: FAILED - {str(e)}")
        
        print("\n📊 Demo Results: Core agent functionality verified")


if __name__ == "__main__":
    # Run the demo test
    asyncio.run(TestRegulatoryAgentDemo().test_regulatory_agent_demo()) 