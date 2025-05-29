"""
Models for the Patient Navigator Agent.

This module defines the Pydantic models used by the Patient Navigator Agent for
request and response structures, ensuring type safety and validation.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MetaIntent(BaseModel):
    """Model representing the meta intent of a user query."""
    request_type: str = Field(
        description="Type of request (expert_request, service_request, symptom_report, policy_question)"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Summary of the user's request"
    )
    emergency: bool = Field(
        default=False,
        description="Whether the request appears to be an emergency"
    )
    location: Optional[str] = Field(
        default=None,
        description="Geographic location mentioned by user (city, state, area)"
    )
    insurance: Optional[str] = Field(
        default=None,
        description="Insurance provider or plan type mentioned by user"
    )


class BodyLocation(BaseModel):
    """Model representing a location on the body."""
    region: Optional[str] = Field(
        default=None,
        description="Body region (e.g., head, chest, abdomen)"
    )
    side: Optional[str] = Field(
        default=None,
        description="Body side (e.g., left, right, bilateral)"
    )
    subpart: Optional[str] = Field(
        default=None,
        description="Specific subpart of the region (e.g., lower, upper)"
    )


class ClinicalContext(BaseModel):
    """Model representing clinical context of a user query."""
    symptom: Optional[str] = Field(
        default=None,
        description="Primary symptom reported"
    )
    body: BodyLocation = Field(
        default_factory=BodyLocation,
        description="Body location information"
    )
    onset: Optional[str] = Field(
        default=None,
        description="When the symptom started"
    )
    duration: Optional[str] = Field(
        default=None,
        description="How long the symptom has lasted"
    )


class ServiceIntent(BaseModel):
    """Model representing service intent of a user query."""
    specialty: Optional[str] = Field(
        default=None,
        description="Medical specialty relevant to the request"
    )
    service: Optional[str] = Field(
        default=None,
        description="Specific service being requested"
    )
    plan_detail_type: Optional[str] = Field(
        default=None,
        description="Type of plan detail being requested"
    )


class Metadata(BaseModel):
    """Model representing metadata for a navigation request."""
    raw_user_text: str = Field(
        description="The original text entered by the user"
    )
    user_response_created: str = Field(
        description="Response to be shown to the user"
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Timestamp of the request in ISO 8601 format"
    )


class NavigatorOutput(BaseModel):
    """Model representing the complete output of the Patient Navigator Agent."""
    meta_intent: MetaIntent = Field(
        description="The meta intent of the user query"
    )
    clinical_context: ClinicalContext = Field(
        description="Clinical context extracted from the query"
    )
    service_intent: ServiceIntent = Field(
        description="Service intent extracted from the query"
    )
    metadata: Metadata = Field(
        description="Request metadata"
    ) 