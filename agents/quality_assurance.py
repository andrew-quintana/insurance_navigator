"""
Quality Assurance Agent

This agent is responsible for:
1. Validating output structure and format
2. Checking logical and factual consistency
3. Flagging low-confidence content
4. Escalating failed validations
5. Logging QA decisions for traceability

Based on FMEA analysis, this agent implements controls for:
- Recursive structure checking
- Self-consistency verification
- Confidence threshold tuning
- Required affirmative QA pass signals
- Centralized QA event logging
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Tuple, Optional, Union
from pydantic import BaseModel, Field, ValidationError
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from agents.base_agent import BaseAgent
from utils.prompt_loader import load_prompt

# Setup logging
logger = logging.getLogger("quality_assurance_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "quality_assurance.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Define output schemas
class ContentIssue(BaseModel):
    """Schema for a content issue identified during QA."""
    issue_type: str = Field(description="Type of issue (structure, factual, logical, clarity)")
    severity: int = Field(description="Severity of the issue (1-10)")
    location: str = Field(description="Where in the content the issue occurs")
    description: str = Field(description="Description of the issue")
    recommendation: str = Field(description="Recommended fix for the issue")
    requires_human_review: bool = Field(description="Whether the issue requires human review", default=False)

class FactualAssessment(BaseModel):
    """Schema for a factual assessment of content."""
    is_accurate: bool = Field(description="Whether the content is factually accurate")
    confidence: float = Field(description="Confidence in the assessment (0-1)")
    factual_issues: List[ContentIssue] = Field(description="Factual issues identified", default_factory=list)
    citations: List[str] = Field(description="Citations supporting factual claims", default_factory=list)
    uncertain_claims: List[str] = Field(description="Claims with uncertain factual basis", default_factory=list)

class StructuralAssessment(BaseModel):
    """Schema for a structural assessment of content."""
    is_well_structured: bool = Field(description="Whether the content is well-structured")
    confidence: float = Field(description="Confidence in the assessment (0-1)")
    structural_issues: List[ContentIssue] = Field(description="Structural issues identified", default_factory=list)
    missing_sections: List[str] = Field(description="Required sections that are missing", default_factory=list)
    invalid_formats: List[str] = Field(description="Elements with invalid formats", default_factory=list)

class QualityAssessment(BaseModel):
    """Output schema for quality assessment."""
    content_id: str = Field(description="Identifier for the assessed content")
    content_type: str = Field(description="Type of content assessed (guide, provider_list, strategy)")
    overall_quality: float = Field(description="Overall quality score (0-1)")
    passed_qa: bool = Field(description="Whether the content passed QA")
    factual_assessment: FactualAssessment = Field(description="Assessment of factual accuracy")
    structural_assessment: StructuralAssessment = Field(description="Assessment of structure")
    readability_score: float = Field(description="Score for readability (0-1)")
    clarity_score: float = Field(description="Score for clarity (0-1)")
    completeness_score: float = Field(description="Score for completeness (0-1)")
    consistency_score: float = Field(description="Score for internal consistency (0-1)")
    requires_escalation: bool = Field(description="Whether QA failure requires escalation")
    escalation_reason: Optional[str] = Field(description="Reason for escalation", default=None)
    confidence_threshold_applied: float = Field(description="Confidence threshold used in assessment")
    qa_decision: str = Field(description="Final QA decision (pass, fail, needs_revision)")
    qa_timestamp: str = Field(description="Timestamp of the QA assessment")

class QualityAssuranceAgent(BaseAgent):
    """Agent responsible for ensuring quality of outputs in the system."""
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize the agent with an optional language model."""
        # Initialize the base agent
        super().__init__(name="quality_assurance", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0))
        
        self.parser = PydanticOutputParser(pydantic_object=QualityAssessment)
        
        # Define expected content structures for various content types
        self._init_content_structure_templates()
        
        # Define system prompt for QA
        # Load the self.qa_system_prompt from file
        try:
            self.qa_system_prompt = load_prompt("quality_assurance_qa")
        except FileNotFoundError:
            self.logger.warning("Could not find quality_assurance_qa.md prompt file, using default prompt")
            # Load the self.qa_system_prompt from file
        try:
            self.qa_system_prompt = load_prompt("quality_assurance_qa_prompt")
        except FileNotFoundError:
            self.logger.warning("Could not find quality_assurance_qa_prompt.md prompt file, using default prompt")
            self.qa_system_prompt = """
            Default prompt for self.qa_system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the QA prompt template
        self.qa_template = PromptTemplate(
            template="""
            {system_prompt}
            
            CONTENT TYPE: {content_type}
            
            EXPECTED STRUCTURE:
            {expected_structure}
            
            CONTENT TO REVIEW:
            {content}
            
            ADDITIONAL CONTEXT:
            {context}
            
            Conduct a thorough quality assessment of this content.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "content_type", "expected_structure", "content", "context"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        # Create the QA chain
        self.qa_chain = (
            {"system_prompt": lambda _: self.qa_system_prompt,
             "content_type": lambda x: x["content_type"],
             "expected_structure": lambda x: self._get_structure_template(x["content_type"]),
             "content": lambda x: json.dumps(x["content"], indent=2) if isinstance(x["content"], dict) else x["content"],
             "context": lambda x: json.dumps(x.get("context", {}), indent=2)}
            | self.qa_template
            | self.llm
            | self.parser
        )
        
        # Set default QA thresholds
        self.thresholds = {
            "guide": 0.85,
            "provider_list": 0.80,
            "strategy": 0.80,
            "general": 0.75
        }
        
        logger.info("Quality Assurance Agent initialized")
    
    def _init_content_structure_templates(self):
        """Initialize templates for different content types."""
        self.structure_templates = {
            "guide": """
            A Medicare guide should have the following structure:
            1. Title - Clear and descriptive
            2. Introduction - Explaining the purpose of the guide
            3. Coverage Overview - What Medicare covers for this topic
            4. Step-by-Step Instructions - Clear numbered steps
            5. Required Documents/Information - What the user needs
            6. Timeline/Deadlines - Any relevant time constraints
            7. Costs/Financial Information - Expected costs, if applicable
            8. Contact Information - Who to contact for assistance
            9. Additional Resources - Links, phone numbers, etc.
            10. Disclaimers - Legal notices and disclaimers
            
            Each section should be clearly labeled and formatted consistently.
            """,
            
            "provider_list": """
            A provider list should have the following structure:
            1. Search Parameters - What criteria were used for the search
            2. Results Summary - Number of providers found, overview
            3. Provider Entries - For each provider:
               a. Name and Credentials
               b. Specialties
               c. Location/Address
               d. Contact Information
               e. Network Status
               f. Accepting New Patients Status
            4. Sorting/Filtering Options - How results can be refined
            5. Disclaimers - When the data was last updated, verification notices
            
            Provider information should be consistently formatted and include all required fields.
            """,
            
            "strategy": """
            A service access strategy should have the following structure:
            1. Strategy Overview - Summary of the approach
            2. User Need Assessment - Analysis of the user's requirements
            3. Recommended Services - Services that meet the user's needs
            4. Step-by-Step Action Plan - Concrete actions for the user to take
            5. Timeline - Expected timeframes for each step
            6. Required Resources - What the user will need
            7. Potential Challenges - Anticipated difficulties and solutions
            8. Alternative Approaches - Backup options if the primary strategy fails
            9. Success Indicators - How to know if the strategy is working
            10. Follow-up Actions - Next steps after implementation
            
            The strategy should be logical, feasible, and directly address the user's needs.
            """
        }
    
    def _get_structure_template(self, content_type: str) -> str:
        """Get the structure template for a given content type."""
        return self.structure_templates.get(content_type, "No specific structure template available for this content type.")
    
    def _get_confidence_threshold(self, content_type: str) -> float:
        """Get the confidence threshold for a given content type."""
        return self.thresholds.get(content_type, self.thresholds["general"])
    
    @BaseAgent.track_performance
    def assess_quality(self, content: Union[str, Dict[str, Any]], content_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Assess the quality of content.
        
        Args:
            content: The content to assess (string or dict)
            content_type: Type of content (guide, provider_list, strategy)
            context: Optional context information
            
        Returns:
            Quality assessment
        """
        start_time = time.time()
        
        # Generate a content ID if not provided in context
        content_id = context.get("content_id") if context else f"{content_type}_{int(time.time())}"
        
        # Log the request
        self.logger.info(f"Assessing quality of {content_type} (ID: {content_id})...")
        
        try:
            # Get the confidence threshold for this content type
            confidence_threshold = self._get_confidence_threshold(content_type)
            
            # Prepare input for the QA chain
            input_dict = {
                "content_type": content_type,
                "content": content,
                "context": context or {}
            }
            
            # Perform quality assessment
            assessment = self.qa_chain.invoke(input_dict)
            
            # Add content ID and timestamp if not provided
            if not assessment.content_id:
                assessment.content_id = content_id
            assessment.qa_timestamp = assessment.qa_timestamp or time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Set the confidence threshold that was applied
            assessment.confidence_threshold_applied = confidence_threshold
            
            # Determine whether content passes QA based on threshold and assessments
            assessment.passed_qa = (
                assessment.overall_quality >= confidence_threshold and
                assessment.factual_assessment.is_accurate and
                assessment.structural_assessment.is_well_structured and
                not assessment.requires_escalation
            )
            
            # Set final QA decision
            if assessment.passed_qa:
                assessment.qa_decision = "pass"
            elif assessment.requires_escalation:
                assessment.qa_decision = "needs_human_review"
            else:
                assessment.qa_decision = "needs_revision"
            
            # Convert to dictionary
            result = assessment.dict()
            
            # Log the result
            self.logger.info(f"Quality assessment for {content_type} (ID: {content_id}): {result['qa_decision']}")
            self.logger.info(f"Overall quality: {result['overall_quality']:.2f}, Threshold: {confidence_threshold:.2f}")
            
            if not result['passed_qa']:
                if result['factual_assessment']['factual_issues']:
                    self.logger.warning(f"Factual issues found: {len(result['factual_assessment']['factual_issues'])}")
                if result['structural_assessment']['structural_issues']:
                    self.logger.warning(f"Structural issues found: {len(result['structural_assessment']['structural_issues'])}")
                if result['requires_escalation']:
                    self.logger.warning(f"Content requires escalation: {result['escalation_reason']}")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Quality assessment completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in quality assessment: {str(e)}")
            
            # Create a fallback assessment in case of error
            fallback = {
                "content_id": content_id,
                "content_type": content_type,
                "overall_quality": 0.0,
                "passed_qa": False,
                "factual_assessment": {
                    "is_accurate": False,
                    "confidence": 0.0,
                    "factual_issues": [{
                        "issue_type": "system_error",
                        "severity": 10,
                        "location": "entire_content",
                        "description": f"QA system error: {str(e)}",
                        "recommendation": "Retry QA assessment or perform manual review",
                        "requires_human_review": True
                    }],
                    "citations": [],
                    "uncertain_claims": []
                },
                "structural_assessment": {
                    "is_well_structured": False,
                    "confidence": 0.0,
                    "structural_issues": [],
                    "missing_sections": [],
                    "invalid_formats": []
                },
                "readability_score": 0.0,
                "clarity_score": 0.0,
                "completeness_score": 0.0,
                "consistency_score": 0.0,
                "requires_escalation": True,
                "escalation_reason": f"QA assessment failed with error: {str(e)}",
                "confidence_threshold_applied": self._get_confidence_threshold(content_type),
                "qa_decision": "needs_human_review",
                "qa_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            }
            
            return fallback
    
    def validate_structure(self, content: Dict[str, Any], content_type: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate the structure of content against the expected structure.
        
        Args:
            content: The content to validate
            content_type: Type of content
            
        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []
        
        if content_type == "guide":
            required_sections = ["title", "introduction", "steps", "requirements", "timeline", "contacts"]
            for section in required_sections:
                if section not in content or not content[section]:
                    issues.append({
                        "issue_type": "structure",
                        "severity": 7,
                        "location": f"section:{section}",
                        "description": f"Required section '{section}' is missing or empty",
                        "recommendation": f"Add the '{section}' section with appropriate content"
                    })
        
        elif content_type == "provider_list":
            if "providers" not in content or not isinstance(content["providers"], list):
                issues.append({
                    "issue_type": "structure",
                    "severity": 8,
                    "location": "root",
                    "description": "Providers list is missing or not an array",
                    "recommendation": "Add a valid 'providers' array to the content"
                })
            else:
                for i, provider in enumerate(content["providers"]):
                    required_fields = ["name", "specialty", "location", "contact", "network_status"]
                    for field in required_fields:
                        if field not in provider or not provider[field]:
                            issues.append({
                                "issue_type": "structure",
                                "severity": 6,
                                "location": f"providers[{i}].{field}",
                                "description": f"Required field '{field}' is missing or empty for provider {i+1}",
                                "recommendation": f"Add the '{field}' information for provider {i+1}"
                            })
        
        elif content_type == "strategy":
            required_sections = ["overview", "steps", "timeline", "resources", "challenges", "alternatives"]
            for section in required_sections:
                if section not in content or not content[section]:
                    issues.append({
                        "issue_type": "structure",
                        "severity": 7,
                        "location": f"section:{section}",
                        "description": f"Required section '{section}' is missing or empty",
                        "recommendation": f"Add the '{section}' section with appropriate content"
                    })
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def escalate_if_needed(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if a QA assessment requires escalation and update it accordingly.
        
        Args:
            assessment: The quality assessment
            
        Returns:
            Updated assessment with escalation information
        """
        result = assessment.copy()
        
        # Check for critical issues that require escalation
        critical_issues = []
        
        # Check factual issues
        for issue in result["factual_assessment"]["factual_issues"]:
            if issue["severity"] >= 7 or issue["requires_human_review"]:
                critical_issues.append(issue)
        
        # Check structural issues
        for issue in result["structural_assessment"]["structural_issues"]:
            if issue["severity"] >= 7 or issue["requires_human_review"]:
                critical_issues.append(issue)
        
        # Check for low overall quality
        overall_quality_threshold = 0.5
        if result["overall_quality"] < overall_quality_threshold:
            critical_issues.append({
                "issue_type": "overall_quality",
                "severity": 8,
                "location": "entire_content",
                "description": f"Overall quality score ({result['overall_quality']:.2f}) is below minimum threshold ({overall_quality_threshold:.2f})",
                "recommendation": "Perform comprehensive review and revision",
                "requires_human_review": True
            })
        
        # Update escalation information
        if critical_issues:
            result["requires_escalation"] = True
            issue_descriptions = [f"{issue['issue_type']} (severity {issue['severity']}): {issue['description']}" for issue in critical_issues]
            result["escalation_reason"] = "Critical issues detected: " + "; ".join(issue_descriptions)
        else:
            result["requires_escalation"] = False
            result["escalation_reason"] = None
        
        return result
    
    def process(self, content: Union[str, Dict[str, Any]], content_type: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process content for quality assessment.
        
        Args:
            content: The content to assess
            content_type: Type of content
            context: Optional context information
            
        Returns:
            Quality assessment
        """
        assessment = self.assess_quality(content, content_type, context)
        assessment = self.escalate_if_needed(assessment)
        return assessment

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = QualityAssuranceAgent()
    
    # Test with sample guide
    sample_guide = {
        "title": "Enrolling in Medicare Part B",
        "introduction": "This guide helps you understand how to enroll in Medicare Part B.",
        "steps": [
            "Step 1: Check your eligibility",
            "Step 2: Determine your enrollment period",
            "Step 3: Complete Form CMS-40B",
            "Step 4: Submit your application",
            "Step 5: Wait for your Medicare card"
        ],
        "requirements": [
            "Social Security card",
            "Proof of identity",
            "Form CMS-40B"
        ],
        "timeline": "Process typically takes 2-4 weeks",
        "contacts": "Social Security Administration: 1-800-772-1213",
        "costs": "Standard Part B premium is $174.70 per month (2023)"
    }
    
    # Process the guide
    assessment = agent.process(sample_guide, "guide")
    
    print(f"Quality Assessment for Guide")
    print(f"Overall Quality: {assessment['overall_quality']:.2f}")
    print(f"Passed QA: {assessment['passed_qa']}")
    print(f"Decision: {assessment['qa_decision']}")
    
    if assessment['factual_assessment']['factual_issues']:
        print("\nFactual Issues:")
        for issue in assessment['factual_assessment']['factual_issues']:
            print(f"- {issue['description']} (Severity: {issue['severity']})")
    
    if assessment['structural_assessment']['structural_issues']:
        print("\nStructural Issues:")
        for issue in assessment['structural_assessment']['structural_issues']:
            print(f"- {issue['description']} (Severity: {issue['severity']})")
    
    if assessment['requires_escalation']:
        print(f"\nRequires Escalation: {assessment['escalation_reason']}") 