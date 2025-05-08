"""
Document Parser Agent

This agent is responsible for:
1. Parsing uploaded insurance policy documents
2. Extracting key information from PDFs, images, and text files
3. Structuring extracted information for downstream agents
4. Handling OCR failures and poor image quality
5. Providing confidence scores for extracted information

Based on FMEA analysis, this agent implements controls for:
- OCR failures due to poor image quality
- Missing key information in complex documents
- Handling multiple document formats
- Document preprocessing for better extraction
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Tuple, Optional, Union, BinaryIO
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from agents.base_agent import BaseAgent
from utils.prompt_loader import load_prompt

# Setup logging
logger = logging.getLogger("document_parser_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "document_parser.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Define output schema for the agent
class ExtractedDocumentInfo(BaseModel):
    """Output schema for the document parser agent."""
    document_type: str = Field(description="Type of document (e.g., policy, claim, EOB)")
    insurer_name: Optional[str] = Field(description="Name of the insurance company")
    policy_number: Optional[str] = Field(description="Policy identifier")
    policy_holder: Optional[str] = Field(description="Name of the policy holder")
    effective_date: Optional[str] = Field(description="Policy effective date")
    expiration_date: Optional[str] = Field(description="Policy expiration date")
    coverage_types: List[str] = Field(description="Types of coverage included", default_factory=list)
    coverage_limits: Dict[str, Any] = Field(description="Coverage limits by type", default_factory=dict)
    key_exclusions: List[str] = Field(description="Key coverage exclusions", default_factory=list)
    deductibles: Dict[str, Any] = Field(description="Deductible amounts by type", default_factory=dict)
    copays: Dict[str, Any] = Field(description="Copay amounts by service type", default_factory=dict)
    extracted_text: str = Field(description="Full extracted text from the document")
    extraction_quality: float = Field(description="Quality score for the extraction (0-1)")
    missing_fields: List[str] = Field(description="Fields that could not be extracted", default_factory=list)
    confidence: Dict[str, float] = Field(description="Confidence scores by field", default_factory=dict)

class DocumentParserAgent(BaseAgent):
    """Agent responsible for parsing insurance documents and extracting structured information."""
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize the agent with an optional language model."""
        # Initialize the base agent
        super().__init__(name="document_parser", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0))
        
        self.parser = PydanticOutputParser(pydantic_object=ExtractedDocumentInfo)
        
        # Define system prompt for document parsing
        # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("document_parser")
        except FileNotFoundError:
            self.logger.warning("Could not find document_parser.md prompt file, using default prompt")
            # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("document_parser")
        except FileNotFoundError:
            self.logger.warning("Could not find document_parser.md prompt file, using default prompt")
            self.system_prompt = """
            Default prompt for self.system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the prompt template
        self.prompt_template = PromptTemplate(
            template="""
            {system_prompt}
            
            DOCUMENT TEXT:
            {document_text}
            
            Extract the key insurance policy information from this document.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "document_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        # Create the chain
        self.chain = (
            {"system_prompt": lambda _: self.system_prompt, "document_text": RunnablePassthrough()}
            | self.prompt_template
            | self.llm
            | self.parser
        )
        
        logger.info("Document Parser Agent initialized")
    
    def preprocess_text(self, document_text: str) -> str:
        """
        Preprocess document text to improve parsing.
        
        Args:
            document_text: Raw document text
            
        Returns:
            Preprocessed document text
        """
        # Basic preprocessing: remove extra whitespace, normalize line breaks
        preprocessed_text = " ".join(document_text.split())
        
        # TODO: Add more sophisticated preprocessing if needed
        
        return preprocessed_text
    
    @BaseAgent.track_performance
    def parse_document(self, document_text: str) -> Dict[str, Any]:
        """
        Parse document text and extract structured information.
        
        Args:
            document_text: The document text to parse
            
        Returns:
            Dictionary with extracted information
        """
        start_time = time.time()
        
        # Log the incoming request
        self.logger.info(f"Parsing document of length: {len(document_text)} characters")
        
        # Preprocess the document text
        preprocessed_text = self.preprocess_text(document_text)
        
        try:
            # Run the document parsing chain
            extracted_info = self.chain.invoke(preprocessed_text)
            result = extracted_info.dict()
            
            # Log the result
            self.logger.info(f"Document parsed as type: {result['document_type']} with quality: {result['extraction_quality']}")
            if result['missing_fields']:
                self.logger.warning(f"Missing fields: {', '.join(result['missing_fields'])}")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Document parsing completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in document parsing: {str(e)}")
            
            # Return a basic result in case of error
            return {
                "document_type": "unknown",
                "insurer_name": None,
                "policy_number": None,
                "policy_holder": None,
                "effective_date": None,
                "expiration_date": None,
                "coverage_types": [],
                "coverage_limits": {},
                "key_exclusions": [],
                "deductibles": {},
                "copays": {},
                "extracted_text": document_text[:1000] + "...(truncated)",
                "extraction_quality": 0.0,
                "missing_fields": ["all_fields_due_to_error"],
                "confidence": {"overall": 0.0},
                "error": str(e)
            }
    
    def process(self, document_text: str) -> Tuple[ExtractedDocumentInfo, Dict[str, Any]]:
        """
        Process a document and return the extracted information.
        
        Args:
            document_text: The document text to process
            
        Returns:
            Tuple of (extracted_info_model, full_result_dict)
        """
        result = self.parse_document(document_text)
        extracted_info = ExtractedDocumentInfo(**result)
        return extracted_info, result

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = DocumentParserAgent()
    
    # Test with a sample document
    sample_doc = """
    ABC INSURANCE COMPANY
    POLICY DOCUMENT
    
    Policy Number: POL123456789
    Policy Holder: John Doe
    Effective Date: 01/01/2025
    Expiration Date: 12/31/2025
    
    COVERAGE SUMMARY:
    - Primary Care: $20 copay per visit
    - Specialist Care: $40 copay per visit
    - Emergency Room: $250 copay (waived if admitted)
    - Hospital Stay: 20% coinsurance after deductible
    
    Annual Deductible: $1,500 individual / $3,000 family
    Out-of-Pocket Maximum: $5,000 individual / $10,000 family
    
    EXCLUSIONS:
    - Cosmetic procedures
    - Experimental treatments
    - Non-emergency care outside network
    """
    
    extracted_info, result = agent.process(sample_doc)
    
    print(f"Document Type: {extracted_info.document_type}")
    print(f"Policy Number: {extracted_info.policy_number}")
    print(f"Policy Holder: {extracted_info.policy_holder}")
    print(f"Coverage Types: {', '.join(extracted_info.coverage_types)}")
    print(f"Extraction Quality: {extracted_info.extraction_quality}")
    print(f"Missing Fields: {', '.join(extracted_info.missing_fields)}") 