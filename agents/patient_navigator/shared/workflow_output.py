"""
Workflow Output Abstraction Layer

This module provides a flexible, agnostic interface for workflow outputs,
allowing different workflows to return their natural output format while
enabling consistent processing by the output processing workflow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class WorkflowOutputType(str, Enum):
    """Types of workflow outputs supported by the system."""
    INFORMATION_RETRIEVAL = "information_retrieval"
    STRATEGY = "strategy"
    REGULATORY = "regulatory"
    COMMUNICATION = "communication"


class WorkflowOutput(BaseModel, ABC):
    """
    Abstract base class for all workflow outputs.
    
    This provides a common interface while allowing workflows to return
    their natural output format with rich semantic information.
    """
    
    workflow_type: WorkflowOutputType = Field(description="Type of workflow that generated this output")
    content: Dict[str, Any] = Field(description="Main content of the workflow output")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score for this output")
    
    @abstractmethod
    def extract_key_information(self) -> Dict[str, Any]:
        """Extract key information for output processing."""
        pass
    
    @abstractmethod
    def get_summary(self) -> str:
        """Get a human-readable summary of the output."""
        pass
    
    @abstractmethod
    def get_actionable_items(self) -> List[str]:
        """Get actionable items from the output."""
        pass


class InformationRetrievalWorkflowOutput(WorkflowOutput):
    """Output from information retrieval workflow."""
    
    workflow_type: WorkflowOutputType = WorkflowOutputType.INFORMATION_RETRIEVAL
    
    def extract_key_information(self) -> Dict[str, Any]:
        """Extract key information from information retrieval output."""
        return {
            "expert_reframe": self.content.get("expert_reframe", ""),
            "direct_answer": self.content.get("direct_answer", ""),
            "key_points": self.content.get("key_points", []),
            "source_chunks": self.content.get("source_chunks", []),
            "processing_steps": self.content.get("processing_steps", [])
        }
    
    def get_summary(self) -> str:
        """Get summary of information retrieval output."""
        return self.content.get("direct_answer", "No information retrieved")
    
    def get_actionable_items(self) -> List[str]:
        """Get actionable items from information retrieval output."""
        return self.content.get("key_points", [])


class StrategyWorkflowOutput(WorkflowOutput):
    """Output from strategy workflow."""
    
    workflow_type: WorkflowOutputType = WorkflowOutputType.STRATEGY
    
    def extract_key_information(self) -> Dict[str, Any]:
        """Extract key information from strategy output."""
        strategies = self.content.get("strategies", [])
        return {
            "strategies": strategies,
            "strategy_count": len(strategies),
            "optimization_types": [s.get("category", "unknown") for s in strategies],
            "actionable_steps": self._extract_all_actionable_steps(strategies),
            "approaches": [s.get("approach", "") for s in strategies],
            "rationales": [s.get("rationale", "") for s in strategies]
        }
    
    def get_summary(self) -> str:
        """Get summary of strategy output."""
        strategies = self.content.get("strategies", [])
        if not strategies:
            return "No strategies generated"
        
        # Create a comprehensive summary
        summary_parts = []
        for i, strategy in enumerate(strategies, 1):
            title = strategy.get("title", f"Strategy {i}")
            approach = strategy.get("approach", "")
            summary_parts.append(f"{i}. {title}: {approach}")
        
        return "Generated strategies:\n" + "\n".join(summary_parts)
    
    def get_actionable_items(self) -> List[str]:
        """Get actionable items from strategy output."""
        strategies = self.content.get("strategies", [])
        return self._extract_all_actionable_steps(strategies)
    
    def _extract_all_actionable_steps(self, strategies: List[Dict[str, Any]]) -> List[str]:
        """Extract all actionable steps from all strategies."""
        all_steps = []
        for strategy in strategies:
            steps = strategy.get("actionable_steps", [])
            if isinstance(steps, list):
                all_steps.extend(steps)
        return all_steps


class RegulatoryWorkflowOutput(WorkflowOutput):
    """Output from regulatory workflow."""
    
    workflow_type: WorkflowOutputType = WorkflowOutputType.REGULATORY
    
    def extract_key_information(self) -> Dict[str, Any]:
        """Extract key information from regulatory output."""
        return {
            "compliance_status": self.content.get("compliance_status", "unknown"),
            "validation_reasons": self.content.get("validation_reasons", []),
            "confidence_score": self.content.get("confidence_score", 0.0),
            "source_references": self.content.get("source_references", [])
        }
    
    def get_summary(self) -> str:
        """Get summary of regulatory output."""
        status = self.content.get("compliance_status", "unknown")
        return f"Regulatory compliance status: {status}"
    
    def get_actionable_items(self) -> List[str]:
        """Get actionable items from regulatory output."""
        reasons = self.content.get("validation_reasons", [])
        return [reason.get("description", "") for reason in reasons if isinstance(reason, dict)]


class CommunicationWorkflowOutput(WorkflowOutput):
    """Output from communication workflow."""
    
    workflow_type: WorkflowOutputType = WorkflowOutputType.COMMUNICATION
    
    def extract_key_information(self) -> Dict[str, Any]:
        """Extract key information from communication output."""
        return {
            "enhanced_content": self.content.get("enhanced_content", ""),
            "original_sources": self.content.get("original_sources", []),
            "metadata": self.content.get("metadata", {}),
            "tone_applied": self.content.get("metadata", {}).get("tone_applied", "unknown")
        }
    
    def get_summary(self) -> str:
        """Get summary of communication output."""
        return self.content.get("enhanced_content", "No communication content")
    
    def get_actionable_items(self) -> List[str]:
        """Get actionable items from communication output."""
        # Communication output typically doesn't have actionable items
        # but we can extract any next steps mentioned in the content
        content = self.content.get("enhanced_content", "")
        # Simple extraction of bullet points or numbered lists
        lines = content.split('\n')
        actionable = []
        for line in lines:
            line = line.strip()
            if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
                actionable.append(line)
        return actionable


class WorkflowOutputProcessor:
    """
    Agnostic processor for workflow outputs.
    
    This processor can handle any workflow output type and extract
    meaningful information for final response synthesis.
    """
    
    def __init__(self):
        self.processors = {
            WorkflowOutputType.INFORMATION_RETRIEVAL: self._process_information_retrieval,
            WorkflowOutputType.STRATEGY: self._process_strategy,
            WorkflowOutputType.REGULATORY: self._process_regulatory,
            WorkflowOutputType.COMMUNICATION: self._process_communication
        }
    
    async def process(self, workflow_output: WorkflowOutput) -> Dict[str, Any]:
        """
        Process any workflow output type and extract meaningful information.
        
        Args:
            workflow_output: Any workflow output instance
            
        Returns:
            Processed information ready for final response synthesis
        """
        processor = self.processors.get(workflow_output.workflow_type)
        if not processor:
            return self._process_generic(workflow_output)
        
        return await processor(workflow_output)
    
    async def _process_information_retrieval(self, output: InformationRetrievalWorkflowOutput) -> Dict[str, Any]:
        """Process information retrieval output."""
        key_info = output.extract_key_information()
        return {
            "content_type": "information_retrieval",
            "summary": output.get_summary(),
            "actionable_items": output.get_actionable_items(),
            "expert_reframe": key_info["expert_reframe"],
            "direct_answer": key_info["direct_answer"],
            "key_points": key_info["key_points"],
            "source_chunks": key_info["source_chunks"],
            "processing_steps": key_info["processing_steps"],
            "confidence_score": output.confidence_score
        }
    
    async def _process_strategy(self, output: StrategyWorkflowOutput) -> Dict[str, Any]:
        """Process strategy output."""
        key_info = output.extract_key_information()
        return {
            "content_type": "strategy",
            "summary": output.get_summary(),
            "actionable_items": output.get_actionable_items(),
            "strategies": key_info["strategies"],
            "strategy_count": key_info["strategy_count"],
            "optimization_types": key_info["optimization_types"],
            "approaches": key_info["approaches"],
            "rationales": key_info["rationales"],
            "confidence_score": output.confidence_score
        }
    
    async def _process_regulatory(self, output: RegulatoryWorkflowOutput) -> Dict[str, Any]:
        """Process regulatory output."""
        key_info = output.extract_key_information()
        return {
            "content_type": "regulatory",
            "summary": output.get_summary(),
            "actionable_items": output.get_actionable_items(),
            "compliance_status": key_info["compliance_status"],
            "validation_reasons": key_info["validation_reasons"],
            "source_references": key_info["source_references"],
            "confidence_score": output.confidence_score
        }
    
    async def _process_communication(self, output: CommunicationWorkflowOutput) -> Dict[str, Any]:
        """Process communication output."""
        key_info = output.extract_key_information()
        return {
            "content_type": "communication",
            "summary": output.get_summary(),
            "actionable_items": output.get_actionable_items(),
            "enhanced_content": key_info["enhanced_content"],
            "original_sources": key_info["original_sources"],
            "tone_applied": key_info["tone_applied"],
            "confidence_score": output.confidence_score
        }
    
    async def _process_generic(self, output: WorkflowOutput) -> Dict[str, Any]:
        """Process generic workflow output."""
        return {
            "content_type": "generic",
            "summary": output.get_summary(),
            "actionable_items": output.get_actionable_items(),
            "raw_content": output.content,
            "confidence_score": output.confidence_score
        }


def create_workflow_output(workflow_type: WorkflowOutputType, content: Dict[str, Any], 
                          confidence_score: float = 0.8, metadata: Optional[Dict[str, Any]] = None) -> WorkflowOutput:
    """
    Factory function to create workflow output instances.
    
    Args:
        workflow_type: Type of workflow output
        content: Main content of the output
        confidence_score: Confidence score (0.0-1.0)
        metadata: Additional metadata
        
    Returns:
        Appropriate workflow output instance
    """
    if metadata is None:
        metadata = {}
    
    if workflow_type == WorkflowOutputType.INFORMATION_RETRIEVAL:
        return InformationRetrievalWorkflowOutput(
            content=content,
            confidence_score=confidence_score,
            metadata=metadata
        )
    elif workflow_type == WorkflowOutputType.STRATEGY:
        return StrategyWorkflowOutput(
            content=content,
            confidence_score=confidence_score,
            metadata=metadata
        )
    elif workflow_type == WorkflowOutputType.REGULATORY:
        return RegulatoryWorkflowOutput(
            content=content,
            confidence_score=confidence_score,
            metadata=metadata
        )
    elif workflow_type == WorkflowOutputType.COMMUNICATION:
        return CommunicationWorkflowOutput(
            content=content,
            confidence_score=confidence_score,
            metadata=metadata
        )
    else:
        raise ValueError(f"Unsupported workflow type: {workflow_type}")
