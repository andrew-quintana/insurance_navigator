"""
Models for the Regulatory Evaluation Agent.

This module defines the Pydantic models used by the Regulatory Agent for evaluating
service access strategies against regulatory requirements.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class RegulatoryDocument(BaseModel):
    """Schema for a relevant regulatory document."""
    document_id: str = Field(description="Unique identifier for the document")
    title: str = Field(description="Document title")
    jurisdiction: str = Field(description="Jurisdiction level (federal/state/county)")
    program: str = Field(description="Related program")
    document_type: str = Field(description="Type of document (regulation/policy/guidance)")
    effective_date: datetime = Field(description="When the document became effective")
    relevant_sections: List[str] = Field(
        description="Relevant sections for the evaluation",
        default_factory=list
    )
    citations: List[str] = Field(
        description="Specific citations used in evaluation",
        default_factory=list
    )

class ComplianceIssue(BaseModel):
    """Schema for identified compliance issues."""
    issue_type: str = Field(description="Type of compliance issue")
    severity: str = Field(description="Severity level (high/medium/low)")
    description: str = Field(description="Description of the issue")
    affected_components: List[str] = Field(
        description="Components of strategy affected",
        default_factory=list
    )
    suggested_modifications: List[str] = Field(
        description="Suggested modifications to achieve compliance",
        default_factory=list
    )
    regulatory_basis: List[str] = Field(
        description="Citations supporting the issue identification",
        default_factory=list
    )

class AlternativeApproach(BaseModel):
    """Schema for suggested alternative approaches."""
    approach_name: str = Field(description="Name of the alternative approach")
    description: str = Field(description="Description of the approach")
    advantages: List[str] = Field(
        description="Advantages of this approach",
        default_factory=list
    )
    disadvantages: List[str] = Field(
        description="Disadvantages of this approach",
        default_factory=list
    )
    compliance_score: float = Field(
        description="Compliance score from 0-1",
        ge=0,
        le=1
    )
    regulatory_support: List[str] = Field(
        description="Citations supporting this approach",
        default_factory=list
    )

class ImplementationStep(BaseModel):
    """Schema for implementation steps."""
    step_number: int = Field(description="Sequence number")
    description: str = Field(description="Step description")
    regulatory_requirements: List[str] = Field(
        description="Regulatory requirements for this step",
        default_factory=list
    )
    timeline_constraints: Optional[str] = Field(
        description="Timeline requirements from regulations",
        default=None
    )
    documentation_needed: List[str] = Field(
        description="Required documentation",
        default_factory=list
    )
    verification_points: List[str] = Field(
        description="Points requiring verification",
        default_factory=list
    )

class RegulatoryEvaluation(BaseModel):
    """Output schema for the regulatory evaluation of a service access strategy."""
    strategy_id: str = Field(description="ID of the evaluated strategy")
    evaluation_timestamp: datetime = Field(description="When evaluation was performed")
    
    # Overall Assessment
    is_compliant: bool = Field(description="Whether strategy is fully compliant")
    compliance_score: float = Field(
        description="Overall compliance score (0-1)",
        ge=0,
        le=1
    )
    
    # Document Sources
    relevant_documents: List[RegulatoryDocument] = Field(
        description="Relevant regulatory documents consulted",
        default_factory=list
    )
    
    # Detailed Analysis
    compliant_elements: List[str] = Field(
        description="Strategy elements that are compliant",
        default_factory=list
    )
    compliance_issues: List[ComplianceIssue] = Field(
        description="Identified compliance issues",
        default_factory=list
    )
    
    # Recommendations
    suggested_modifications: List[str] = Field(
        description="Suggested modifications to achieve compliance",
        default_factory=list
    )
    alternative_approaches: List[AlternativeApproach] = Field(
        description="Alternative compliant approaches",
        default_factory=list
    )
    
    # Implementation Guidance
    implementation_plan: List[ImplementationStep] = Field(
        description="Regulatory-aligned implementation steps",
        default_factory=list
    )
    
    # Risk Assessment
    risk_factors: Dict[str, Any] = Field(
        description="Identified risk factors",
        default_factory=dict
    )
    
    # Confidence Assessment
    evaluation_confidence: float = Field(
        description="Confidence in evaluation (0-1)",
        ge=0,
        le=1
    )
    uncertainty_notes: List[str] = Field(
        description="Areas of uncertainty in evaluation",
        default_factory=list
    ) 