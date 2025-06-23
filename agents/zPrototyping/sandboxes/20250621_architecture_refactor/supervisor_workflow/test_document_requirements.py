#!/usr/bin/env python3
"""
Test script for Document Requirements Agent
"""

import sys
import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

# Add necessary paths
sys.path.append('../../')
from langgraph_utils import create_agent

# Define schema
class DocumentRequirementsOutput(BaseModel):
    """Schema for document requirements agent output"""
    required_documents: List[str] = Field(description="List of required documents")
    optional_documents: List[str] = Field(description="List of optional/helpful documents")
    missing_information: List[str] = Field(description="List of missing information that requires user input")
    document_categories: dict = Field(description="Document categorization (required/optional/reference)")
    reasoning: str = Field(description="Explanation of document requirements")
    readiness_assessment: str = Field(description="Overall readiness: ready, needs_user_input, needs_extensive_user_input")
    confidence: float = Field(description="Confidence score", ge=0.0, le=1.0)

def test_document_requirements_agent():
    """Test the document requirements agent with mock LLM"""
    
    print("🧪 Testing Document Requirements Agent")
    print("=" * 50)
    
    try:
        # Create agent with mock LLM (None = mock mode)
        doc_agent = create_agent(
            name="DocumentRequirementsTest",
            prompt_path="document_requirements/document_requirements_system.md",
            examples_path="document_requirements/document_requirements_examples.json",
            output_schema=DocumentRequirementsOutput,
            llm=None,  # Mock mode
            use_langchain_pattern=True,
            use_human_message=True,
            use_system_message=True,
            merge_examples=True
        )
        
        print(f"✅ Agent created: {doc_agent.__name__}")
        
        # Test input (simulating output from workflow prescription agent)
        test_input = """
        Prescribed Workflows: ['information_retrieval']
        User's Original Request: What is the copay for a doctor's visit?
        Additional Context: Priority level low, Confidence 0.9
        """
        
        print(f"\n📝 Test Input: {test_input.strip()}")
        
        # Call agent
        result = doc_agent(test_input)
        
        print(f"\n📋 Results:")
        print(f"   Required Documents: {result.required_documents}")
        print(f"   Optional Documents: {result.optional_documents}")
        print(f"   Missing Information: {result.missing_information}")
        print(f"   Readiness Assessment: {result.readiness_assessment}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Reasoning: {result.reasoning[:100]}...")
        
        print(f"\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_document_requirements_agent()
    exit(0 if success else 1) 