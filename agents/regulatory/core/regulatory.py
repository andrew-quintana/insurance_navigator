"""
Regulatory Agent

This agent is responsible for:
1. Detecting and redacting sensitive information (PHI/PII)
2. Ensuring compliance with HIPAA regulations
3. Verifying adherence to CMS guidelines
4. Adding appropriate disclaimers and advisory language
5. Tracking provenance of recommendations for auditability

Based on FMEA analysis, this agent implements controls for:
- PHI/PII entity classification and redaction
- Context-aware masking with semantic role labeling
- Policy update triggers with CMS diff checking
- Nested content security scanning
- Conditional advisory and disclaimer injection
"""

import os
import json
import time
import logging
import re
from typing import Dict, List, Any, Tuple, Optional, Union, Set
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
logger = logging.getLogger("regulatory_agent")
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join("agents", "regulatory", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up file handler
    handler = logging.FileHandler(os.path.join(log_dir, "regulatory.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Define output schemas
class SensitiveEntity(BaseModel):
    """Schema for a sensitive entity detected in content."""
    entity_type: str = Field(description="Type of sensitive entity (PII, PHI)")
    entity_subtype: str = Field(description="Subtype of entity (name, DOB, address, etc.)")
    content: str = Field(description="Content of the sensitive entity")
    location: str = Field(description="Location in the content (section, field)")
    confidence: float = Field(description="Confidence in the detection (0-1)")
    redaction_recommended: bool = Field(description="Whether redaction is recommended")
    context: Optional[str] = Field(description="Surrounding context", default=None)

class ComplianceIssue(BaseModel):
    """Schema for a compliance issue identified in content."""
    issue_type: str = Field(description="Type of compliance issue (HIPAA, CMS, advisory)")
    severity: int = Field(description="Severity of the issue (1-10)")
    description: str = Field(description="Description of the compliance issue")
    recommendation: str = Field(description="Recommended fix for the issue")
    reference: Optional[str] = Field(description="Reference to relevant regulation or guideline", default=None)
    location: str = Field(description="Location in the content")
    requires_immediate_action: bool = Field(description="Whether immediate action is required", default=False)

class RedactionResult(BaseModel):
    """Schema for redaction results."""
    original_content_hash: str = Field(description="Hash of the original content")
    redacted_content: str = Field(description="Redacted content")
    entities_redacted: List[SensitiveEntity] = Field(description="Entities that were redacted", default_factory=list)
    redaction_count: int = Field(description="Number of redactions performed")
    confidence: float = Field(description="Overall confidence in redaction (0-1)")

class RegulatoryAssessment(BaseModel):
    """Output schema for regulatory assessment."""
    content_id: str = Field(description="Identifier for the assessed content")
    content_type: str = Field(description="Type of content assessed")
    hipaa_compliant: bool = Field(description="Whether the content is HIPAA compliant")
    cms_compliant: bool = Field(description="Whether the content is CMS compliant")
    contains_phi: bool = Field(description="Whether the content contains PHI")
    contains_pii: bool = Field(description="Whether the content contains PII")
    sensitive_entities: List[SensitiveEntity] = Field(description="Sensitive entities detected", default_factory=list)
    compliance_issues: List[ComplianceIssue] = Field(description="Compliance issues identified", default_factory=list)
    advisories_needed: List[str] = Field(description="Advisories needed for the content", default_factory=list)
    disclaimers_needed: List[str] = Field(description="Disclaimers needed for the content", default_factory=list)
    confidence: float = Field(description="Overall confidence in assessment (0-1)")
    overall_risk_level: str = Field(description="Overall risk level (low, medium, high, critical)")
    assessment_timestamp: str = Field(description="Timestamp of the assessment")
    references: List[str] = Field(description="References to relevant regulations", default_factory=list)
    recommendations: List[str] = Field(description="Recommendations for regulatory compliance", default_factory=list)

class RegulatoryAgent(BaseAgent):
    """Agent responsible for ensuring regulatory compliance and data privacy."""
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize the agent with an optional language model."""
        # Initialize the base agent
        super().__init__(name="regulatory", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0))
        
        self.assessment_parser = PydanticOutputParser(pydantic_object=RegulatoryAssessment)
        self.redaction_parser = PydanticOutputParser(pydantic_object=RedactionResult)
        
        # Initialize sensitive information patterns
        self._init_sensitive_patterns()
        
        # Initialize standard disclaimers
        self._init_standard_disclaimers()
        
        # Define system prompt for regulatory assessment
        # Load the self.assessment_system_prompt from file
        try:
            self.assessment_system_prompt = load_prompt("regulatory_assessment")
        except FileNotFoundError:
            self.logger.warning("Could not find regulatory_assessment.md prompt file, using default prompt")
            # Load the self.assessment_system_prompt from file
        try:
            self.assessment_system_prompt = load_prompt("regulatory_assessment_prompt")
        except FileNotFoundError:
            self.logger.warning("Could not find regulatory_assessment_prompt.md prompt file, using default prompt")
            self.assessment_system_prompt = """
            Default prompt for self.assessment_system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define system prompt for content redaction
        # Load the self.redaction_system_prompt from file
        try:
            self.redaction_system_prompt = load_prompt("regulatory_redaction")
        except FileNotFoundError:
            self.logger.warning("Could not find regulatory_redaction.md prompt file, using default prompt")
            # Load the self.redaction_system_prompt from file
        try:
            self.redaction_system_prompt = load_prompt("regulatory_redaction_prompt")
        except FileNotFoundError:
            self.logger.warning("Could not find regulatory_redaction_prompt.md prompt file, using default prompt")
            self.redaction_system_prompt = """
            Default prompt for self.redaction_system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the assessment prompt template
        self.assessment_template = PromptTemplate(
            template="""
            {system_prompt}
            
            CONTENT TYPE: {content_type}
            
            CONTENT TO ASSESS:
            {content}
            
            ADDITIONAL CONTEXT:
            {context}
            
            Conduct a thorough regulatory assessment of this content, identifying any PHI/PII, 
            compliance issues, and necessary advisories or disclaimers.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "content_type", "content", "context"],
            partial_variables={"format_instructions": self.assessment_parser.get_format_instructions()}
        )
        
        # Define the redaction prompt template
        self.redaction_template = PromptTemplate(
            template="""
            {system_prompt}
            
            CONTENT TO REDACT:
            {content}
            
            SENSITIVE ENTITIES TO REDACT:
            {sensitive_entities}
            
            Redact all PHI and PII from this content while preserving its essential meaning and usefulness.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "content", "sensitive_entities"],
            partial_variables={"format_instructions": self.redaction_parser.get_format_instructions()}
        )
        
        # Create the assessment chain
        self.assessment_chain = (
            {"system_prompt": lambda _: self.assessment_system_prompt,
             "content_type": lambda x: x["content_type"],
             "content": lambda x: json.dumps(x["content"], indent=2) if isinstance(x["content"], dict) else x["content"],
             "context": lambda x: json.dumps(x.get("context", {}), indent=2)}
            | self.assessment_template
            | self.llm
            | self.assessment_parser
        )
        
        # Create the redaction chain
        self.redaction_chain = (
            {"system_prompt": lambda _: self.redaction_system_prompt,
             "content": lambda x: json.dumps(x["content"], indent=2) if isinstance(x["content"], dict) else x["content"],
             "sensitive_entities": lambda x: json.dumps(x["sensitive_entities"], indent=2)}
            | self.redaction_template
            | self.llm
            | self.redaction_parser
        )
        
        logger.info("Regulatory Agent initialized")
    
    def _init_sensitive_patterns(self):
        """Initialize patterns for detecting sensitive information."""
        self.phi_patterns = {
            "name": r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "medicare_id": r"\b[1-9][0-9]{2}-[0-9]{2}-[0-9]{4}[A-Z]\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "dob": r"\b(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/(19|20)\d{2}\b",
            "address": r"\b\d+\s+[A-Za-z\s]+,\s+[A-Za-z\s]+,\s+[A-Z]{2}\s+\d{5}(-\d{4})?\b"
        }
        
        # Compile regex patterns
        self.compiled_patterns = {
            pattern_name: re.compile(pattern, re.IGNORECASE)
            for pattern_name, pattern in self.phi_patterns.items()
        }
    
    def _init_standard_disclaimers(self):
        """Initialize standard disclaimers and advisories."""
        self.standard_disclaimers = {
            "general": """
            This information is for educational purposes only and does not constitute official Medicare advice. 
            Always consult with Medicare directly or a licensed insurance professional for decisions about 
            your specific situation.
            """,
            
            "provider": """
            Provider information is subject to change. Verify network status and other details directly 
            with the provider or Medicare before scheduling appointments or services.
            """,
            
            "coverage": """
            Coverage information is general and based on standard Medicare policies. Your specific coverage 
            may vary based on your plan, location, and individual circumstances. Contact Medicare or your 
            plan administrator for details about your specific coverage.
            """,
            
            "cost": """
            Cost estimates are approximate and subject to change. Your actual costs may vary based on 
            your specific plan, deductible status, provider billing practices, and other factors.
            """,
            
            "medical": """
            This content does not constitute medical advice. Always consult with a qualified healthcare 
            provider for medical decisions, diagnoses, and treatment options.
            """
        }
    
    def _quick_scan_for_phi(self, content: str) -> List[Dict[str, Any]]:
        """
        Perform a quick regex-based scan for potential PHI/PII.
        
        Args:
            content: Content to scan
            
        Returns:
            List of potential sensitive entities
        """
        potential_entities = []
        
        # Convert content to string if it's a dictionary
        if isinstance(content, dict):
            content = json.dumps(content)
        
        # Check each pattern
        for pattern_name, compiled_pattern in self.compiled_patterns.items():
            matches = compiled_pattern.finditer(content)
            for match in matches:
                # Get surrounding context (20 chars before and after)
                start_context = max(0, match.start() - 20)
                end_context = min(len(content), match.end() + 20)
                context = content[start_context:end_context]
                
                # Add potential entity
                potential_entities.append({
                    "entity_type": "PHI" if pattern_name in ["medicare_id", "dob"] else "PII",
                    "entity_subtype": pattern_name,
                    "content": match.group(),
                    "location": f"offset_{match.start()}-{match.end()}",
                    "confidence": 0.75,  # Default confidence for regex matches
                    "redaction_recommended": True,
                    "context": context
                })
        
        return potential_entities
    
    @BaseAgent.track_performance
    def assess_regulatory_compliance(self, content: Union[str, Dict[str, Any]], content_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assess the regulatory compliance of content.
        
        Args:
            content: Content to assess
            content_type: Type of content (guide, provider_list, etc.)
            context: Optional context information
            
        Returns:
            Regulatory assessment
        """
        start_time = time.time()
        
        # Generate a content ID if not provided in context
        content_id = context.get("content_id") if context else f"{content_type}_{int(time.time())}"
        
        # Log the request
        self.logger.info(f"Assessing regulatory compliance of {content_type} (ID: {content_id})...")
        
        try:
            # Prepare input for the assessment chain
            input_dict = {
                "content_type": content_type,
                "content": content,
                "context": context or {}
            }
            
            # Perform quick scan for potential PHI/PII
            content_str = json.dumps(content) if isinstance(content, dict) else content
            potential_entities = self._quick_scan_for_phi(content_str)
            
            if potential_entities:
                self.logger.info(f"Quick scan found {len(potential_entities)} potential sensitive entities")
                
                # Add potential entities to context
                if "context" not in input_dict:
                    input_dict["context"] = {}
                input_dict["context"]["potential_sensitive_entities"] = potential_entities
            
            # Perform regulatory assessment
            assessment = self.assessment_chain.invoke(input_dict)
            
            # Add content ID and timestamp if not provided
            if not assessment.content_id:
                assessment.content_id = content_id
            assessment.assessment_timestamp = assessment.assessment_timestamp or time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Convert to dictionary
            result = assessment.dict()
            
            # Log the result
            self.logger.info(f"Regulatory assessment for {content_type} (ID: {content_id})")
            self.logger.info(f"HIPAA compliant: {result['hipaa_compliant']}, CMS compliant: {result['cms_compliant']}")
            self.logger.info(f"Contains PHI: {result['contains_phi']}, Contains PII: {result['contains_pii']}")
            self.logger.info(f"Risk level: {result['overall_risk_level']}")
            
            if result['sensitive_entities']:
                self.logger.warning(f"Found {len(result['sensitive_entities'])} sensitive entities")
            
            if result['compliance_issues']:
                self.logger.warning(f"Found {len(result['compliance_issues'])} compliance issues")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Regulatory assessment completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in regulatory assessment: {str(e)}")
            
            # Create a conservative fallback assessment in case of error
            fallback = {
                "content_id": content_id,
                "content_type": content_type,
                "hipaa_compliant": False,  # Conservative assumption
                "cms_compliant": False,    # Conservative assumption
                "contains_phi": True,      # Conservative assumption
                "contains_pii": True,      # Conservative assumption
                "sensitive_entities": [],
                "compliance_issues": [{
                    "issue_type": "system_error",
                    "severity": 10,
                    "description": f"Regulatory assessment failed with error: {str(e)}",
                    "recommendation": "Perform manual regulatory review",
                    "location": "entire_content",
                    "requires_immediate_action": True
                }],
                "advisories_needed": list(self.standard_disclaimers.keys()),  # Include all disclaimers to be safe
                "disclaimers_needed": list(self.standard_disclaimers.keys()),  # Include all disclaimers to be safe
                "confidence": 0.0,
                "overall_risk_level": "critical",  # Conservative assumption
                "assessment_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "references": [],
                "recommendations": ["Perform manual regulatory review"],
                "error": str(e)
            }
            
            return fallback
    
    @BaseAgent.track_performance
    def redact_sensitive_information(self, content: Union[str, Dict[str, Any]], sensitive_entities: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Redact sensitive information from content.
        
        Args:
            content: Content to redact
            sensitive_entities: Optional list of sensitive entities to redact
            
        Returns:
            Redaction result
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info("Redacting sensitive information...")
        
        try:
            # If no sensitive entities provided, perform assessment to find them
            if not sensitive_entities:
                content_type = "unknown"
                if isinstance(content, dict):
                    content_type = content.get("type", "unknown")
                
                self.logger.info("No sensitive entities provided, performing assessment first")
                assessment = self.assess_regulatory_compliance(content, content_type)
                sensitive_entities = assessment.get("sensitive_entities", [])
            
            # If still no sensitive entities, return the original content with a note
            if not sensitive_entities:
                self.logger.info("No sensitive entities found, returning original content")
                
                # Calculate hash of original content
                import hashlib
                content_str = json.dumps(content) if isinstance(content, dict) else content
                original_hash = hashlib.sha256(content_str.encode()).hexdigest()
                
                return {
                    "original_content_hash": original_hash,
                    "redacted_content": content_str,
                    "entities_redacted": [],
                    "redaction_count": 0,
                    "confidence": 1.0
                }
            
            # Prepare input for the redaction chain
            input_dict = {
                "content": content,
                "sensitive_entities": sensitive_entities
            }
            
            # Perform redaction
            redaction_result = self.redaction_chain.invoke(input_dict)
            
            # Convert to dictionary
            result = redaction_result.dict()
            
            # Log the result
            self.logger.info(f"Redaction completed: {result['redaction_count']} entities redacted")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Redaction completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in redaction: {str(e)}")
            
            # Calculate hash of original content
            import hashlib
            content_str = json.dumps(content) if isinstance(content, dict) else content
            original_hash = hashlib.sha256(content_str.encode()).hexdigest()
            
            # Return a conservative result in case of error
            return {
                "original_content_hash": original_hash,
                "redacted_content": "[CONTENT REDACTED DUE TO PROCESSING ERROR]",
                "entities_redacted": [],
                "redaction_count": 1,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def get_standard_disclaimer(self, disclaimer_type: str) -> str:
        """
        Get a standard disclaimer by type.
        
        Args:
            disclaimer_type: Type of disclaimer
            
        Returns:
            Disclaimer text
        """
        return self.standard_disclaimers.get(
            disclaimer_type, 
            "This information is provided for guidance only. Consult official Medicare resources for definitive information."
        )
    
    def add_disclaimers(self, content: Union[str, Dict[str, Any]], disclaimers: List[str]) -> Union[str, Dict[str, Any]]:
        """
        Add disclaimers to content.
        
        Args:
            content: Content to add disclaimers to
            disclaimers: List of disclaimer types to add
            
        Returns:
            Content with disclaimers added
        """
        disclaimer_texts = [self.get_standard_disclaimer(d) for d in disclaimers]
        
        if isinstance(content, dict):
            # Deep copy the content to avoid modifying the original
            result = json.loads(json.dumps(content))
            
            # Add a disclaimers field or append to existing
            if "disclaimers" not in result:
                result["disclaimers"] = disclaimer_texts
            else:
                if isinstance(result["disclaimers"], list):
                    result["disclaimers"].extend(disclaimer_texts)
                else:
                    # If it's a string, convert to list
                    result["disclaimers"] = [result["disclaimers"]] + disclaimer_texts
            
            return result
        else:
            # For string content, add disclaimers at the end
            result = content
            
            if result and not result.endswith("\n"):
                result += "\n\n"
            else:
                result += "\n"
                
            result += "DISCLAIMERS:\n" + "\n".join([f"- {d.strip()}" for d in disclaimer_texts])
            
            return result
    
    def process(self, content: Union[str, Dict[str, Any]], content_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process content for regulatory compliance.
        
        Args:
            content: Content to process
            content_type: Type of content
            context: Optional context information
            
        Returns:
            Processing result with assessment and redacted content if needed
        """
        # Assess regulatory compliance
        assessment = self.assess_regulatory_compliance(content, content_type, context)
        
        result = {
            "assessment": assessment,
            "content": content
        }
        
        # If content contains PHI or PII, redact sensitive information
        if assessment.get("contains_phi", False) or assessment.get("contains_pii", False):
            self.logger.info("Content contains sensitive information, performing redaction")
            redaction_result = self.redact_sensitive_information(content, assessment.get("sensitive_entities", []))
            result["redacted_content"] = redaction_result["redacted_content"]
            result["redaction_result"] = redaction_result
        
        # Add necessary disclaimers
        if assessment.get("disclaimers_needed", []):
            self.logger.info(f"Adding {len(assessment['disclaimers_needed'])} disclaimers to content")
            result["content_with_disclaimers"] = self.add_disclaimers(
                result.get("redacted_content", content),
                assessment["disclaimers_needed"]
            )
        
        return result

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = RegulatoryAgent()
    
    # Test with sample content
    sample_content = """
    Medicare Benefit Guide for John Smith
    
    Dear Mr. Smith,
    
    Based on your enrollment in Medicare Part B (Medicare ID: 123-45-6789A) and your diagnosis 
    of Type 2 Diabetes on 01/15/2022, you are eligible for the following benefits:
    
    1. Diabetes self-management training
    2. Blood glucose monitors and supplies
    3. Therapeutic shoes and inserts (with a doctor's certification)
    
    To access these benefits, please contact Dr. Jane Johnson at Boston Medical Center 
    (555-123-4567) to schedule an appointment.
    
    For questions about your coverage, please call 1-800-MEDICARE or email us at 
    john.smith@example.com.
    
    Sincerely,
    Medicare Benefits Coordinator
    """
    
    # Process the content
    result = agent.process(sample_content, "guide")
    
    print("Regulatory Assessment:")
    print(f"HIPAA Compliant: {result['assessment']['hipaa_compliant']}")
    print(f"Contains PHI: {result['assessment']['contains_phi']}")
    print(f"Contains PII: {result['assessment']['contains_pii']}")
    print(f"Risk Level: {result['assessment']['overall_risk_level']}")
    
    if "redacted_content" in result:
        print("\nRedacted Content:")
        print(result["redacted_content"])
    
    if "content_with_disclaimers" in result:
        print("\nContent with Disclaimers:")
        print(result["content_with_disclaimers"]) 