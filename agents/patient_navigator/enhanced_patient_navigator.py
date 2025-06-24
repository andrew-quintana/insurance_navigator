"""
Enhanced Patient Navigator Agent with Vector Search Integration

This enhanced version of the Patient Navigator Agent includes:
1. Document-aware responses using vector search
2. Integration with user's uploaded documents
3. Regulatory document context when relevant
4. Improved context handling for better responses
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional, Union
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import PydanticOutputParser

# Import base functionality
from agents.patient_navigator.patient_navigator import PatientNavigatorAgent as BasePatientNavigator
from agents.patient_navigator.navigator_models import NavigatorOutput
from agents.common.vector_search_agent import VectorSearchAgent, SearchContext, get_agent_context

# Setup logger
logger = logging.getLogger(__name__)

class EnhancedPatientNavigatorAgent(BasePatientNavigator):
    """Enhanced Patient Navigator Agent with vector search capabilities."""
    
    def __init__(self, 
                 llm: Optional[BaseLanguageModel] = None,
                 prompt_security_agent=None,
                 config_manager=None,
                 enable_vector_search: bool = True):
        """
        Initialize the Enhanced Patient Navigator Agent.
        
        Args:
            llm: Language model to use
            prompt_security_agent: Security agent for prompt validation
            config_manager: Configuration manager instance
            enable_vector_search: Whether to enable vector search capabilities
        """
        # Initialize base patient navigator
        super().__init__(llm, prompt_security_agent, config_manager)
        
        # Initialize vector search capabilities
        self.enable_vector_search = enable_vector_search
        if self.enable_vector_search:
            self.vector_search_agent = VectorSearchAgent(force_supabase=True)
            logger.info("Vector search capabilities enabled for Patient Navigator")
        else:
            self.vector_search_agent = None
            logger.info("Vector search capabilities disabled")
        
        # Enhanced prompt template with document context
        self.enhanced_prompt_template = PromptTemplate(
            template="""
            {system_prompt}
            
            DOCUMENT CONTEXT:
            {document_context}
            
            User Query:
            {user_query}
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "document_context", "user_query"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
        
        # Create enhanced chain with document context
        self.enhanced_chain = (
            {
                "system_prompt": lambda _: self.system_prompt,
                "document_context": lambda x: x.get("document_context", "No relevant documents found."),
                "user_query": lambda x: x["user_query"]
            }
            | self.enhanced_prompt_template
            | self.llm
            | self.output_parser
        )
    
    async def get_document_context(self, user_query: str, user_id: str) -> str:
        """
        Get relevant document context for the user query.
        
        Args:
            user_query: The user's query
            user_id: The user's ID
            
        Returns:
            Formatted document context string
        """
        if not self.enable_vector_search or not self.vector_search_agent:
            return "Document search not available."
        
        try:
            # Get comprehensive context from both user and regulatory documents
            search_context = await self.vector_search_agent.search_combined_context(
                query=user_query,
                user_id=user_id,
                user_doc_limit=3,  # Limit user docs for performance
                regulatory_limit=2  # Limit regulatory docs for performance
            )
            
            if search_context.total_results == 0:
                return "No relevant documents found for this query."
            
            # Format context for agent prompt
            formatted_context = self.vector_search_agent.create_agent_prompt_context(
                search_context=search_context,
                max_context_length=3000  # Keep context manageable
            )
            
            # Add metadata about the search
            metadata_info = f"\n\nContext Summary: Found {search_context.total_results} relevant chunks "
            if search_context.document_context:
                metadata_info += f"({len(search_context.document_context)} from user documents"
            if search_context.regulatory_context:
                if search_context.document_context:
                    metadata_info += f", {len(search_context.regulatory_context)} from regulations)"
                else:
                    metadata_info += f"({len(search_context.regulatory_context)} from regulations)"
            else:
                metadata_info += ")"
            
            return formatted_context + metadata_info
            
        except Exception as e:
            logger.error(f"Error getting document context: {e}")
            return f"Error retrieving document context: {str(e)}"
    
    async def process_with_context(self, user_query: str, user_id: str, session_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process user query with document context enhancement.
        
        Args:
            user_query: The user's query
            user_id: The user's ID
            session_id: The session ID
            
        Returns:
            Tuple of (response, metadata)
        """
        try:
            # Performance tracking
            start_time = time.time()
            
            # Security check
            is_safe, security_reason = self._check_security(user_query)
            if not is_safe:
                logger.warning(f"Security check failed for query: {security_reason}")
                return (
                    "I'm sorry, but I can't process that request due to security concerns. Please rephrase your question.",
                    {"error": "Security check failed", "reason": security_reason}
                )
            
            # Get document context
            document_context = await self.get_document_context(user_query, user_id)
            
            # Process with enhanced chain that includes document context
            enhanced_input = {
                "user_query": user_query,
                "document_context": document_context
            }
            
            # Execute the enhanced chain
            result = self.enhanced_chain.invoke(enhanced_input)
            
            # Handle the result
            if isinstance(result, NavigatorOutput):
                response_text = result.response
                metadata = {
                    "intent": result.intent,
                    "confidence": result.confidence,
                    "locations": result.locations,
                    "insurance_info": result.insurance_info,
                    "document_context_available": len(document_context) > 50,  # Basic check
                    "processing_time": time.time() - start_time,
                    "vector_search_enabled": self.enable_vector_search
                }
            else:
                # Fallback for unexpected result format
                response_text = str(result)
                metadata = {
                    "document_context_available": len(document_context) > 50,
                    "processing_time": time.time() - start_time,
                    "vector_search_enabled": self.enable_vector_search
                }
            
            # Update conversation context
            self._handle_context(user_id, session_id, {
                "query": user_query,
                "response": response_text,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Enhanced processing completed in {metadata.get('processing_time', 0):.2f}s")
            return response_text, metadata
            
        except Exception as e:
            logger.error(f"Error in enhanced processing: {str(e)}")
            # Fallback to base processing
            return self.process(user_query, user_id, session_id)
    
    async def search_user_documents(self, query: str, user_id: str) -> SearchContext:
        """
        Search user's documents directly.
        
        Args:
            query: Search query
            user_id: User ID
            
        Returns:
            SearchContext with user document results
        """
        if not self.enable_vector_search or not self.vector_search_agent:
            return SearchContext(
                query=query,
                user_id=user_id,
                total_results=0,
                max_relevance_score=0.0,
                document_context=[],
                regulatory_context=[],
                combined_text="Vector search not available",
                metadata_summary={}
            )
        
        return await self.vector_search_agent.search_user_documents(
            query=query,
            user_id=user_id,
            limit=10
        )
    
    async def get_document_summary(self, document_id: str, user_id: str) -> SearchContext:
        """
        Get a complete summary of a specific document.
        
        Args:
            document_id: Document ID to summarize
            user_id: User ID for access control
            
        Returns:
            SearchContext with complete document content
        """
        if not self.enable_vector_search or not self.vector_search_agent:
            return SearchContext(
                query=f"Document summary: {document_id}",
                user_id=user_id,
                total_results=0,
                max_relevance_score=0.0,
                document_context=[],
                regulatory_context=[],
                combined_text="Vector search not available",
                metadata_summary={}
            )
        
        return await self.vector_search_agent.get_document_by_id(
            document_id=document_id,
            user_id=user_id,
            source_type="user_document"
        )
    
    def create_document_aware_response(self, base_response: str, search_context: SearchContext) -> str:
        """
        Enhance a response with document-specific information.
        
        Args:
            base_response: The base response from the agent
            search_context: Document search context
            
        Returns:
            Enhanced response with document references
        """
        if search_context.total_results == 0:
            return base_response
        
        # Add document references
        enhanced_response = base_response
        
        if search_context.document_context:
            enhanced_response += f"\n\n📄 Based on your uploaded documents:"
            doc_count = len(search_context.document_context)
            enhanced_response += f"\nI found information in {doc_count} document section(s) that may be relevant to your question."
        
        if search_context.regulatory_context:
            enhanced_response += f"\n\n⚖️ Relevant regulations:"
            reg_count = len(search_context.regulatory_context)
            enhanced_response += f"\nI also found {reg_count} regulatory reference(s) that apply to your situation."
        
        return enhanced_response
    
    # Override the base process method to use enhanced processing by default
    @BasePatientNavigator.track_performance
    def process(self, user_query: str, user_id: str, session_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process user query with enhanced capabilities.
        
        This method maintains compatibility with the base class while adding
        vector search capabilities when available.
        """
        if self.enable_vector_search:
            # Use async processing with document context
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(
                    self.process_with_context(user_query, user_id, session_id)
                )
            except RuntimeError:
                # No event loop, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self.process_with_context(user_query, user_id, session_id)
                    )
                finally:
                    loop.close()
        else:
            # Fallback to base processing
            return super().process(user_query, user_id, session_id)

# Convenience function to create an enhanced patient navigator
def create_enhanced_patient_navigator(
    llm: Optional[BaseLanguageModel] = None,
    prompt_security_agent=None,
    config_manager=None,
    enable_vector_search: bool = True
) -> EnhancedPatientNavigatorAgent:
    """
    Create an enhanced patient navigator agent.
    
    Args:
        llm: Language model to use
        prompt_security_agent: Security agent for prompt validation
        config_manager: Configuration manager instance
        enable_vector_search: Whether to enable vector search capabilities
        
    Returns:
        Configured EnhancedPatientNavigatorAgent
    """
    return EnhancedPatientNavigatorAgent(
        llm=llm,
        prompt_security_agent=prompt_security_agent,
        config_manager=config_manager,
        enable_vector_search=enable_vector_search
    ) 