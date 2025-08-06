"""
Workflow Prescription Agent

This agent classifies user requests into appropriate workflows:
- information_retrieval
- service_access_strategy  
- determine_eligibility
- form_preparation
"""

from .workflow_prescription_agent import WorkflowPrescriptionAgent

__all__ = ['WorkflowPrescriptionAgent'] 