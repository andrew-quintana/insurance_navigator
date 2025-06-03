#!/usr/bin/env python3
"""
Script to fix import statements after agent reorganization.
Updates all __init__.py files to use the new flattened structure.
"""

import os
from pathlib import Path

def update_main_agents_init():
    """Update the main agents/__init__.py file"""
    init_file = Path("agents/__init__.py")
    
    content = '''"""
Agents package for the Insurance Navigator system.

This package contains all the agent modules that make up the multi-agent system.
Each agent is responsible for a specific task in the insurance navigation process.
"""

# Import base agent
from agents.base_agent import BaseAgent

# Import specialized agents
from agents.prompt_security.prompt_security import PromptSecurityAgent
from agents.patient_navigator.patient_navigator import PatientNavigatorAgent
from agents.task_requirements.task_requirements import TaskRequirementsAgent
from agents.service_access_strategy.service_access_strategy import ServiceAccessStrategyAgent
from agents.chat_communicator.chat_communicator import ChatCommunicatorAgent
from agents.regulatory.regulatory import RegulatoryAgent

# Import models
from agents.prompt_security.models.security_models import SecurityCheck
from agents.patient_navigator.models.navigator_models import (
    NavigatorOutput, MetaIntent, ClinicalContext, 
    ServiceIntent, Metadata, BodyLocation
)
from agents.task_requirements.models.task_models import (
    DocumentStatus, ReactStep, TaskProcessingResult
)
from agents.service_access_strategy.models.strategy_models import (
    ServiceAccessStrategy, ServiceMatch, ActionStep
)

# Import exceptions
from agents.common.exceptions import (
    InsuranceNavigatorException,
    ConfigurationException,
    InvalidConfigurationError,
    MissingConfigurationError,
    AgentException,
    PromptSecurityException,
    PromptInjectionDetected,
    PromptSecurityValidationError,
    PromptSecurityConfigError,
    PatientNavigatorException,
    PatientNavigatorProcessingError,
    PatientNavigatorOutputParsingError,
    PatientNavigatorSessionError,
    TaskRequirementsException,
    TaskRequirementsProcessingError,
    DocumentValidationError,
    ReactProcessingError,
    ServiceAccessStrategyException,
    StrategyDevelopmentError,
    PolicyComplianceError,
    ProviderLookupError,
    APIException,
    ModelAPIException,
    ExternalServiceException
)

__all__ = [
    # Agent classes
    'BaseAgent', 
    'PromptSecurityAgent',
    'PatientNavigatorAgent',
    'TaskRequirementsAgent',
    'ServiceAccessStrategyAgent',
    'ChatCommunicatorAgent',
    'RegulatoryAgent',
    
    # Model classes
    'SecurityCheck',
    'NavigatorOutput', 'MetaIntent', 'ClinicalContext', 'ServiceIntent', 'Metadata', 'BodyLocation',
    'DocumentStatus', 'ReactStep', 'TaskProcessingResult',
    'ServiceAccessStrategy', 'ServiceMatch', 'ActionStep',
    
    # Base exceptions
    'InsuranceNavigatorException',
    'ConfigurationException',
    'InvalidConfigurationError',
    'MissingConfigurationError',
    'AgentException',
    'APIException',
    'ModelAPIException',
    'ExternalServiceException',
    
    # Agent-specific exceptions
    'PromptSecurityException',
    'PromptInjectionDetected',
    'PromptSecurityValidationError',
    'PromptSecurityConfigError',
    'PatientNavigatorException',
    'PatientNavigatorProcessingError',
    'PatientNavigatorOutputParsingError',
    'PatientNavigatorSessionError',
    'TaskRequirementsException',
    'TaskRequirementsProcessingError',
    'DocumentValidationError',
    'ReactProcessingError',
    'ServiceAccessStrategyException',
    'StrategyDevelopmentError',
    'PolicyComplianceError',
    'ProviderLookupError'
]
'''
    
    with open(init_file, 'w') as f:
        f.write(content)
    print("Updated main agents/__init__.py")

def update_agent_init_files():
    """Update individual agent __init__.py files"""
    agents = [
        'prompt_security',
        'patient_navigator', 
        'task_requirements',
        'service_access_strategy',
        'chat_communicator',
        'regulatory'
    ]
    
    for agent in agents:
        init_file = Path(f"agents/{agent}/__init__.py")
        if init_file.exists():
            # Convert agent name to class name (e.g., prompt_security -> PromptSecurityAgent)
            class_name = ''.join(word.capitalize() for word in agent.split('_')) + 'Agent'
            
            content = f'''from .{agent} import {class_name}

__all__ = ['{class_name}']
'''
            with open(init_file, 'w') as f:
                f.write(content)
            print(f"Updated agents/{agent}/__init__.py")

def main():
    """Main function to update all import statements"""
    print("Fixing import statements after agent reorganization...")
    
    update_main_agents_init()
    update_agent_init_files()
    
    print("\nImport fixes complete!")

if __name__ == "__main__":
    main() 