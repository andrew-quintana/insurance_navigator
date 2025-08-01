from pydantic import BaseModel
from typing import List, Dict, Any
from ..types import Strategy, ValidationReason, SourceReference

class RegulatoryAgentInput(BaseModel):
    strategy: Strategy
    regulatory_context: str

class RegulatoryAgentOutput(BaseModel):
    compliance_status: str  # 'approved', 'flagged', 'rejected'
    validation_reasons: List[ValidationReason]
    confidence_score: float
    source_references: List[SourceReference] 