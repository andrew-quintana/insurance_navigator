from typing import Dict, Any
from pydantic import BaseModel, Field


class MemorySummary(BaseModel):
    """Pydantic schema for short-term memory summaries.

    The schema must match the RFC structure exactly.
    """

    user_confirmed: Dict[str, Any] = Field(default_factory=dict, description="Facts explicitly confirmed by the user")
    llm_inferred: Dict[str, Any] = Field(default_factory=dict, description="Model-derived assumptions not directly confirmed")
    general_summary: str = Field(default="", description="Coherent summary of chat goals and progress")


class SummarizerInput(BaseModel):
    """Input for the summarizer agent.

    prior_memory: current memory record from `chat_metadata` (may be defaults)
    new_context_snippet: fresh context to incorporate
    """

    prior_memory: Dict[str, Any]
    new_context_snippet: str

