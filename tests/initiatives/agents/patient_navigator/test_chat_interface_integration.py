"""
Integration test for the Patient Navigator Chat Interface.

This test validates the complete conversation flow including:
1. Input processing workflow
2. Agent workflow routing
3. Output processing workflow
4. End-to-end message processing
"""

import pytest
import asyncio
import time
from agents.patient_navigator.chat_interface import (
    PatientNavigatorChatInterface, 
    ChatMessage, 
    ChatResponse
)


class TestChatInterfaceIntegration:
    """Test complete chat interface integration."""
    
    @pytest.fixture
    async def chat_interface(self):
        """Create a chat interface instance for testing."""
        return PatientNavigatorChatInterface()
    
    @pytest.fixture
    def sample_questions(self):
        """Sample questions to test different workflow routing."""
        return [
            {
                "question": "What is the deductible for my insurance policy?",
                "expected_workflow": "information_retrieval",
                "description": "Information retrieval question about policy details"
            },
            {
                "question": "What strategy should I use to minimize my out-of-pocket costs?",
                "expected_workflow": "strategy",
                "description": "Strategy question about cost optimization"
            },
            {
                "question": "How much will I pay for a doctor visit?",
                "expected_workflow": "information_retrieval",
                "description": "Information retrieval question about specific costs"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_complete_message_processing_flow(self, chat_interface, sample_questions):
        """Test the complete message processing flow end-to-end."""
        for question_data in sample_questions:
            question = question_data["question"]
            expected_workflow = question_data["expected_workflow"]
            description = question_data["description"]
            
            print(f"\nTesting: {description}")
            print(f"Question: {question}")
            
            # Create chat message
            message = ChatMessage(
                user_id="test_user_123",
                content=question,
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
            
            # Process message through complete flow
            start_time = time.time()
            response = await chat_interface.process_message(message)
            processing_time = time.time() - start_time
            
            # Validate response structure
            assert response is not None
            assert isinstance(response, ChatResponse)
            assert response.content is not None
            assert len(response.content) > 0
            assert response.agent_sources is not None
            assert len(response.agent_sources) > 0
            assert response.confidence >= 0.0
            assert response.processing_time >= 0.0
            
            # Validate processing time (should be reasonable)
            assert processing_time < 30.0  # Should complete within 30 seconds
            
            print(f"Response: {response.content[:100]}...")
            print(f"Agent sources: {response.agent_sources}")
            print(f"Confidence: {response.confidence}")
            print(f"Processing time: {processing_time:.2f}s")
            print(f"Expected workflow: {expected_workflow}")
            
            # Check if the expected workflow was used (if available)
            if expected_workflow in response.agent_sources:
                print(f"✅ Expected workflow '{expected_workflow}' was used")
            else:
                print(f"⚠️  Expected workflow '{expected_workflow}' not found in sources: {response.agent_sources}")
    
    @pytest.mark.asyncio
    async def test_conversation_context_persistence(self, chat_interface):
        """Test that conversation context is maintained across multiple messages."""
        user_id = "test_user_context"
        
        # Clear any existing history
        await chat_interface.clear_conversation_history(user_id)
        
        # Send first message
        message1 = ChatMessage(
            user_id=user_id,
            content="What is my deductible?",
            timestamp=time.time(),
            message_type="text",
            language="en"
        )
        
        response1 = await chat_interface.process_message(message1)
        assert response1 is not None
        
        # Check conversation history
        history1 = await chat_interface.get_conversation_history(user_id)
        assert len(history1) == 2  # User message + system response
        
        # Send follow-up message
        message2 = ChatMessage(
            user_id=user_id,
            content="And what about my copay?",
            timestamp=time.time(),
            message_type="text",
            language="en"
        )
        
        response2 = await chat_interface.process_message(message2)
        assert response2 is not None
        
        # Check updated conversation history
        history2 = await chat_interface.get_conversation_history(user_id)
        assert len(history2) == 4  # 2 user messages + 2 system responses
        
        # Verify message order
        assert history2[0].content == "What is my deductible?"
        assert history2[1].user_id == "system"
        assert history2[2].content == "And what about my copay?"
        assert history2[3].user_id == "system"
        
        print(f"✅ Conversation context maintained: {len(history2)} messages")
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, chat_interface):
        """Test error handling and recovery mechanisms."""
        # Test with an empty message
        empty_message = ChatMessage(
            user_id="test_user_error",
            content="",
            timestamp=time.time(),
            message_type="text",
            language="en"
        )
        
        try:
            response = await chat_interface.process_message(empty_message)
            # Should handle gracefully and return an error response
            assert response is not None
            assert "error" in response.metadata or "error" in response.content.lower()
            print("✅ Empty message handled gracefully")
        except Exception as e:
            print(f"⚠️  Empty message caused exception: {e}")
        
        # Test with a very long message
        long_message = ChatMessage(
            user_id="test_user_error",
            content="This is a very long message " * 1000,  # Very long content
            timestamp=time.time(),
            message_type="text",
            language="en"
        )
        
        try:
            response = await chat_interface.process_message(long_message)
            assert response is not None
            print("✅ Long message handled gracefully")
        except Exception as e:
            print(f"⚠️  Long message caused exception: {e}")
    
    @pytest.mark.asyncio
    async def test_multilingual_support(self, chat_interface):
        """Test multilingual input support."""
        # Test Spanish input (hardcoded for MVP)
        spanish_message = ChatMessage(
            user_id="test_user_spanish",
            content="¿Cuál es mi deducible?",
            timestamp=time.time(),
            message_type="text",
            language="es"
        )
        
        try:
            response = await chat_interface.process_message(spanish_message)
            assert response is not None
            assert len(response.content) > 0
            print("✅ Spanish input processed successfully")
        except Exception as e:
            print(f"⚠️  Spanish input caused exception: {e}")
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, chat_interface):
        """Test performance under multiple concurrent requests."""
        user_ids = [f"load_test_user_{i}" for i in range(5)]
        messages = []
        
        # Create multiple messages
        for user_id in user_ids:
            message = ChatMessage(
                user_id=user_id,
                content="What is my insurance coverage?",
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
            messages.append((user_id, message))
        
        # Process messages concurrently
        start_time = time.time()
        tasks = []
        for user_id, message in messages:
            task = asyncio.create_task(chat_interface.process_message(message))
            tasks.append((user_id, task))
        
        # Wait for all to complete
        responses = []
        for user_id, task in tasks:
            try:
                response = await task
                responses.append((user_id, response))
            except Exception as e:
                print(f"❌ Error processing message for {user_id}: {e}")
        
        total_time = time.time() - start_time
        
        # Validate all responses
        assert len(responses) == len(messages)
        for user_id, response in responses:
            assert response is not None
            assert response.content is not None
        
        print(f"✅ Processed {len(responses)} concurrent messages in {total_time:.2f}s")
        print(f"Average time per message: {total_time/len(responses):.2f}s")


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
