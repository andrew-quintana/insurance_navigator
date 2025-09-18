"""
Agnostic Output Processing Workflow

This module provides workflow-agnostic output processing that can handle
any workflow output type and synthesize meaningful responses without
forcing workflows to conform to a specific output format.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union
from agents.patient_navigator.shared.workflow_output import (
    WorkflowOutput, 
    WorkflowOutputProcessor,
    WorkflowOutputType,
    create_workflow_output
)

logger = logging.getLogger(__name__)


class AgnosticOutputProcessor:
    """
    Agnostic output processor that can handle any workflow output type.
    
    This processor extracts meaningful information from any workflow output
    and synthesizes it into a coherent response without forcing format conversion.
    """
    
    def __init__(self):
        self.workflow_processor = WorkflowOutputProcessor()
        self.logger = logging.getLogger(__name__)
    
    async def process_workflow_outputs(
        self, 
        workflow_outputs: List[WorkflowOutput],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process multiple workflow outputs and synthesize a coherent response.
        
        Args:
            workflow_outputs: List of workflow outputs to process
            user_context: Optional user context for personalization
            
        Returns:
            Synthesized response with enhanced content and metadata
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing {len(workflow_outputs)} workflow outputs")
            
            # Process each workflow output
            processed_outputs = []
            for output in workflow_outputs:
                processed = await self.workflow_processor.process(output)
                processed_outputs.append(processed)
            
            # Synthesize the processed outputs
            synthesized_response = await self._synthesize_outputs(
                processed_outputs, 
                user_context
            )
            
            processing_time = time.time() - start_time
            synthesized_response["processing_time"] = processing_time
            
            self.logger.info(f"Successfully processed outputs in {processing_time:.2f}s")
            return synthesized_response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error processing workflow outputs: {e}")
            
            return {
                "enhanced_content": "I encountered an error while processing your request. Please try again.",
                "original_sources": [output.workflow_type.value for output in workflow_outputs],
                "processing_time": processing_time,
                "metadata": {
                    "error": str(e),
                    "content_type": "error",
                    "workflow_count": len(workflow_outputs)
                }
            }
    
    async def _synthesize_outputs(
        self, 
        processed_outputs: List[Dict[str, Any]], 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesize multiple processed outputs into a coherent response.
        
        Args:
            processed_outputs: List of processed workflow outputs
            user_context: Optional user context for personalization
            
        Returns:
            Synthesized response
        """
        # Group outputs by content type
        content_groups = self._group_by_content_type(processed_outputs)
        
        # Extract key information from each group
        synthesis_data = {
            "information_retrieval": self._extract_information_retrieval_data(content_groups),
            "strategy": self._extract_strategy_data(content_groups),
            "regulatory": self._extract_regulatory_data(content_groups),
            "communication": self._extract_communication_data(content_groups)
        }
        
        # Generate enhanced content
        enhanced_content = await self._generate_enhanced_content(synthesis_data, user_context)
        
        # Extract original sources
        original_sources = [output.get("content_type", "unknown") for output in processed_outputs]
        
        # Calculate overall confidence
        confidence_scores = [output.get("confidence_score", 0.0) for output in processed_outputs]
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "enhanced_content": enhanced_content,
            "original_sources": original_sources,
            "confidence_score": overall_confidence,
            "metadata": {
                "content_groups": list(content_groups.keys()),
                "synthesis_data": synthesis_data,
                "user_context_provided": user_context is not None,
                "workflow_count": len(processed_outputs)
            }
        }
    
    def _group_by_content_type(self, processed_outputs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group processed outputs by content type."""
        groups = {}
        for output in processed_outputs:
            content_type = output.get("content_type", "unknown")
            if content_type not in groups:
                groups[content_type] = []
            groups[content_type].append(output)
        return groups
    
    def _extract_information_retrieval_data(self, content_groups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Extract information retrieval data from content groups."""
        info_outputs = content_groups.get("information_retrieval", [])
        if not info_outputs:
            return {}
        
        # Combine all information retrieval data
        combined_data = {
            "expert_reframes": [],
            "direct_answers": [],
            "key_points": [],
            "source_chunks": [],
            "processing_steps": []
        }
        
        for output in info_outputs:
            combined_data["expert_reframes"].append(output.get("expert_reframe", ""))
            combined_data["direct_answers"].append(output.get("direct_answer", ""))
            combined_data["key_points"].extend(output.get("key_points", []))
            combined_data["source_chunks"].extend(output.get("source_chunks", []))
            combined_data["processing_steps"].extend(output.get("processing_steps", []))
        
        return combined_data
    
    def _extract_strategy_data(self, content_groups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Extract strategy data from content groups."""
        strategy_outputs = content_groups.get("strategy", [])
        if not strategy_outputs:
            return {}
        
        # Combine all strategy data
        combined_data = {
            "strategies": [],
            "actionable_steps": [],
            "approaches": [],
            "rationales": [],
            "optimization_types": []
        }
        
        for output in strategy_outputs:
            combined_data["strategies"].extend(output.get("strategies", []))
            combined_data["actionable_steps"].extend(output.get("actionable_items", []))
            combined_data["approaches"].extend(output.get("approaches", []))
            combined_data["rationales"].extend(output.get("rationales", []))
            combined_data["optimization_types"].extend(output.get("optimization_types", []))
        
        return combined_data
    
    def _extract_regulatory_data(self, content_groups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Extract regulatory data from content groups."""
        regulatory_outputs = content_groups.get("regulatory", [])
        if not regulatory_outputs:
            return {}
        
        # Combine all regulatory data
        combined_data = {
            "compliance_statuses": [],
            "validation_reasons": [],
            "source_references": []
        }
        
        for output in regulatory_outputs:
            combined_data["compliance_statuses"].append(output.get("compliance_status", "unknown"))
            combined_data["validation_reasons"].extend(output.get("validation_reasons", []))
            combined_data["source_references"].extend(output.get("source_references", []))
        
        return combined_data
    
    def _extract_communication_data(self, content_groups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Extract communication data from content groups."""
        communication_outputs = content_groups.get("communication", [])
        if not communication_outputs:
            return {}
        
        # Combine all communication data
        combined_data = {
            "enhanced_contents": [],
            "original_sources": [],
            "tones_applied": []
        }
        
        for output in communication_outputs:
            combined_data["enhanced_contents"].append(output.get("enhanced_content", ""))
            combined_data["original_sources"].extend(output.get("original_sources", []))
            combined_data["tones_applied"].append(output.get("tone_applied", "unknown"))
        
        return combined_data
    
    async def _generate_enhanced_content(
        self, 
        synthesis_data: Dict[str, Any], 
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate enhanced content from synthesis data.
        
        This method creates a coherent response by combining information
        from different workflow types in a meaningful way.
        """
        content_parts = []
        
        # Start with information retrieval content if available
        if synthesis_data.get("information_retrieval"):
            info_data = synthesis_data["information_retrieval"]
            if info_data.get("direct_answers"):
                # Use the most comprehensive direct answer
                best_answer = max(info_data["direct_answers"], key=len)
                content_parts.append(best_answer)
            
            # Add key points if available
            if info_data.get("key_points"):
                key_points = info_data["key_points"][:5]  # Limit to top 5
                if key_points:
                    content_parts.append("\n**Key Points:**")
                    for i, point in enumerate(key_points, 1):
                        content_parts.append(f"{i}. {point}")
        
        # Add strategy content if available
        if synthesis_data.get("strategy"):
            strategy_data = synthesis_data["strategy"]
            if strategy_data.get("strategies"):
                content_parts.append("\n**Recommended Strategies:**")
                for i, strategy in enumerate(strategy_data["strategies"][:3], 1):  # Limit to top 3
                    title = strategy.get("title", f"Strategy {i}")
                    approach = strategy.get("approach", "")
                    content_parts.append(f"\n{i}. **{title}**")
                    content_parts.append(f"   {approach}")
                
                # Add actionable steps
                if strategy_data.get("actionable_steps"):
                    content_parts.append("\n**Actionable Steps:**")
                    for i, step in enumerate(strategy_data["actionable_steps"][:5], 1):  # Limit to top 5
                        content_parts.append(f"{i}. {step}")
        
        # Add regulatory content if available
        if synthesis_data.get("regulatory"):
            regulatory_data = synthesis_data["regulatory"]
            if regulatory_data.get("compliance_statuses"):
                statuses = regulatory_data["compliance_statuses"]
                if statuses:
                    content_parts.append(f"\n**Regulatory Status:** {statuses[0]}")
        
        # If no content was generated, provide a fallback
        if not content_parts:
            content_parts.append("I've processed your request, but I need more information to provide a comprehensive response. Please try rephrasing your question or providing more context.")
        
        return "\n".join(content_parts)


class WorkflowOutputConverter:
    """
    Converter for legacy workflow outputs to new agnostic format.
    
    This handles the transition from tightly coupled output formats
    to the new agnostic workflow output system.
    """
    
    @staticmethod
    def convert_information_retrieval_output(
        legacy_output: Any, 
        confidence_score: float = 0.8
    ) -> WorkflowOutput:
        """
        Convert legacy InformationRetrievalOutput to new format.
        
        Args:
            legacy_output: Legacy InformationRetrievalOutput instance
            confidence_score: Confidence score for the output
            
        Returns:
            New WorkflowOutput instance
        """
        content = {
            "expert_reframe": getattr(legacy_output, "expert_reframe", ""),
            "direct_answer": getattr(legacy_output, "direct_answer", ""),
            "key_points": getattr(legacy_output, "key_points", []),
            "source_chunks": getattr(legacy_output, "source_chunks", []),
            "processing_steps": getattr(legacy_output, "processing_steps", [])
        }
        
        metadata = {
            "legacy_format": "InformationRetrievalOutput",
            "conversion_timestamp": time.time()
        }
        
        return create_workflow_output(
            WorkflowOutputType.INFORMATION_RETRIEVAL,
            content,
            confidence_score,
            metadata
        )
    
    @staticmethod
    def convert_strategy_output(
        strategies: List[Any], 
        confidence_score: float = 0.8
    ) -> WorkflowOutput:
        """
        Convert strategy objects to new format.
        
        Args:
            strategies: List of strategy objects
            confidence_score: Confidence score for the output
            
        Returns:
            New WorkflowOutput instance
        """
        # Convert strategy objects to dictionaries
        strategy_dicts = []
        for strategy in strategies:
            if hasattr(strategy, '__dict__'):
                strategy_dict = strategy.__dict__
            elif isinstance(strategy, dict):
                strategy_dict = strategy
            else:
                strategy_dict = {"title": str(strategy), "approach": "", "actionable_steps": []}
            
            strategy_dicts.append(strategy_dict)
        
        content = {
            "strategies": strategy_dicts,
            "strategy_count": len(strategy_dicts)
        }
        
        metadata = {
            "legacy_format": "StrategyObjects",
            "conversion_timestamp": time.time()
        }
        
        return create_workflow_output(
            WorkflowOutputType.STRATEGY,
            content,
            confidence_score,
            metadata
        )
