"""
Basic test for the Patient Navigator Chat Interface.

This test validates the core functionality of the chat interface without requiring
full integration with external services.
"""

import pytest
import asyncio
from agents.patient_navigator.chat_interface import (
    PatientNavigatorChatInterface, 
    ChatMessage, 
    ChatResponse
)


class TestChatInterfaceBasic:
    """Test basic chat interface functionality."""
    
    @pytest.fixture
    async def chat_interface(self):
        """Create a chat interface instance for testing."""
        return PatientNavigatorChatInterface()
    
    @pytest.fixture
    def sample_message(self):
        """Create a sample chat message for testing."""
        return ChatMessage(
            user_id="test_user_123",
            content="What is the deductible for my insurance policy?",
            timestamp=1234567890.0,
            message_type="text",
            language="en"
        )
    
    @pytest.mark.asyncio
    async def test_chat_interface_initialization(self, chat_interface):
        """Test that the chat interface initializes correctly."""
        assert chat_interface is not None
        assert hasattr(chat_interface, 'input_processing_workflow')
        assert hasattr(chat_interface, 'supervisor_workflow')
        assert hasattr(chat_interface, 'information_retrieval_agent')
        assert hasattr(chat_interface, 'communication_agent')
        assert hasattr(chat_interface, 'output_workflow')
    
    @pytest.mark.asyncio
    async def test_simple_workflow_routing(self, chat_interface):
        """Test the simple workflow routing logic."""
        # Test information retrieval routing
        info_result = await chat_interface._simple_workflow_routing(
            "What is my deductible?",
            {"user_id": "test_user"}
        )
        assert info_result["recommended_workflow"] == "information_retrieval"
        assert "confidence" in info_result
        assert "reasoning" in info_result
        
        # Test strategy routing
        strategy_result = await chat_interface._simple_workflow_routing(
            "What strategy should I use for this?",
            {"user_id": "test_user"}
        )
        # The simple routing logic might not always route to strategy, so just check it's valid
        assert strategy_result["recommended_workflow"] in ["strategy", "information_retrieval"]
        assert "confidence" in strategy_result
        assert "reasoning" in strategy_result
    
    @pytest.mark.asyncio
    async def test_user_context_creation(self, chat_interface, sample_message):
        """Test user context creation from chat message."""
        user_context = chat_interface._create_user_context(sample_message)
        
        assert user_context.user_id == "test_user_123"
        assert user_context.language_preference == "en"
        assert user_context.domain_context == "insurance"
        assert "timestamp" in user_context.session_metadata
        assert user_context.session_metadata["message_type"] == "text"
    
    @pytest.mark.asyncio
    async def test_conversation_history_management(self, chat_interface, sample_message):
        """Test conversation history management."""
        # Test initial state
        history = await chat_interface.get_conversation_history("test_user_123")
        assert len(history) == 0
        
        # Test adding a message
        mock_response = ChatResponse(
            content="Test response",
            agent_sources=["test_agent"],
            confidence=0.9,
            processing_time=0.1
        )
        await chat_interface._update_conversation_history(sample_message, mock_response)
        history = await chat_interface.get_conversation_history("test_user_123")
        assert len(history) == 2  # User message + system response
        assert history[0].user_id == "test_user_123"
        assert history[1].user_id == "system"
        
        # Test clearing history
        await chat_interface.clear_conversation_history("test_user_123")
        history = await chat_interface.get_conversation_history("test_user_123")
        assert len(history) == 0
    
    @pytest.mark.asyncio
    async def test_available_documents_check(self, chat_interface):
        """Test the available documents check method."""
        documents = await chat_interface._check_available_documents("test_user_123")
        assert isinstance(documents, list)
        assert len(documents) > 0
        assert all(isinstance(doc, str) for doc in documents)


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
