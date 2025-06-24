"""
LangGraph Integration Test

Tests the integration between RAG pipeline and LangGraph agents.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List

# Test configuration
from tests.config.rag_test_config import get_test_config, update_document_id

# Services
from db.services.document_service import DocumentService
from agents.common.vector_retrieval_tool import VectorRetrievalTool, get_document_vectors, get_document_text

# LangGraph utilities
from agents.zPrototyping.langgraph_utils import (
    WorkflowBuilder,
    WorkflowState,
    AgentDiscovery,
    create_agent
)

logger = logging.getLogger(__name__)

class LangGraphRAGIntegration:
    """Test integration between LangGraph and RAG pipeline."""
    
    def __init__(self, document_id: Optional[str] = None):
        """Initialize integration tester."""
        if document_id:
            self.config = update_document_id(document_id)
        else:
            self.config = get_test_config()
        
        self.document_service = DocumentService()
        self.vector_tool = VectorRetrievalTool()
        self.agent_discovery = AgentDiscovery()
        
        logger.info(f"LangGraph RAG Integration initialized for document: {self.config.primary_document.document_id}")
    
    async def test_workflow_creation(self) -> bool:
        """Test creating a basic RAG workflow with LangGraph."""
        try:
            # Create workflow builder
            builder = WorkflowBuilder(name="rag_workflow")
            
            # Define RAG workflow nodes
            async def retrieve_documents(state: WorkflowState) -> WorkflowState:
                """Retrieve relevant documents."""
                doc_id = self.config.primary_document.document_id
                user_id = self.config.primary_document.test_user_id
                
                # Perform vector retrieval
                vectors = await self.vector_tool.get_vectors_by_document(
                    document_id=doc_id,
                    user_id=user_id,
                    source_type="user_document"
                )
                
                state.context["retrieved_vectors"] = vectors or []
                state.context["retrieval_success"] = len(vectors or []) > 0
                state.add_message(f"Retrieved {len(vectors or [])} vector chunks")
                return state
            
            async def generate_response(state: WorkflowState) -> WorkflowState:
                """Generate response based on retrieved vectors."""
                vectors = state.context.get("retrieved_vectors", [])
                
                if vectors:
                    # Extract text content from vectors
                    text_content = self.vector_tool.get_text_content(vectors)
                    response = f"Based on {len(vectors)} vector chunks ({len(text_content)} characters), here is the information..."
                    state.context["final_response"] = response
                    state.context["text_content"] = text_content
                    state.add_message(response)
                else:
                    state.context["final_response"] = "No relevant vectors found"
                    state.add_message("No relevant vectors found")
                
                return state
            
            # Build workflow
            workflow = (builder
                       .add_node("retrieve", retrieve_documents, "Document retrieval")
                       .add_node("generate", generate_response, "Response generation")
                       .add_edge("retrieve", "generate")
                       .set_entry_point("retrieve")
                       .build())
            
            if workflow:
                logger.info("✓ RAG workflow created successfully")
                return True
            else:
                logger.error("✗ Failed to create RAG workflow")
                return False
                
        except Exception as e:
            logger.error(f"✗ Workflow creation failed: {e}")
            return False
    
    async def test_agent_discovery(self) -> bool:
        """Test agent discovery functionality."""
        try:
            agents = self.agent_discovery.discover_agents()
            
            if not agents:
                logger.error("✗ No agents discovered")
                return False
            
            # Check for key agents
            key_agents = ["patient_navigator", "regulatory", "chat_communicator"]
            available_agents = []
            
            for agent_name in key_agents:
                if agent_name in agents:
                    available_agents.append(agent_name)
                    agent_info = self.agent_discovery.get_agent_info(agent_name)
                    if agent_info:
                        logger.info(f"✓ Agent '{agent_name}' available: {agent_info.description or 'No description'}")
            
            if available_agents:
                logger.info(f"✓ Agent discovery successful: {len(available_agents)} key agents found")
                return True
            else:
                logger.error("✗ No key agents found")
                return False
                
        except Exception as e:
            logger.error(f"✗ Agent discovery failed: {e}")
            return False
    
    async def test_rag_agent_workflow(self) -> bool:
        """Test a complete RAG workflow with agent integration."""
        try:
            # Test with a sample query
            test_query = self.config.test_queries[0] if self.config.test_queries else "What is covered?"
            user_id = self.config.primary_document.test_user_id
            
            # Step 1: Vector retrieval
            doc_id = self.config.primary_document.document_id
            vectors = await self.vector_tool.get_vectors_by_document(
                document_id=doc_id,
                user_id=user_id,
                source_type="user_document"
            )
            
            # Step 2: Text extraction
            text_content = self.vector_tool.get_text_content(vectors) if vectors else ""
            
            # Step 3: Simulate agent processing
            workflow_state = WorkflowState()
            workflow_state.add_message(test_query)
            workflow_state.context["vectors"] = vectors or []
            workflow_state.context["text_content"] = text_content
            
            # Check if we have usable results
            has_vectors = len(vectors or []) > 0
            has_text = len(text_content) > 0
            
            if has_vectors and has_text:
                logger.info(f"✓ RAG agent workflow test passed")
                logger.info(f"  Vector chunks: {len(vectors)}")
                logger.info(f"  Text content: {len(text_content)} characters")
                return True
            else:
                logger.error("✗ RAG agent workflow test failed - no usable content")
                return False
                
        except Exception as e:
            logger.error(f"✗ RAG agent workflow test failed: {e}")
            return False
    
    async def run_integration_tests(self) -> Dict[str, bool]:
        """Run all integration tests."""
        logger.info("="*60)
        logger.info("Starting LangGraph RAG Integration Tests")
        logger.info(f"Document ID: {self.config.primary_document.document_id}")
        logger.info("="*60)
        
        results = {}
        
        # Run tests
        results["workflow_creation"] = await self.test_workflow_creation()
        results["agent_discovery"] = await self.test_agent_discovery()
        results["rag_agent_workflow"] = await self.test_rag_agent_workflow()
        
        # Summary
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        logger.info("="*60)
        logger.info(f"Integration Test Results: {passed}/{total} tests passed")
        
        for test_name, passed in results.items():
            status = "PASS" if passed else "FAIL"
            logger.info(f"  {test_name}: {status}")
        
        logger.info("="*60)
        
        return results

# Convenience functions
async def test_langgraph_integration(document_id: Optional[str] = None) -> Dict[str, bool]:
    """Test LangGraph integration with RAG."""
    integration = LangGraphRAGIntegration(document_id=document_id)
    return await integration.run_integration_tests()

# CLI interface
if __name__ == "__main__":
    import sys
    
    async def main():
        doc_id = sys.argv[1] if len(sys.argv) > 1 else None
        results = await test_langgraph_integration(doc_id)
        
        # Exit with error code if any tests failed
        failed_tests = [name for name, passed in results.items() if not passed]
        if failed_tests:
            print(f"Failed tests: {', '.join(failed_tests)}")
            exit(1)
        else:
            print("All integration tests passed!")
            exit(0)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
