"""
Models for the Service Access Strategy Agent.

This module defines the Pydantic models used by the Service Access Strategy Agent 
for service matching, action steps, and strategy development.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ServiceMatch(BaseModel):
    """Schema for a matched healthcare service."""
    service_name: str = Field(
        description="Name of the healthcare service"
    )
    service_type: str = Field(
        description="Type/category of service"
    )
    service_description: str = Field(
        description="Description of the service"
    )
    is_covered: bool = Field(
        description="Whether the service is covered by insurance"
    )
    coverage_details: Dict[str, Any] = Field(
        description="Details about coverage", 
        default_factory=dict
    )
    estimated_cost: Optional[str] = Field(
        description="Estimated cost of the service", 
        default=None
    )
    required_documentation: List[str] = Field(
        description="Documents required for the service", 
        default_factory=list
    )
    prerequisites: List[str] = Field(
        description="Prerequisites for accessing the service", 
        default_factory=list
    )
    alternatives: List[str] = Field(
        description="Alternative services", 
        default_factory=list
    )
    compliance_score: float = Field(
        description="Compliance score from 0-1"
    )


class ActionStep(BaseModel):
    """Schema for an action step in the service access plan."""
    step_number: int = Field(
        description="Number of the step in sequence"
    )
    step_description: str = Field(
        description="Description of the action step"
    )
    expected_timeline: str = Field(
        description="Expected timeline for completing the step"
    )
    required_resources: List[str] = Field(
        description="Resources required for the step", 
        default_factory=list
    )
    potential_obstacles: List[str] = Field(
        description="Potential obstacles for this step", 
        default_factory=list
    )
    contingency_plan: Optional[str] = Field(
        description="Contingency plan if step encounters issues", 
        default=None
    )


class ServiceAccessStrategy(BaseModel):
    """Output schema for the service access strategy."""
    patient_need: str = Field(
        description="Description of the patient's medical need"
    )
    matched_services: List[ServiceMatch] = Field(
        description="List of matched services", 
        default_factory=list
    )
    recommended_service: str = Field(
        description="The recommended service option"
    )
    action_plan: List[ActionStep] = Field(
        description="Step-by-step action plan", 
        default_factory=list
    )
    estimated_timeline: str = Field(
        description="Estimated overall timeline"
    )
    provider_options: List[Dict[str, Any]] = Field(
        description="Provider options", 
        default_factory=list
    )
    compliance_assessment: Dict[str, Any] = Field(
        description="Policy compliance assessment", 
        default_factory=dict
    )
    guidance_notes: List[str] = Field(
        description="Additional guidance notes", 
        default_factory=list
    )
    confidence: float = Field(
        description="Overall confidence in the strategy (0-1)"
    ) 