"""
Two-Stage Output Synthesizer

This module provides a sophisticated two-stage approach to processing workflow outputs:
1. Stage 1: Content Extraction and Analysis
2. Stage 2: Human-Readable Formatting and Synthesis

The goal is to separate technical content processing from human presentation,
making the system more maintainable and the output more natural.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .types import AgentOutput, CommunicationRequest, CommunicationResponse
from .agent import CommunicationAgent

logger = logging.getLogger(__name__)

class ContentType(str, Enum):
    """Types of content that can be processed."""
    INFORMATION_RETRIEVAL = "information_retrieval"
    STRATEGY_GUIDANCE = "strategy_guidance"
    BENEFITS_EXPLANATION = "benefits_explanation"
    PROCEDURAL_GUIDANCE = "procedural_guidance"
    ERROR_RESPONSE = "error_response"
    MIXED_CONTENT = "mixed_content"

@dataclass
class ExtractedContent:
    """Structured representation of extracted content from workflow outputs."""
    content_type: ContentType
    main_topic: str
    key_points: List[str]
    actionable_steps: List[str]
    specific_details: Dict[str, Any]
    confidence_score: float
    source_workflows: List[str]
    metadata: Dict[str, Any]

@dataclass
class FormattedResponse:
    """Human-readable formatted response."""
    content: str
    content_type: ContentType
    confidence: float
    sources: List[str]
    metadata: Dict[str, Any]

class StageOneContentExtractor:
    """
    Stage 1: Content Extraction and Analysis
    
    This stage focuses on:
    - Extracting meaningful content from workflow outputs
    - Analyzing content type and structure
    - Identifying key information and actionable items
    - Determining confidence and relevance
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.StageOneContentExtractor")
    
    def extract_content(self, agent_outputs: List[AgentOutput]) -> ExtractedContent:
        """
        Extract and analyze content from agent outputs.
        
        Args:
            agent_outputs: List of agent outputs to process
            
        Returns:
            ExtractedContent: Structured representation of the content
        """
        self.logger.info(f"Stage 1: Extracting content from {len(agent_outputs)} agent outputs")
        
        # Analyze each agent output
        all_content = []
        all_key_points = []
        all_actionable_steps = []
        source_workflows = []
        confidence_scores = []
        
        for output in agent_outputs:
            source_workflows.append(output.agent_id)
            
            # Extract content based on agent type
            if output.agent_id == "information_retrieval":
                content_data = self._extract_information_retrieval_content(output)
            elif output.agent_id == "strategy":
                content_data = self._extract_strategy_content(output)
            else:
                content_data = self._extract_generic_content(output)
            
            all_content.append(content_data)
            all_key_points.extend(content_data.get("key_points", []))
            all_actionable_steps.extend(content_data.get("actionable_steps", []))
            confidence_scores.append(content_data.get("confidence", 0.0))
        
        # Determine content type
        content_type = self._determine_content_type(all_content, agent_outputs)
        
        # Extract main topic
        main_topic = self._extract_main_topic(all_content, agent_outputs)
        
        # Consolidate specific details
        specific_details = self._consolidate_specific_details(all_content)
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return ExtractedContent(
            content_type=content_type,
            main_topic=main_topic,
            key_points=all_key_points,
            actionable_steps=all_actionable_steps,
            specific_details=specific_details,
            confidence_score=overall_confidence,
            source_workflows=source_workflows,
            metadata={"extraction_method": "two_stage", "stage": "content_extraction"}
        )
    
    def _extract_information_retrieval_content(self, output: AgentOutput) -> Dict[str, Any]:
        """Extract content from information retrieval agent output."""
        try:
            # Try to parse as JSON first
            if output.content.startswith('{'):
                content_data = json.loads(output.content)
                return {
                    "key_points": content_data.get("key_points", []),
                    "actionable_steps": content_data.get("actionable_steps", []),
                    "specific_details": content_data.get("specific_details", {}),
                    "confidence": content_data.get("confidence_score", 0.0),
                    "content_type": "information_retrieval"
                }
            else:
                # Fallback to text parsing
                return {
                    "key_points": [output.content],
                    "actionable_steps": [],
                    "specific_details": {},
                    "confidence": output.metadata.get("confidence_score", 0.0),
                    "content_type": "information_retrieval"
                }
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse information retrieval content: {e}")
            return {
                "key_points": [output.content],
                "actionable_steps": [],
                "specific_details": {},
                "confidence": 0.0,
                "content_type": "information_retrieval"
            }
    
    def _extract_strategy_content(self, output: AgentOutput) -> Dict[str, Any]:
        """Extract content from strategy agent output."""
        try:
            if output.content.startswith('{'):
                content_data = json.loads(output.content)
                strategies = content_data.get("strategies", [])
                return {
                    "key_points": [s.get("title", "") for s in strategies],
                    "actionable_steps": [step for s in strategies for step in s.get("actionable_steps", [])],
                    "specific_details": {"strategies": strategies},
                    "confidence": content_data.get("confidence_score", 0.0),
                    "content_type": "strategy_guidance"
                }
            else:
                return {
                    "key_points": [output.content],
                    "actionable_steps": [],
                    "specific_details": {},
                    "confidence": output.metadata.get("confidence_score", 0.0),
                    "content_type": "strategy_guidance"
                }
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse strategy content: {e}")
            return {
                "key_points": [output.content],
                "actionable_steps": [],
                "specific_details": {},
                "confidence": 0.0,
                "content_type": "strategy_guidance"
            }
    
    def _extract_generic_content(self, output: AgentOutput) -> Dict[str, Any]:
        """Extract content from generic agent output."""
        return {
            "key_points": [output.content],
            "actionable_steps": [],
            "specific_details": {},
            "confidence": output.metadata.get("confidence_score", 0.0),
            "content_type": "generic"
        }
    
    def _determine_content_type(self, content_data: List[Dict], agent_outputs: List[AgentOutput]) -> ContentType:
        """Determine the overall content type based on extracted content."""
        # Check for specific content types
        if any("x-ray" in str(content).lower() or "radiology" in str(content).lower() for content in content_data):
            return ContentType.PROCEDURAL_GUIDANCE
        elif any("deductible" in str(content).lower() or "copay" in str(content).lower() for content in content_data):
            return ContentType.BENEFITS_EXPLANATION
        elif any(content.get("content_type") == "strategy_guidance" for content in content_data):
            return ContentType.STRATEGY_GUIDANCE
        elif any(content.get("content_type") == "information_retrieval" for content in content_data):
            return ContentType.INFORMATION_RETRIEVAL
        else:
            return ContentType.MIXED_CONTENT
    
    def _extract_main_topic(self, content_data: List[Dict], agent_outputs: List[AgentOutput]) -> str:
        """Extract the main topic from the content."""
        # Look for common topics in the content
        topics = []
        for content in content_data:
            if "x-ray" in str(content).lower():
                topics.append("x-ray procedure")
            elif "deductible" in str(content).lower():
                topics.append("insurance deductible")
            elif "coverage" in str(content).lower():
                topics.append("insurance coverage")
        
        return topics[0] if topics else "general insurance inquiry"
    
    def _consolidate_specific_details(self, content_data: List[Dict]) -> Dict[str, Any]:
        """Consolidate specific details from all content."""
        details = {}
        for content in content_data:
            specific_details = content.get("specific_details", {})
            details.update(specific_details)
        return details

class StageTwoHumanFormatter:
    """
    Stage 2: Human-Readable Formatting and Synthesis
    
    This stage focuses on:
    - Converting extracted content into natural language
    - Applying appropriate tone and style
    - Structuring information for optimal readability
    - Ensuring responses feel conversational and helpful
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.StageTwoHumanFormatter")
        self.communication_agent = CommunicationAgent()
    
    async def format_response(self, extracted_content: ExtractedContent, user_context: Dict[str, Any]) -> FormattedResponse:
        """
        Format extracted content into human-readable response.
        
        Args:
            extracted_content: Structured content from Stage 1
            user_context: User context for personalization
            
        Returns:
            FormattedResponse: Human-readable formatted response
        """
        self.logger.info(f"Stage 2: Formatting {extracted_content.content_type.value} content")
        
        # Create agent output for communication agent
        agent_output = AgentOutput(
            agent_id="two_stage_synthesizer",
            content=self._create_structured_content(extracted_content),
            metadata={
                "content_type": extracted_content.content_type.value,
                "main_topic": extracted_content.main_topic,
                "confidence_score": extracted_content.confidence_score,
                "source_workflows": extracted_content.source_workflows
            }
        )
        
        # Use communication agent for final formatting
        request = CommunicationRequest(
            agent_outputs=[agent_output],
            user_context=user_context
        )
        
        try:
            self.logger.info("=== CALLING COMMUNICATION AGENT ENHANCE_RESPONSE ===")
            self.logger.info(f"Communication request prepared with {len(request.agent_outputs)} agent outputs")
            self.logger.info(f"User context provided: {bool(request.user_context)}")
            
            response = await self.communication_agent.enhance_response(request)
            self.logger.info("=== COMMUNICATION AGENT ENHANCE_RESPONSE COMPLETED SUCCESSFULLY ===")
            self.logger.info(f"Enhanced response length: {len(response.enhanced_content)} characters")
            
            return FormattedResponse(
                content=response.enhanced_content,
                content_type=extracted_content.content_type,
                confidence=extracted_content.confidence_score,
                sources=extracted_content.source_workflows,
                metadata={
                    "processing_method": "two_stage_synthesizer",
                    "stage_one_complete": True,
                    "stage_two_complete": True,
                    **extracted_content.metadata
                }
            )
        except Exception as e:
            self.logger.error(f"Communication agent failed: {e}")
            self.logger.error(f"Communication agent error type: {type(e).__name__}")
            return self._create_fallback_response(extracted_content)
    
    def _create_structured_content(self, extracted_content: ExtractedContent) -> str:
        """Create structured content string for communication agent."""
        content_parts = []
        
        # Add main topic
        content_parts.append(f"Main Topic: {extracted_content.main_topic}")
        
        # Add key points
        if extracted_content.key_points:
            content_parts.append("Key Information:")
            for i, point in enumerate(extracted_content.key_points, 1):
                content_parts.append(f"{i}. {point}")
        
        # Add actionable steps
        if extracted_content.actionable_steps:
            content_parts.append("Actionable Steps:")
            for i, step in enumerate(extracted_content.actionable_steps, 1):
                content_parts.append(f"{i}. {step}")
        
        # Add specific details
        if extracted_content.specific_details:
            content_parts.append("Specific Details:")
            for key, value in extracted_content.specific_details.items():
                if isinstance(value, (str, int, float)):
                    content_parts.append(f"- {key}: {value}")
                elif isinstance(value, list):
                    content_parts.append(f"- {key}: {', '.join(map(str, value))}")
        
        return "\n".join(content_parts)
    
    def _create_fallback_response(self, extracted_content: ExtractedContent) -> FormattedResponse:
        """Create fallback response when communication agent fails."""
        content = f"I can help you with {extracted_content.main_topic}. "
        
        if extracted_content.key_points:
            content += "Here's what I found: " + ". ".join(extracted_content.key_points[:3]) + "."
        
        if extracted_content.actionable_steps:
            content += " Here are the steps you can take: " + ". ".join(extracted_content.actionable_steps[:3]) + "."
        
        return FormattedResponse(
            content=content,
            content_type=extracted_content.content_type,
            confidence=extracted_content.confidence_score,
            sources=extracted_content.source_workflows,
            metadata={"fallback": True, "error": "communication_agent_failed"}
        )

class TwoStageOutputSynthesizer:
    """
    Main orchestrator for the two-stage output synthesis process.
    
    This class coordinates between Stage 1 (content extraction) and Stage 2 (human formatting)
    to provide a sophisticated approach to processing workflow outputs.
    """
    
    def __init__(self):
        self.stage_one = StageOneContentExtractor()
        self.stage_two = StageTwoHumanFormatter()
        self.logger = logging.getLogger(f"{__name__}.TwoStageOutputSynthesizer")
    
    async def synthesize_outputs(
        self, 
        agent_outputs: List[AgentOutput], 
        user_context: Dict[str, Any]
    ) -> CommunicationResponse:
        """
        Synthesize agent outputs using the two-stage approach.
        
        Args:
            agent_outputs: List of agent outputs to process
            user_context: User context for personalization
            
        Returns:
            CommunicationResponse: Final synthesized response
        """
        self.logger.info("=== TWO-STAGE SYNTHESIZER CALLED ===")
        self.logger.info(f"Starting two-stage synthesis for {len(agent_outputs)} agent outputs")
        self.logger.info(f"Agent outputs: {[output.agent_id for output in agent_outputs]}")
        
        try:
            # Stage 1: Extract and analyze content
            self.logger.info("Stage 1: Starting content extraction")
            extracted_content = self.stage_one.extract_content(agent_outputs)
            self.logger.info(f"Stage 1 complete: {extracted_content.content_type.value} content extracted")
            self.logger.info(f"Extracted content - Main topic: {extracted_content.main_topic}")
            self.logger.info(f"Extracted content - Key points count: {len(extracted_content.key_points)}")
            self.logger.info(f"Extracted content - Confidence: {extracted_content.confidence_score}")
            
            # Stage 2: Format for human consumption
            self.logger.info("Stage 2: Starting human-readable formatting")
            formatted_response = await self.stage_two.format_response(extracted_content, user_context)
            self.logger.info(f"Stage 2 complete: Response formatted for {formatted_response.content_type.value}")
            self.logger.info(f"Formatted response - Content length: {len(formatted_response.content)} characters")
            self.logger.info(f"Formatted response - Confidence: {formatted_response.confidence}")
            
            # Create final response
            return CommunicationResponse(
                enhanced_content=formatted_response.content,
                original_sources=formatted_response.sources,
                processing_time=0.0,  # Will be calculated by the system
                metadata={
                    **formatted_response.metadata,
                    "confidence": formatted_response.confidence
                }
            )
            
        except Exception as e:
            self.logger.error(f"Two-stage synthesis failed: {e}")
            return self._create_error_response(agent_outputs, str(e))
    
    def _create_error_response(self, agent_outputs: List[AgentOutput], error: str) -> CommunicationResponse:
        """Create error response when synthesis fails."""
        return CommunicationResponse(
            enhanced_content="I encountered an issue while processing your request. Please try again, and I'll do my best to help you with your insurance questions.",
            original_sources=[output.agent_id for output in agent_outputs],
            confidence=0.0,
            processing_time=0.0,
            metadata={"error": error, "fallback": True}
        )
