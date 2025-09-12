"""
Information Retrieval Agent for Patient Navigator

This agent implements a ReAct pattern to translate user queries into insurance terminology,
integrate with the RAG system, and provide consistent responses using self-consistency methodology.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from agents.base_agent import BaseAgent
from agents.tooling.rag.core import RAGTool, RetrievalConfig, ChunkWithContext
from .models import InformationRetrievalInput, InformationRetrievalOutput, SourceChunk
from ..shared.terminology import InsuranceTerminologyTranslator
from ..shared.consistency import SelfConsistencyChecker


class InformationRetrievalAgent(BaseAgent):
    """
    Information retrieval agent for insurance document navigation.
    
    Inherits from BaseAgent following established patterns.
    Integrates with existing RAG system and terminology utilities.
    """
    
    def __init__(self, use_mock: bool = False, **kwargs):
        """
        Initialize the Information Retrieval Agent.
        
        Args:
            use_mock: If True, use mock responses for testing
            **kwargs: Additional arguments passed to BaseAgent
        """
        super().__init__(
            name="information_retrieval",
            prompt="",  # Will be loaded from file
            output_schema=InformationRetrievalOutput,
            mock=use_mock,
            **kwargs
        )
        
        # Initialize domain-specific utilities
        self.terminology_translator = InsuranceTerminologyTranslator()
        self.consistency_checker = SelfConsistencyChecker()
        self.rag_tool = None  # Will be initialized with user context
        
    async def retrieve_information(self, input_data: InformationRetrievalInput) -> InformationRetrievalOutput:
        """
        Main entry point for information retrieval using ReAct pattern.
        
        Args:
            input_data: Structured input from supervisor workflow
            
        Returns:
            InformationRetrievalOutput with structured response
        """
        try:
            # Step 1: Parse Structured Input from supervisor workflow
            user_query = input_data.user_query
            user_id = input_data.user_id
            workflow_context = input_data.workflow_context or {}
            document_requirements = input_data.document_requirements or []
            
            self.logger.info(f"Processing query: {user_query[:100]}...")
            
            # Step 2: Query Reframing using insurance terminology
            expert_query = await self._reframe_query(user_query)
            self.logger.info(f"Expert reframe: {expert_query}")
            
            # Step 3: RAG Integration with existing system
            chunks = await self._retrieve_chunks(expert_query, user_id)
            self.logger.info(f"Retrieved {len(chunks)} chunks")
            
            # Step 4-N: Self-Consistency Loop (3-5 iterations)
            response_variants = await self._generate_response_variants(chunks, user_query, expert_query)
            consistency_score = self.consistency_checker.calculate_consistency(response_variants)
            
            # Final: Structured Output generation
            final_response = self.consistency_checker.synthesize_final_response(response_variants, consistency_score)
            key_points = self.consistency_checker.extract_key_points(response_variants)
            
            # Ensure we have at least one key point to satisfy Pydantic validation
            if not key_points:
                key_points = ["Information retrieved from insurance documents"]
            
            confidence_score = self.consistency_checker.calculate_confidence_score(response_variants, consistency_score)
            
            # Convert chunks to source chunks for attribution
            source_chunks = self._convert_to_source_chunks(chunks)
            
            return InformationRetrievalOutput(
                expert_reframe=expert_query,
                direct_answer=final_response,
                key_points=key_points,
                confidence_score=confidence_score,
                source_chunks=source_chunks,
                processing_steps=[
                    "Query parsing and validation",
                    "Insurance terminology translation",
                    "RAG system document retrieval",
                    f"Self-consistency generation ({len(response_variants)} variants)",
                    "Response synthesis and confidence scoring"
                ]
            )
            
        except Exception as e:
            self.logger.error(f"Error in information retrieval: {e}")
            return InformationRetrievalOutput(
                expert_reframe="",
                direct_answer="I encountered an error while processing your request. Please try again.",
                key_points=["Error occurred during processing"],
                confidence_score=0.0,
                source_chunks=[],
                error_message=str(e)
            )
    
    async def _reframe_query(self, user_query: str) -> str:
        """
        Reframe user query into expert insurance terminology using LLM.
        
        Args:
            user_query: The user's natural language query
            
        Returns:
            Expert-level query in insurance terminology
        """
        # Use LLM for expert reframing - more flexible than static dictionary
        system_prompt = self._load_if_path("prompts/system_prompt.md")
        
        # Create expert reframing prompt
        expert_prompt = f"""
{system_prompt}

Please reframe the following user query into expert insurance terminology:

User Query: "{user_query}"

Instructions:
1. Convert the user's natural language into professional insurance terminology
2. Use terms that would appear in insurance documents and benefit descriptions
3. Focus on key concepts like: physician services, prescription drug benefits, cost-sharing, 
   benefit coverage, provider networks, authorization requirements, etc.
4. Maintain the original intent while using expert terminology
5. Provide ONLY the expert-level query reframing, no additional explanation

Expert Query Reframe:
"""
        
        try:
            # Use BaseAgent's LLM capabilities for expert reframing
            response = await self._call_llm(expert_prompt)
            
            # Extract the expert reframe from the response
            expert_query = response.strip()
            
            # Validate the translation using the terminology translator
            if not self.terminology_translator.validate_translation(user_query, expert_query):
                self.logger.warning("LLM translation validation failed, using fallback")
                expert_query = self.terminology_translator.get_fallback_translation(user_query)
            
            return expert_query
            
        except Exception as e:
            self.logger.error(f"Error in LLM query reframing: {e}")
            # Fallback to simple keyword replacement
            return self.terminology_translator.get_fallback_translation(user_query)
    
    def _fallback_translation(self, user_query: str) -> str:
        """
        Simple fallback translation using basic keyword replacement.
        
        Args:
            user_query: The user's natural language query
            
        Returns:
            Basic expert-level query
        """
        return self.terminology_translator.get_fallback_translation(user_query)
    
    async def _retrieve_chunks(self, expert_query: str, user_id: str) -> List[ChunkWithContext]:
        """
        Retrieve relevant document chunks using RAG system.
        
        Args:
            expert_query: Expert-level query for retrieval
            user_id: User identifier for access control
            
        Returns:
            List of relevant document chunks
        """
        try:
            # Initialize RAG tool with user context
            self.rag_tool = RAGTool(user_id=user_id, config=RetrievalConfig.default())
            
            # Use RAG tool's built-in text-to-chunks method (handles embedding generation internally)
            chunks = await self.rag_tool.retrieve_chunks_from_text(expert_query)
            
            # Extract similarity scores for histogram analysis
            similarities = [chunk.similarity for chunk in chunks if chunk.similarity is not None]
            
            # Generate and log similarity histogram for debugging
            if similarities:
                from utils.similarity_histogram import log_similarity_histogram
                log_similarity_histogram(similarities, threshold=0.4, logger=self.logger)
            else:
                self.logger.warning("No similarity scores available for histogram analysis")
            
            # Filter chunks by similarity threshold (adjusted for real OpenAI embeddings)
            filtered_chunks = [
                chunk for chunk in chunks 
                if chunk.similarity and chunk.similarity >= 0.3
            ]
            
            self.logger.info(f"Retrieved {len(chunks)} chunks, filtered to {len(filtered_chunks)} with similarity >= 0.3")
            
            return filtered_chunks
            
        except Exception as e:
            self.logger.error(f"Error in RAG retrieval: {e}")
            return []
    
    
    async def _generate_response_variants(self, chunks: List[ChunkWithContext], user_query: str, expert_query: str) -> List[str]:
        """
        Generate multiple response variants using self-consistency methodology.
        
        Args:
            chunks: Retrieved document chunks
            user_query: Original user query
            expert_query: Expert-reframed query
            
        Returns:
            List of response variants
        """
        if not chunks:
            return ["No relevant information found in the available documents."]
        
        # Prepare document context for LLM
        document_context = self._prepare_document_context(chunks)
        
        # Generate multiple variants
        variants = []
        max_variants = 3  # Start with 3 variants for MVP
        
        for i in range(max_variants):
            try:
                # Create variant-specific prompt
                variant_prompt = self._create_variant_prompt(
                    user_query, expert_query, document_context, variant_num=i+1
                )
                
                # Generate variant using LLM
                variant_response = await self._call_llm(variant_prompt)
                
                # Clean and validate variant
                cleaned_variant = self._clean_response_variant(variant_response)
                if cleaned_variant:
                    variants.append(cleaned_variant)
                
            except Exception as e:
                self.logger.error(f"Error generating variant {i+1}: {e}")
                continue
        
        # Ensure we have at least one variant
        if not variants:
            variants = ["Unable to generate response due to processing error."]
        
        return variants
    
    def _prepare_document_context(self, chunks: List[ChunkWithContext]) -> str:
        """
        Prepare document context for LLM processing.
        
        Args:
            chunks: Retrieved document chunks
            
        Returns:
            Formatted document context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            chunk_info = f"Chunk {i+1} (Similarity: {chunk.similarity:.3f})"
            if chunk.section_title:
                chunk_info += f" - Section: {chunk.section_title}"
            if chunk.page_start:
                chunk_info += f" - Page: {chunk.page_start}"
            
            context_parts.append(f"{chunk_info}\n{chunk.content}\n")
        
        return "\n".join(context_parts)
    
    def _create_variant_prompt(self, user_query: str, expert_query: str, document_context: str, variant_num: int) -> str:
        """
        Create prompt for generating a specific response variant.
        
        Args:
            user_query: Original user query
            expert_query: Expert-reframed query
            document_context: Document chunks context
            variant_num: Variant number for diversity
            
        Returns:
            Formatted prompt for LLM
        """
        system_prompt = self._load_if_path("prompts/system_prompt.md")
        
        variant_instructions = f"""
You are generating response variant {variant_num} of 3. Focus on providing a comprehensive answer that addresses the user's question using the provided document context.

User Query: {user_query}
Expert Query: {expert_query}

Document Context:
{document_context}

Instructions:
1. Analyze the document context thoroughly
2. Provide a complete answer addressing the user's question
3. Include specific details from the documents when available
4. Use clear, patient-friendly language while maintaining technical accuracy
5. If information is not available in the documents, clearly state this
6. Focus on being comprehensive and helpful

Generate a detailed response that would be most helpful to the user.
"""
        
        return f"{system_prompt}\n\n{variant_instructions}"
    
    def _clean_response_variant(self, response: str) -> str:
        """
        Clean and validate a response variant.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned response string
        """
        # Remove common LLM artifacts
        cleaned = response.strip()
        
        # Remove markdown formatting if present
        cleaned = cleaned.replace("```", "").strip()
        
        # Remove system instructions that might be included
        if "You are generating response variant" in cleaned:
            # Extract only the response part
            lines = cleaned.split('\n')
            response_lines = []
            in_response = False
            
            for line in lines:
                if "Generate a detailed response" in line:
                    in_response = True
                    continue
                if in_response:
                    response_lines.append(line)
            
            cleaned = '\n'.join(response_lines).strip()
        
        # Validate response quality
        quality_metrics = self.consistency_checker.validate_response_quality(cleaned)
        
        # Only return responses that meet basic quality standards
        if quality_metrics["length"] > 20 and quality_metrics["is_complete"]:
            return cleaned
        
        return ""
    
    def _convert_to_source_chunks(self, chunks: List[ChunkWithContext]) -> List[SourceChunk]:
        """
        Convert RAG chunks to source chunks for attribution.
        
        Args:
            chunks: RAG system chunks
            
        Returns:
            List of source chunks for attribution
        """
        source_chunks = []
        
        for chunk in chunks:
            source_chunk = SourceChunk(
                chunk_id=chunk.id,
                doc_id=chunk.doc_id,
                content=chunk.content,
                section_title=chunk.section_title,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                similarity=chunk.similarity,
                tokens=chunk.tokens
            )
            source_chunks.append(source_chunk)
        
        return source_chunks
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call LLM with prompt using BaseAgent's capabilities.
        
        Args:
            prompt: Prompt to send to LLM
            
        Returns:
            LLM response string
        """
        try:
            if self.mock or self.llm is None:
                # Return a mock string response for query reframing
                return "expert insurance terminology query reframe"
            
            # Call the LLM directly for string response
            response = self.llm(prompt)
            return response
        except Exception as e:
            self.logger.error(f"Error calling LLM: {e}")
            # Return fallback response
            return "expert insurance terminology query reframe"
    
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Process method for integration with supervisor workflow.
        
        Args:
            input_data: Structured input from supervisor workflow
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Convert input to InformationRetrievalInput
            if isinstance(input_data, dict):
                input_model = InformationRetrievalInput(**input_data)
            elif isinstance(input_data, InformationRetrievalInput):
                input_model = input_data
            else:
                raise ValueError(f"Unsupported input type: {type(input_data)}")
            
            # Process the request
            result = asyncio.run(self.retrieve_information(input_model))
            
            # Convert to dictionary for supervisor workflow
            return result.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error in process method: {e}")
            return {
                "error": str(e),
                "status": "error",
                "expert_reframe": "",
                "direct_answer": "An error occurred while processing your request.",
                "key_points": [],
                "confidence_score": 0.0,
                "source_chunks": []
            } 

    def mock_output(self, user_input: str) -> InformationRetrievalOutput:
        """
        Generate a mock output matching the InformationRetrievalOutput schema.
        
        Args:
            user_input: The user's query input
            
        Returns:
            Mock InformationRetrievalOutput with valid data types
        """
        # Generate realistic mock data with proper types
        mock_data = {
            "expert_reframe": f"mock_expert_reframe for: {user_input[:50]}...",
            "direct_answer": f"Mock answer for: {user_input[:50]}...",
            "key_points": ["mock_key_point_1", "mock_key_point_2", "mock_key_point_3"],
            "confidence_score": 0.85,  # Float between 0.0 and 1.0
            "source_chunks": [],  # Empty list of SourceChunk objects
            "processing_steps": ["step1", "step2", "step3"],  # List of strings
            "error_message": None  # Optional string
        }
        
        return InformationRetrievalOutput(**mock_data) 