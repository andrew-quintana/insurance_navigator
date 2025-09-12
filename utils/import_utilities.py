"""
Import Utilities for Insurance Navigator

This module provides safe import functions and error handling for all
project modules to prevent "No module named 'agents'" errors.

Usage:
    from utils.import_utilities import safe_import_agents, safe_import_rag_tool
    
    agents = safe_import_agents()
    if agents:
        # Use agents module
        pass
"""

import logging
import sys
from typing import Any, Optional, Dict, List
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

# Global flag to track if paths have been set up
_paths_setup = False


def ensure_paths_setup():
    """Ensure Python paths are set up for project imports"""
    global _paths_setup
    
    if not _paths_setup:
        try:
            # Add project root to Python path
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
            
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
                logger.debug(f"Added project root to Python path: {project_root}")
            
            # Add common module directories
            common_dirs = [
                project_root / 'agents',
                project_root / 'backend',
                project_root / 'utils',
                project_root / 'config',
                project_root / 'db',
                project_root / 'shared'
            ]
            
            for dir_path in common_dirs:
                if dir_path.exists() and str(dir_path) not in sys.path:
                    sys.path.insert(0, str(dir_path))
                    logger.debug(f"Added directory to Python path: {dir_path}")
            
            _paths_setup = True
            logger.info("Python paths setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup Python paths: {str(e)}")
            raise


def safe_import(module_name: str, fallback=None, required: bool = False):
    """
    Safely import a module with error handling.
    
    Args:
        module_name: Name of the module to import
        fallback: Fallback value if import fails
        required: If True, raise exception on import failure
        
    Returns:
        The imported module or fallback value
        
    Raises:
        ImportError: If required=True and import fails
    """
    ensure_paths_setup()
    
    try:
        __import__(module_name)
        return sys.modules[module_name]
    except ImportError as e:
        error_msg = f"Failed to import {module_name}: {str(e)}"
        if required:
            logger.error(error_msg)
            raise ImportError(error_msg) from e
        else:
            logger.warning(error_msg)
            return fallback
    except Exception as e:
        error_msg = f"Unexpected error importing {module_name}: {str(e)}"
        if required:
            logger.error(error_msg)
            raise ImportError(error_msg) from e
        else:
            logger.warning(error_msg)
            return fallback


def safe_import_from(module_name: str, attribute_name: str, fallback=None, required: bool = False):
    """
    Safely import an attribute from a module.
    
    Args:
        module_name: Name of the module to import from
        attribute_name: Name of the attribute to import
        fallback: Fallback value if import fails
        required: If True, raise exception on import failure
        
    Returns:
        The imported attribute or fallback value
    """
    module = safe_import(module_name, required=required)
    if module is None:
        return fallback
    
    try:
        return getattr(module, attribute_name)
    except AttributeError as e:
        error_msg = f"Attribute {attribute_name} not found in {module_name}: {str(e)}"
        if required:
            logger.error(error_msg)
            raise AttributeError(error_msg) from e
        else:
            logger.warning(error_msg)
            return fallback


# Specific import functions for common modules
def safe_import_agents():
    """Safely import the agents module"""
    return safe_import('agents')


def safe_import_base_agent():
    """Safely import BaseAgent class"""
    return safe_import_from('agents.base_agent', 'BaseAgent')


def safe_import_rag_tool():
    """Safely import RAGTool class"""
    return safe_import_from('agents.tooling.rag.core', 'RAGTool')


def safe_import_retrieval_config():
    """Safely import RetrievalConfig class"""
    return safe_import_from('agents.tooling.rag.core', 'RetrievalConfig')


def safe_import_information_retrieval_agent():
    """Safely import InformationRetrievalAgent class"""
    return safe_import_from('agents.patient_navigator.information_retrieval.agent', 'InformationRetrievalAgent')


def safe_import_information_retrieval_input():
    """Safely import InformationRetrievalInput class"""
    return safe_import_from('agents.patient_navigator.information_retrieval.models', 'InformationRetrievalInput')


def safe_import_information_retrieval_output():
    """Safely import InformationRetrievalOutput class"""
    return safe_import_from('agents.patient_navigator.information_retrieval.models', 'InformationRetrievalOutput')


def safe_import_patient_navigator_chat_interface():
    """Safely import PatientNavigatorChatInterface class"""
    return safe_import_from('agents.patient_navigator.chat_interface', 'PatientNavigatorChatInterface')


def safe_import_chat_message():
    """Safely import ChatMessage class"""
    return safe_import_from('agents.patient_navigator.chat_interface', 'ChatMessage')


def safe_import_supervisor_workflow():
    """Safely import SupervisorWorkflow class"""
    return safe_import_from('agents.patient_navigator.supervisor.workflow', 'SupervisorWorkflow')


def safe_import_workflow_prescription_agent():
    """Safely import WorkflowPrescriptionAgent class"""
    return safe_import_from('agents.patient_navigator.supervisor.workflow_prescription.agent', 'WorkflowPrescriptionAgent')


def safe_import_database_manager():
    """Safely import DatabaseManager class"""
    return safe_import_from('shared.db', 'DatabaseManager')


def safe_import_storage_manager():
    """Safely import StorageManager class"""
    return safe_import_from('shared.storage', 'StorageManager')


def safe_import_service_router():
    """Safely import ServiceRouter class"""
    return safe_import_from('shared.external.service_router', 'ServiceRouter')


def safe_import_worker_config():
    """Safely import WorkerConfig class"""
    return safe_import_from('shared.config.worker_config', 'WorkerConfig')


def safe_import_enhanced_service_client():
    """Safely import EnhancedServiceClient class"""
    return safe_import_from('shared.external.enhanced_service_client', 'EnhancedServiceClient')


def safe_import_error_handler():
    """Safely import WorkerErrorHandler class"""
    return safe_import_from('shared.external.error_handler', 'WorkerErrorHandler')


# Validation functions
def validate_agents_imports() -> Dict[str, bool]:
    """Validate that all agents-related imports are working"""
    results = {}
    
    # Test core agents imports
    results['agents'] = safe_import_agents() is not None
    results['base_agent'] = safe_import_base_agent() is not None
    results['rag_tool'] = safe_import_rag_tool() is not None
    results['retrieval_config'] = safe_import_retrieval_config() is not None
    
    # Test patient navigator imports
    results['information_retrieval_agent'] = safe_import_information_retrieval_agent() is not None
    results['information_retrieval_input'] = safe_import_information_retrieval_input() is not None
    results['information_retrieval_output'] = safe_import_information_retrieval_output() is not None
    results['patient_navigator_chat_interface'] = safe_import_patient_navigator_chat_interface() is not None
    results['chat_message'] = safe_import_chat_message() is not None
    results['supervisor_workflow'] = safe_import_supervisor_workflow() is not None
    results['workflow_prescription_agent'] = safe_import_workflow_prescription_agent() is not None
    
    # Test shared imports
    results['database_manager'] = safe_import_database_manager() is not None
    results['storage_manager'] = safe_import_storage_manager() is not None
    results['service_router'] = safe_import_service_router() is not None
    results['worker_config'] = safe_import_worker_config() is not None
    results['enhanced_service_client'] = safe_import_enhanced_service_client() is not None
    results['error_handler'] = safe_import_error_handler() is not None
    
    return results


def get_import_status_report() -> Dict[str, Any]:
    """Get a comprehensive import status report"""
    validation_results = validate_agents_imports()
    
    total_imports = len(validation_results)
    successful_imports = sum(validation_results.values())
    failed_imports = total_imports - successful_imports
    
    return {
        'total_imports': total_imports,
        'successful_imports': successful_imports,
        'failed_imports': failed_imports,
        'success_rate': successful_imports / total_imports if total_imports > 0 else 0,
        'validation_results': validation_results,
        'recommendations': _get_import_recommendations(validation_results)
    }


def _get_import_recommendations(validation_results: Dict[str, bool]) -> List[str]:
    """Get recommendations for fixing import issues"""
    recommendations = []
    
    if not validation_results.get('agents', False):
        recommendations.append("Check that agents/__init__.py exists and is properly configured")
        recommendations.append("Ensure project root is in PYTHONPATH")
        recommendations.append("Run scripts from project root directory")
    
    if not validation_results.get('rag_tool', False):
        recommendations.append("Check that agents/tooling/rag/core.py exists")
        recommendations.append("Verify RAGTool class is properly defined")
    
    if not validation_results.get('information_retrieval_agent', False):
        recommendations.append("Check that agents/patient_navigator/information_retrieval/agent.py exists")
        recommendations.append("Verify InformationRetrievalAgent class is properly defined")
    
    if not validation_results.get('database_manager', False):
        recommendations.append("Check that shared/db.py exists")
        recommendations.append("Verify DatabaseManager class is properly defined")
    
    return recommendations


# Context manager for safe imports
class SafeImportContext:
    """Context manager for safe imports with automatic cleanup"""
    
    def __init__(self, modules: List[str]):
        self.modules = modules
        self.imported_modules = {}
    
    def __enter__(self):
        for module_name in self.modules:
            module = safe_import(module_name)
            if module:
                self.imported_modules[module_name] = module
        return self.imported_modules
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass


# Decorator for functions that need safe imports
def with_safe_imports(*module_names):
    """Decorator to ensure safe imports before function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            ensure_paths_setup()
            with SafeImportContext(module_names):
                return func(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test the import utilities
    print("Import Utilities Test")
    print("=" * 50)
    
    # Get import status report
    report = get_import_status_report()
    
    print(f"Total Imports: {report['total_imports']}")
    print(f"Successful: {report['successful_imports']}")
    print(f"Failed: {report['failed_imports']}")
    print(f"Success Rate: {report['success_rate']:.2%}")
    
    print("\nDetailed Results:")
    for module, success in report['validation_results'].items():
        status = "✅" if success else "❌"
        print(f"  {status} {module}")
    
    if report['recommendations']:
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
