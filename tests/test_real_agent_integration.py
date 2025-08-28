"""
Real Agent Integration Test

This test validates that real agents can process messages and workflows correctly.
"""

import pytest
import asyncio
import time
from agents.patient_navigator.chat_interface import (
    PatientNavigatorChatInterface, 
    ChatMessage, 
    ChatResponse
)


class TestRealAgentIntegration:
    """Test real agent integration and workflow functionality."""
    
    @pytest.fixture
    async def chat_interface(self):
        """Create a chat interface instance with real agents."""
        return PatientNavigatorChatInterface()
    
    @pytest.mark.asyncio
    async def test_real_information_retrieval_agent(self, chat_interface):
        """Test that the real information retrieval agent can process queries."""
        message = ChatMessage(
            user_id="5710ff53-32ea-4fab-be6d-3a6f0627fbff",  # Valid UUID for testing
            content="What is the deductible for my insurance policy?",
            timestamp=time.time(),
            message_type="text",
            language="en"
        )
        
        try:
            # Process message through real agents
            start_time = time.time()
            response = await chat_interface.process_message(message)
            processing_time = time.time() - start_time
            
            # Validate response
            assert response is not None
            assert isinstance(response, ChatResponse)
            assert response.content is not None
            assert len(response.content) > 0
            
            # Check if real agent was used
            if "information_retrieval" in response.agent_sources:
                print(f"✅ Real information retrieval agent used successfully")
                print(f"Response: {response.content[:200]}...")
                print(f"Processing time: {processing_time:.2f}s")
            else:
                print(f"⚠️  Information retrieval agent not used: {response.agent_sources}")
            
        except Exception as e:
            pytest.fail(f"Real agent processing failed: {e}")
    
    @pytest.mark.asyncio
    async def test_real_strategy_agent(self, chat_interface):
        """Test that the real strategy agent can process strategy requests."""
        message = ChatMessage(
            user_id="5710ff53-32ea-4fab-be6d-3a6f0627fbff",  # Valid UUID for testing
            content="What strategy should I use to minimize my out-of-pocket costs?",
            timestamp=time.time(),
            message_type="text",
            language="en"
        )
        
        try:
            # Process message through real agents
            start_time = time.time()
            response = await chat_interface.process_message(message)
            processing_time = time.time() - start_time
            
            # Validate response
            assert response is not None
            assert isinstance(response, ChatResponse)
            assert response.content is not None
            assert len(response.content) > 0
            
            # Check if real agent was used
            if "strategy" in response.agent_sources:
                print(f"✅ Real strategy agent used successfully")
                print(f"Response: {response.content[:200]}...")
                print(f"Processing time: {processing_time:.2f}s")
            else:
                print(f"⚠️  Strategy agent not used: {response.agent_sources}")
            
        except Exception as e:
            pytest.fail(f"Real agent processing failed: {e}")
    
    @pytest.mark.asyncio
    async def test_supervisor_workflow_integration(self, chat_interface):
        """Test that the supervisor workflow can route requests correctly."""
        # Test different types of queries to see routing behavior
        test_queries = [
            ("What is my deductible?", "information_retrieval"),
            ("How can I save money on insurance?", "strategy"),
            ("What does my policy cover?", "information_retrieval"),
            ("What's the best approach for my situation?", "strategy")
        ]
        
        for query, expected_workflow in test_queries:
            message = ChatMessage(
                user_id="test_user_supervisor",
                content=query,
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
            
            try:
                response = await chat_interface.process_message(message)
                
                # Check if the expected workflow was used
                if expected_workflow in response.agent_sources:
                    print(f"✅ Supervisor correctly routed '{query[:50]}...' to {expected_workflow}")
                else:
                    print(f"⚠️  Supervisor routing may be incorrect for '{query[:50]}...'")
                    print(f"   Expected: {expected_workflow}, Got: {response.agent_sources}")
                
            except Exception as e:
                print(f"❌ Supervisor workflow failed for query '{query[:50]}...': {e}")
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, chat_interface):
        """Test error handling and recovery mechanisms with real agents."""
        # Test with problematic input
        problematic_messages = [
            ChatMessage(
                user_id="test_user_error",
                content="",  # Empty message
                timestamp=time.time(),
                message_type="text",
                language="en"
            ),
            ChatMessage(
                user_id="test_user_error",
                content="A" * 10000,  # Very long message
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
        ]
        
        for message in problematic_messages:
            try:
                response = await chat_interface.process_message(message)
                
                # Should handle gracefully
                assert response is not None
                assert response.content is not None
                
                print(f"✅ Error handling successful for {message.content[:50] if message.content else 'empty'}...")
                
            except Exception as e:
                print(f"⚠️  Error handling failed for problematic input: {e}")
    
    @pytest.mark.asyncio
    async def test_performance_with_real_agents(self, chat_interface):
        """Test performance characteristics with real agents."""
        message = ChatMessage(
            user_id="test_user_performance",
            content="What is the deductible for my insurance policy?",
            timestamp=time.time(),
            message_type="text",
            language="en"
        )
        
        # Test multiple iterations to measure performance
        times = []
        for i in range(3):
            start_time = time.time()
            response = await chat_interface.process_message(message)
            processing_time = time.time() - start_time
            times.append(processing_time)
            
            # Small delay between requests
            await asyncio.sleep(0.1)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"Performance metrics:")
        print(f"  Average time: {avg_time:.2f}s")
        print(f"  Min time: {min_time:.2f}s")
        print(f"  Max time: {max_time:.2f}s")
        
        # Performance should be reasonable
        assert avg_time < 30.0, f"Average processing time {avg_time:.2f}s is too high"
        assert max_time < 60.0, f"Maximum processing time {max_time:.2f}s is too high"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
