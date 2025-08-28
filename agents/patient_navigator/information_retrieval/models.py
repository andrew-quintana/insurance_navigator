"""
Pydantic models for Information Retrieval Agent I/O.

These models define the structured input and output formats for the agent,
ensuring type safety and validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class InformationRetrievalInput(BaseModel):
    """
    Input model for information retrieval requests.
    
    This represents the structured input from the supervisor workflow,
    containing the user query and context information.
    """
    
    user_query: str = Field(
        description="The user's natural language query about insurance information",
        examples=[
            "What does my insurance cover for doctor visits?",
            "How much do I pay for prescription drugs?",
            "Is physical therapy covered under my plan?"
        ]
    )
    
    user_id: str = Field(
        description="User identifier for access control and document retrieval"
    )
    
    workflow_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context from the supervisor workflow"
    )
    
    document_requirements: Optional[List[str]] = Field(
        default=None,
        description="List of required document types or specific documents"
    )


class SourceChunk(BaseModel):
    """
    Model for a source document chunk with attribution.
    """
    
    chunk_id: str = Field(description="Unique identifier for the chunk")
    doc_id: str = Field(description="Document identifier")
    content: str = Field(description="Text content of the chunk")
    section_title: Optional[str] = Field(default=None, description="Section title if available")
    page_start: Optional[int] = Field(default=None, description="Start page number")
    page_end: Optional[int] = Field(default=None, description="End page number")
    similarity: Optional[float] = Field(default=None, description="Similarity score with query")
    tokens: Optional[int] = Field(default=None, description="Token count of the chunk")


class InformationRetrievalOutput(BaseModel):
    """
    Output model for information retrieval responses.
    
    This provides structured output with expert reframing, direct answers,
    key points, confidence scoring, and source attribution.
    """
    
    expert_reframe: str = Field(
        description="Expert-level query reframing in insurance terminology",
        examples=[
            "coverage analysis for outpatient physician services",
            "prescription drug benefit structure and cost-sharing",
            "physical therapy coverage under current benefit plan"
        ]
    )
    
    direct_answer: str = Field(
        description="Concise, focused response to the user's query",
        examples=[
            "Your plan covers doctor visits with a $25 copay for primary care and $40 for specialists.",
            "Prescription drugs are covered with tiered copays: $10 for generics, $30 for preferred brands.",
            "Physical therapy is covered for up to 20 visits per year with a $30 copay per session."
        ]
    )
    
    key_points: List[str] = Field(
        description="Ranked list of relevant information points",
        min_items=1,
        max_items=10,
        examples=[
            ["Copay amounts vary by provider type", "Prior authorization required for specialists"],
            ["Tiered copay structure applies", "Mail-order pharmacy available for maintenance drugs"],
            ["Visit limits apply per calendar year", "Referral required from primary care physician"]
        ]
    )
    
    confidence_score: float = Field(
        description="Confidence score based on self-consistency methodology (0.0-1.0)",
        ge=0.0,
        le=1.0,
        examples=[0.85, 0.92, 0.78]
    )
    
    source_chunks: List[SourceChunk] = Field(
        description="Source document chunks used to generate the response",
        default_factory=list
    )
    
    processing_steps: Optional[List[str]] = Field(
        default_factory=list,
        description="List of processing steps completed for transparency"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    ) 