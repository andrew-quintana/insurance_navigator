"""
Information Retrieval Agent for Patient Navigator

This agent translates user queries into insurance terminology, integrates with the RAG system,
and provides consistent responses using self-consistency methodology.

The agent follows a ReAct pattern with structured step-by-step processing:
1. Parse Structured Input from supervisor workflow
2. Query Reframing using insurance terminology
3. RAG Integration with existing system
4. Self-Consistency Loop (3-5 iterations)
5. Structured Output generation
"""

from .agent import InformationRetrievalAgent
from .models import InformationRetrievalInput, InformationRetrievalOutput

__all__ = [
    "InformationRetrievalAgent",
    "InformationRetrievalInput", 
    "InformationRetrievalOutput"
] 