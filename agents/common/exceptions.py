"""
Common exceptions for the Insurance Navigator system.

This module defines all the exception classes used by the various agents and components
of the Insurance Navigator system, providing a standardized way to handle errors.
"""

class InsuranceNavigatorException(Exception):
    """Base exception for all Insurance Navigator system errors."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# Configuration exceptions
class ConfigurationException(InsuranceNavigatorException):
    """Base exception for configuration errors."""
    pass

class InvalidConfigurationError(ConfigurationException):
    """Exception raised when configuration is invalid."""
    pass

class MissingConfigurationError(ConfigurationException):
    """Exception raised when required configuration is missing."""
    pass


# Agent exceptions
class AgentException(InsuranceNavigatorException):
    """Base exception for agent errors."""
    pass


# Prompt Security exceptions
class PromptSecurityException(AgentException):
    """Base exception for prompt security agent errors."""
    pass

class PromptInjectionDetected(PromptSecurityException):
    """Exception raised when a prompt injection is detected."""
    def __init__(self, message: str, threat_type: str = "unknown", severity: str = "unknown"):
        self.threat_type = threat_type
        self.severity = severity
        super().__init__(f"{message} (Type: {threat_type}, Severity: {severity})")

class PromptSecurityValidationError(PromptSecurityException):
    """Exception raised when input validation fails in prompt security."""
    pass

class PromptSecurityConfigError(PromptSecurityException):
    """Exception raised when prompt security agent has configuration issues."""
    pass


# Patient Navigator exceptions
class PatientNavigatorException(AgentException):
    """Base exception for patient navigator agent errors."""
    pass

class PatientNavigatorProcessingError(PatientNavigatorException):
    """Exception raised when there's an error processing a patient navigation request."""
    pass

class PatientNavigatorOutputParsingError(PatientNavigatorException):
    """Exception raised when output parsing fails in the patient navigator."""
    pass

class PatientNavigatorSessionError(PatientNavigatorException):
    """Exception raised when there's an error with the patient navigator session."""
    pass


# Task Requirements exceptions
class TaskRequirementsException(AgentException):
    """Base exception for task requirements agent errors."""
    pass

class TaskRequirementsProcessingError(TaskRequirementsException):
    """Exception raised when there's an error processing requirements."""
    pass

class DocumentValidationError(TaskRequirementsException):
    """Exception raised when document validation fails."""
    pass

class ReactProcessingError(TaskRequirementsException):
    """Exception raised when there's an error in the ReAct loop."""
    pass


# Service Access Strategy exceptions
class ServiceAccessStrategyException(AgentException):
    """Base exception for service access strategy agent errors."""
    pass

class StrategyDevelopmentError(ServiceAccessStrategyException):
    """Exception raised when there's an error developing a service access strategy."""
    pass

class PolicyComplianceError(ServiceAccessStrategyException):
    """Exception raised when there's an error checking policy compliance."""
    pass

class ProviderLookupError(ServiceAccessStrategyException):
    """Exception raised when there's an error looking up providers."""
    pass


# Database Agent exceptions
class DatabaseAgentException(AgentException):
    """Base exception for database agent errors."""
    pass

class DatabaseOperationError(DatabaseAgentException):
    """Exception raised when there's an error executing a database operation."""
    pass

class DatabaseConnectionError(DatabaseAgentException):
    """Exception raised when there's an error connecting to the database."""
    pass

class DatabaseQueryError(DatabaseAgentException):
    """Exception raised when there's an error in the database query."""
    pass

class DataValidationError(DatabaseAgentException):
    """Exception raised when data validation fails."""
    pass


# Regulatory Agent exceptions
class RegulatoryAgentException(AgentException):
    """Base exception for regulatory agent errors."""
    pass

class RegulatoryComplianceError(RegulatoryAgentException):
    """Exception raised when there's an error assessing regulatory compliance."""
    pass

class RegulatoryRequirementError(RegulatoryAgentException):
    """Exception raised when there's an error with regulatory requirements."""
    pass

class ComplianceDocumentationError(RegulatoryAgentException):
    """Exception raised when there's an error with compliance documentation."""
    pass


# API exceptions
class APIException(InsuranceNavigatorException):
    """Base exception for API errors."""
    pass

class ModelAPIException(APIException):
    """Exception raised when there's an error with the model API."""
    pass

class ExternalServiceException(APIException):
    """Exception raised when there's an error with an external service."""
    pass 