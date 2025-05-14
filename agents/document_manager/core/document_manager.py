"""
Document Manager Agent

This agent is responsible for:
1. Managing document lifecycle
2. Processing document content
3. Handling document metadata
4. Coordinating document-related workflows
5. Ensuring document security and compliance

Based on FMEA analysis, this agent implements controls for:
- Document validation and verification
- Content extraction and processing
- Metadata management
- Document security and access control
- Integration with other agents for specialized document handling
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Tuple, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import PydanticOutputParser

from agents.base_agent import BaseAgent
from utils.prompt_loader import load_prompt

# Setup logging
logger = logging.getLogger("document_manager_agent")
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join("agents", "document_manager", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler
    handler = logging.FileHandler(os.path.join(log_dir, "document_manager.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Define output schemas
class DocumentMetadata(BaseModel):
    """Schema for document metadata."""
    document_id: str = Field(description="Unique identifier for the document")
    title: str = Field(description="Document title")
    document_type: str = Field(description="Type of document")
    creation_date: str = Field(description="Date the document was created")
    last_modified: str = Field(description="Date the document was last modified")
    author: Optional[str] = Field(description="Document author", default=None)
    version: Optional[str] = Field(description="Document version", default="1.0")
    tags: List[str] = Field(description="Tags associated with the document", default_factory=list)
    status: str = Field(description="Document status (draft, review, approved, etc.)")

class DocumentContent(BaseModel):
    """Schema for document content."""
    text: str = Field(description="Extracted text content")
    sections: List[Dict[str, Any]] = Field(description="Document sections", default_factory=list)
    tables: List[Dict[str, Any]] = Field(description="Tables extracted from the document", default_factory=list)
    images: List[Dict[str, Any]] = Field(description="Images referenced in the document", default_factory=list)
    forms: List[Dict[str, Any]] = Field(description="Forms contained in the document", default_factory=list)

class DocumentAnalysis(BaseModel):
    """Schema for document analysis results."""
    summary: str = Field(description="Document summary")
    key_points: List[str] = Field(description="Key points extracted from the document", default_factory=list)
    entities: List[Dict[str, Any]] = Field(description="Named entities found in the document", default_factory=list)
    sentiment: Optional[Dict[str, Any]] = Field(description="Sentiment analysis results", default=None)
    topics: List[str] = Field(description="Topics identified in the document", default_factory=list)
    compliance_status: Dict[str, Any] = Field(description="Compliance status of the document", default_factory=dict)

class DocumentProcessingResult(BaseModel):
    """Output schema for document processing."""
    metadata: DocumentMetadata
    content: DocumentContent
    analysis: DocumentAnalysis
    processing_status: str = Field(description="Status of document processing")
    processing_time: float = Field(description="Time taken to process the document in seconds")
    errors: List[Dict[str, Any]] = Field(description="Errors encountered during processing", default_factory=list)
    warnings: List[Dict[str, Any]] = Field(description="Warnings generated during processing", default_factory=list)
    timestamp: str = Field(description="Timestamp of processing")

class DocumentManagerAgent(BaseAgent):
    """Agent responsible for managing and processing healthcare documents."""
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize the agent with an optional language model."""
        # Initialize the base agent
        super().__init__(
            name="document_manager", 
            llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0.3),
            prompt_version="V0.1",
            prompt_description="Document management, processing, and lifecycle agent"
        )
        
        self.processing_parser = PydanticOutputParser(pydantic_object=DocumentProcessingResult)
        
        # Load the system prompt
        try:
            self.system_prompt = load_prompt("document_manager")
        except FileNotFoundError:
            self.logger.warning("Could not find document_manager.md prompt file, using default prompt")
            self.system_prompt = """
            You are an expert Document Manager with deep knowledge in document processing, content extraction, 
            and metadata management. Your task is to analyze documents, extract relevant information, and 
            provide structured outputs that can be used by other agents in the system.
            """
        
        # Define the prompt template
        self.prompt_template = PromptTemplate(
            template="""
            {system_prompt}
            
            DOCUMENT INFORMATION:
            {document_info}
            
            PROCESSING PARAMETERS:
            {processing_params}
            
            Process this document according to the specified parameters and provide a structured output.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "document_info", "processing_params"],
            partial_variables={"format_instructions": self.processing_parser.get_format_instructions()}
        )
        
        # Create the chain
        self.chain = (
            {"system_prompt": lambda _: self.system_prompt,
             "document_info": lambda x: json.dumps(x["document_info"], indent=2),
             "processing_params": lambda x: json.dumps(x.get("processing_params", {}), indent=2)}
            | self.prompt_template
            | self.llm
            | self.processing_parser
        )
        
        logger.info("Document Manager Agent initialized")
    
    @BaseAgent.track_performance
    def process(self, document_info: Dict[str, Any], processing_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a document and return structured results.
        
        Args:
            document_info: Information about the document to process
            processing_params: Parameters controlling the processing behavior
            
        Returns:
            Dict containing the processing results
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Processing document: {document_info.get('title', 'Untitled')}")
        
        try:
            # Prepare the input for the chain
            input_dict = {
                "document_info": document_info,
                "processing_params": processing_params or {}
            }
            
            # Process the document
            result = self.chain.invoke(input_dict)
            
            # Convert to dict for return
            result_dict = result.model_dump()
            
            # Log the result
            self.logger.info(f"Document processed successfully. Status: {result.processing_status}")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Document processing completed in {execution_time:.2f}s")
            
            return result_dict
            
        except Exception as e:
            self.logger.error(f"Error in document processing: {str(e)}")
            
            # Return a basic response in case of error
            error_response = {
                "metadata": {
                    "document_id": document_info.get("document_id", "unknown"),
                    "title": document_info.get("title", "Untitled"),
                    "document_type": document_info.get("document_type", "unknown"),
                    "creation_date": document_info.get("creation_date", ""),
                    "last_modified": document_info.get("last_modified", ""),
                    "status": "error"
                },
                "content": {
                    "text": "",
                    "sections": [],
                    "tables": [],
                    "images": [],
                    "forms": []
                },
                "analysis": {
                    "summary": "Document processing failed",
                    "key_points": [],
                    "entities": [],
                    "topics": [],
                    "compliance_status": {"status": "unknown"}
                },
                "processing_status": "failed",
                "processing_time": time.time() - start_time,
                "errors": [{"type": "processing_error", "message": str(e)}],
                "warnings": [],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
            return error_response 