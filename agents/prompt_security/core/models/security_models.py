"""
Models for the Prompt Security Agent.

This module defines the Pydantic models used by the Prompt Security Agent for
security validation and response.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator, constr, ConfigDict

class SecurityCheck(BaseModel):
    """Output schema for the prompt security agent."""
    is_safe: bool = Field(description="Whether the input is safe to process")
    threat_detected: bool = Field(description="Whether a security threat was detected")
    threat_type: Literal[
        "jailbreak", "override", "leakage",
        "hijack", "obfuscation", "payload_splitting",
        "unknown", "none"
    ] = Field(
        description="The specific type of threat detected",
        default="none"
    )
    threat_severity: Literal[
        "none_detected", "borderline", "explicit"
    ] = Field(
        description="The risk of the impact if the threat is not mitigated",
        default="none_detected"
    )
    sanitized_input: str = Field(description="Cleaned or redacted prompt string")
    confidence: float = Field(
        description="Model's confidence in this assessment",
        ge=0.0,
        le=1.0
    )
    reasoning: constr(min_length=10, max_length=500) = Field(
        description="One- to three-sentence justification, structured as: 'This input [appears to / attempts to] ... [with / without] clear intent to [bypass / harm / violate / provoke].'"
    )
    
    @field_validator('threat_type')
    def validate_threat_type(cls, v, info):
        values = info.data
        if values.get('threat_detected') and v == "none":
            raise ValueError("threat_type cannot be 'none' when threat_detected is True")
        if not values.get('threat_detected') and v != "none":
            raise ValueError("threat_type must be 'none' when threat_detected is False")
        return v
    
    @field_validator('threat_severity')
    def validate_severity(cls, v, info):
        values = info.data
        if not values.get('threat_detected') and v != "none_detected":
            raise ValueError("threat_severity must be 'none_detected' when threat_detected is False")
        if values.get('threat_detected') and v == "none_detected":
            raise ValueError("threat_severity must not be 'none_detected' when threat_detected is True")
        return v
    
    @field_validator('reasoning')
    def validate_reasoning_format(cls, v, info):
        if not (v.startswith("This input appears to") or 
                v.startswith("This input attempts to")):
            raise ValueError("reasoning must start with 'This input [appears to / attempts to]'")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_safe": False,
                "threat_detected": True,
                "threat_type": "injection",
                "threat_severity": "explicit",
                "sanitized_input": "[BLOCKED DUE TO SECURITY CONCERNS]",
                "confidence": 0.92,
                "reasoning": "This input attempts to bypass system instructions with clear intent to provoke unauthorized behavior."
            }
        }
    ) 