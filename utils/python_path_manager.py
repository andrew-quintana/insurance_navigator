"""
Python Path Manager for Insurance Navigator

This module provides centralized Python path management to prevent
"No module named 'agents'" and similar import errors throughout the system.

Features:
- Automatic project root detection
- Consistent path setup across all scripts
- Import validation and error handling
- Deployment environment detection
- Module availability checking
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import importlib.util
import traceback


class PythonPathManager:
    """
    Centralized Python path manager for consistent module imports.
    
    This class ensures that all modules can be imported correctly regardless
    of the current working directory or script location.
    """
    
    def __init__(self):
        self.project_root = self._detect_project_root()
        self.original_path = sys.path.copy()
        self.setup_logging()
        self._setup_paths()
    
    def _detect_project_root(self) -> Path:
        """
        Detect the project root directory by looking for key files.
        
        Returns:
            Path: The project root directory
        """
        current_path = Path(__file__).resolve()
        
        # Look for project root indicators
        indicators = [
            'main.py',
            'requirements.txt',
            'pyproject.toml',
            'setup.py',
            '.git',
            'agents',
            'backend',
            'ui'
        ]
        
        # Walk up the directory tree looking for indicators
        for path in [current_path] + list(current_path.parents):
            if any((path / indicator).exists() for indicator in indicators):
                return path
        
        # Fallback to current working directory
        return Path.cwd()
    
    def setup_logging(self):
        """Setup logging for the path manager"""
        self.logger = logging.getLogger('python_path_manager')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _setup_paths(self):
        """Setup Python paths for the project"""
        try:
            # Add project root to Python path
            if str(self.project_root) not in sys.path:
                sys.path.insert(0, str(self.project_root))
                self.logger.info(f"Added project root to Python path: {self.project_root}")
            
            # Add common module directories
            common_dirs = [
                self.project_root / 'agents',
                self.project_root / 'backend',
                self.project_root / 'utils',
                self.project_root / 'config',
                self.project_root / 'db',
                self.project_root / 'shared'
            ]
            
            for dir_path in common_dirs:
                if dir_path.exists() and str(dir_path) not in sys.path:
                    sys.path.insert(0, str(dir_path))
                    self.logger.debug(f"Added directory to Python path: {dir_path}")
            
            self.logger.info("Python paths setup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Python paths: {str(e)}")
            raise
    
    def get_project_root(self) -> Path:
        """Get the project root directory"""
        return self.project_root
    
    def add_path(self, path: str) -> bool:
        """
        Add a path to sys.path if it exists and isn't already there.
        
        Args:
            path: Path to add
            
        Returns:
            bool: True if path was added, False otherwise
        """
        try:
            path_obj = Path(path).resolve()
            if path_obj.exists() and str(path_obj) not in sys.path:
                sys.path.insert(0, str(path_obj))
                self.logger.debug(f"Added path: {path_obj}")
                return True
            return False
        except Exception as e:
            self.logger.warning(f"Failed to add path {path}: {str(e)}")
            return False
    
    def validate_import(self, module_name: str) -> Dict[str, Any]:
        """
        Validate that a module can be imported.
        
        Args:
            module_name: Name of the module to validate
            
        Returns:
            Dict containing validation results
        """
        result = {
            'module_name': module_name,
            'can_import': False,
            'error': None,
            'module_path': None,
            'import_time': None
        }
        
        try:
            import time
            start_time = time.time()
            
            # Try to import the module
            module = importlib.import_module(module_name)
            
            result['can_import'] = True
            result['module_path'] = getattr(module, '__file__', None)
            result['import_time'] = time.time() - start_time
            
            self.logger.debug(f"Successfully validated import: {module_name}")
            
        except ImportError as e:
            result['error'] = f"ImportError: {str(e)}"
            self.logger.warning(f"Import validation failed for {module_name}: {str(e)}")
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error validating {module_name}: {str(e)}")
        
        return result
    
    def safe_import(self, module_name: str, fallback=None):
        """
        Safely import a module with fallback handling.
        
        Args:
            module_name: Name of the module to import
            fallback: Fallback value if import fails
            
        Returns:
            The imported module or fallback value
        """
        try:
            return importlib.import_module(module_name)
        except ImportError as e:
            self.logger.warning(f"Failed to import {module_name}: {str(e)}")
            return fallback
        except Exception as e:
            self.logger.error(f"Unexpected error importing {module_name}: {str(e)}")
            return fallback
    
    def get_available_modules(self, base_path: Optional[Path] = None) -> List[str]:
        """
        Get list of available modules in a directory.
        
        Args:
            base_path: Base path to search (defaults to project root)
            
        Returns:
            List of available module names
        """
        if base_path is None:
            base_path = self.project_root
        
        modules = []
        
        try:
            for py_file in base_path.rglob('*.py'):
                if py_file.name == '__init__.py':
                    # This is a package
                    rel_path = py_file.relative_to(base_path)
                    module_name = str(rel_path.parent).replace(os.sep, '.')
                    if module_name and module_name not in modules:
                        modules.append(module_name)
                else:
                    # This is a module
                    rel_path = py_file.relative_to(base_path)
                    module_name = str(rel_path.with_suffix('')).replace(os.sep, '.')
                    if module_name and module_name not in modules:
                        modules.append(module_name)
        
        except Exception as e:
            self.logger.error(f"Error scanning for modules: {str(e)}")
        
        return sorted(modules)
    
    def check_critical_modules(self) -> Dict[str, bool]:
        """
        Check if critical modules are available.
        
        Returns:
            Dict mapping module names to availability status
        """
        critical_modules = [
            'agents',
            'agents.base_agent',
            'agents.patient_navigator',
            'agents.tooling.rag.core',
            'db.services',
            'shared.external',
            'utils'
        ]
        
        results = {}
        for module in critical_modules:
            validation = self.validate_import(module)
            results[module] = validation['can_import']
        
        return results
    
    def reset_paths(self):
        """Reset sys.path to original state"""
        sys.path.clear()
        sys.path.extend(self.original_path)
        self.logger.info("Python paths reset to original state")
    
    def get_path_info(self) -> Dict[str, Any]:
        """Get information about current Python path setup"""
        return {
            'project_root': str(self.project_root),
            'current_working_dir': str(Path.cwd()),
            'python_path_count': len(sys.path),
            'python_paths': sys.path[:10],  # First 10 paths
            'critical_modules_status': self.check_critical_modules()
        }


# Global instance
_path_manager = None


def get_path_manager() -> PythonPathManager:
    """Get the global path manager instance"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PythonPathManager()
    return _path_manager


def setup_python_path() -> PythonPathManager:
    """
    Setup Python path for the project.
    
    This function should be called at the beginning of any script
    that needs to import project modules.
    
    Returns:
        PythonPathManager: The configured path manager
    """
    return get_path_manager()


def safe_import_agents():
    """
    Safely import agents module with proper error handling.
    
    Returns:
        The agents module or None if import fails
    """
    path_manager = get_path_manager()
    return path_manager.safe_import('agents')


def safe_import_rag_tool():
    """
    Safely import RAG tool with proper error handling.
    
    Returns:
        The RAGTool class or None if import fails
    """
    path_manager = get_path_manager()
    rag_module = path_manager.safe_import('agents.tooling.rag.core')
    if rag_module:
        return getattr(rag_module, 'RAGTool', None)
    return None


def validate_project_imports() -> Dict[str, Any]:
    """
    Validate that all critical project imports are working.
    
    Returns:
        Dict containing validation results
    """
    path_manager = get_path_manager()
    
    # Check critical modules
    critical_status = path_manager.check_critical_modules()
    
    # Get path info
    path_info = path_manager.get_path_info()
    
    # Overall status
    all_critical_available = all(critical_status.values())
    
    return {
        'all_critical_available': all_critical_available,
        'critical_modules': critical_status,
        'path_info': path_info,
        'recommendations': _get_import_recommendations(critical_status)
    }


def _get_import_recommendations(critical_status: Dict[str, bool]) -> List[str]:
    """Get recommendations for fixing import issues"""
    recommendations = []
    
    if not critical_status.get('agents', False):
        recommendations.append("Add project root to PYTHONPATH environment variable")
        recommendations.append("Run scripts from project root directory")
        recommendations.append("Use setup_python_path() at the beginning of scripts")
    
    if not critical_status.get('agents.tooling.rag.core', False):
        recommendations.append("Check that agents/tooling/rag/core.py exists")
        recommendations.append("Verify file permissions and syntax")
    
    if not critical_status.get('db.services', False):
        recommendations.append("Check that db/services directory exists")
        recommendations.append("Verify database service modules are properly configured")
    
    return recommendations


# Convenience functions for common imports
def import_agents():
    """Import agents module with error handling"""
    return safe_import_agents()


def import_rag_tool():
    """Import RAG tool with error handling"""
    return safe_import_rag_tool()


def import_information_retrieval_agent():
    """Import Information Retrieval Agent with error handling"""
    path_manager = get_path_manager()
    return path_manager.safe_import('agents.patient_navigator.information_retrieval.agent')


# Context manager for temporary path setup
class PythonPathContext:
    """Context manager for temporary Python path setup"""
    
    def __init__(self, additional_paths: Optional[List[str]] = None):
        self.additional_paths = additional_paths or []
        self.original_path = None
    
    def __enter__(self):
        self.original_path = sys.path.copy()
        path_manager = get_path_manager()
        
        for path in self.additional_paths:
            path_manager.add_path(path)
        
        return path_manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_path:
            sys.path.clear()
            sys.path.extend(self.original_path)


if __name__ == "__main__":
    # Test the path manager
    path_manager = setup_python_path()
    
    print("Python Path Manager Test")
    print("=" * 50)
    
    # Show path info
    path_info = path_manager.get_path_info()
    print(f"Project Root: {path_info['project_root']}")
    print(f"Current Working Directory: {path_info['current_working_dir']}")
    print(f"Python Path Count: {path_info['python_path_count']}")
    
    # Check critical modules
    print("\nCritical Modules Status:")
    for module, available in path_info['critical_modules_status'].items():
        status = "✅" if available else "❌"
        print(f"  {status} {module}")
    
    # Validate imports
    print("\nImport Validation:")
    validation = validate_project_imports()
    if validation['all_critical_available']:
        print("✅ All critical modules are available")
    else:
        print("❌ Some critical modules are missing")
        print("\nRecommendations:")
        for rec in validation['recommendations']:
            print(f"  - {rec}")
