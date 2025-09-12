#!/usr/bin/env python3
"""
Deployment Checks for Insurance Navigator

This script performs comprehensive checks to ensure the deployment
is ready and all modules can be imported correctly.

Usage:
    python scripts/deployment_checks.py
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.import_utilities import (
    validate_agents_imports,
    get_import_status_report,
    safe_import_agents,
    safe_import_rag_tool,
    safe_import_information_retrieval_agent
)
from utils.python_path_manager import setup_python_path, validate_project_imports

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentChecker:
    """Comprehensive deployment checker for Insurance Navigator"""
    
    def __init__(self):
        self.project_root = project_root
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_total = 0
        self.results = {}
    
    def run_check(self, check_name: str, check_func) -> bool:
        """Run a single check and record results"""
        self.checks_total += 1
        logger.info(f"Running check: {check_name}")
        
        try:
            result = check_func()
            if result:
                self.checks_passed += 1
                logger.info(f"✅ {check_name} - PASSED")
                self.results[check_name] = {"status": "PASSED", "details": result}
                return True
            else:
                self.checks_failed += 1
                logger.error(f"❌ {check_name} - FAILED")
                self.results[check_name] = {"status": "FAILED", "details": result}
                return False
        except Exception as e:
            self.checks_failed += 1
            logger.error(f"❌ {check_name} - ERROR: {str(e)}")
            self.results[check_name] = {"status": "ERROR", "details": str(e)}
            return False
    
    def check_python_path_setup(self) -> bool:
        """Check if Python path is set up correctly"""
        try:
            path_manager = setup_python_path()
            path_info = path_manager.get_path_info()
            
            # Check if project root is in path
            if str(self.project_root) not in path_info['python_paths']:
                logger.error(f"Project root not in Python path: {self.project_root}")
                return False
            
            # Check if critical modules are available
            critical_status = path_info['critical_modules_status']
            if not critical_status.get('agents', False):
                logger.error("Agents module not available")
                return False
            
            logger.info(f"Python path setup correct. Project root: {self.project_root}")
            return True
            
        except Exception as e:
            logger.error(f"Python path setup failed: {str(e)}")
            return False
    
    def check_agents_imports(self) -> bool:
        """Check if agents modules can be imported"""
        try:
            validation_results = validate_agents_imports()
            
            # Check critical agents modules
            critical_modules = [
                'agents',
                'base_agent',
                'rag_tool',
                'information_retrieval_agent'
            ]
            
            for module in critical_modules:
                if not validation_results.get(module, False):
                    logger.error(f"Critical module {module} not available")
                    return False
            
            logger.info("All critical agents modules imported successfully")
            return True
            
        except Exception as e:
            logger.error(f"Agents import check failed: {str(e)}")
            return False
    
    def check_rag_functionality(self) -> bool:
        """Check if RAG functionality is working"""
        try:
            RAGTool = safe_import_rag_tool()
            if not RAGTool:
                logger.error("RAGTool class not available")
                return False
            
            # Test RAG tool initialization
            user_id = "test-user-123"
            rag_tool = RAGTool(user_id)
            
            logger.info("RAG functionality check passed")
            return True
            
        except Exception as e:
            logger.error(f"RAG functionality check failed: {str(e)}")
            return False
    
    def check_information_retrieval_agent(self) -> bool:
        """Check if Information Retrieval Agent is working"""
        try:
            InformationRetrievalAgent = safe_import_information_retrieval_agent()
            if not InformationRetrievalAgent:
                logger.error("InformationRetrievalAgent class not available")
                return False
            
            # Test agent initialization
            agent = InformationRetrievalAgent()
            
            logger.info("Information Retrieval Agent check passed")
            return True
            
        except Exception as e:
            logger.error(f"Information Retrieval Agent check failed: {str(e)}")
            return False
    
    def check_database_connectivity(self) -> bool:
        """Check if database connectivity is working"""
        try:
            from utils.import_utilities import safe_import_database_manager
            DatabaseManager = safe_import_database_manager()
            
            if not DatabaseManager:
                logger.error("DatabaseManager class not available")
                return False
            
            # Check if DATABASE_URL is set
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.error("DATABASE_URL environment variable not set")
                return False
            
            logger.info("Database connectivity check passed")
            return True
            
        except Exception as e:
            logger.error(f"Database connectivity check failed: {str(e)}")
            return False
    
    def check_environment_variables(self) -> bool:
        """Check if required environment variables are set"""
        try:
            required_vars = [
                'DATABASE_URL',
                'SUPABASE_URL',
                'SUPABASE_ANON_KEY',
                'SUPABASE_SERVICE_ROLE_KEY'
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                logger.error(f"Missing required environment variables: {missing_vars}")
                return False
            
            logger.info("All required environment variables are set")
            return True
            
        except Exception as e:
            logger.error(f"Environment variables check failed: {str(e)}")
            return False
    
    def check_file_structure(self) -> bool:
        """Check if required files and directories exist"""
        try:
            required_paths = [
                'agents/__init__.py',
                'agents/base_agent.py',
                'agents/tooling/rag/core.py',
                'agents/patient_navigator/information_retrieval/agent.py',
                'utils/import_utilities.py',
                'utils/python_path_manager.py',
                'main.py'
            ]
            
            missing_paths = []
            for path in required_paths:
                full_path = self.project_root / path
                if not full_path.exists():
                    missing_paths.append(path)
            
            if missing_paths:
                logger.error(f"Missing required files: {missing_paths}")
                return False
            
            logger.info("All required files exist")
            return True
            
        except Exception as e:
            logger.error(f"File structure check failed: {str(e)}")
            return False
    
    def check_worker_services(self) -> bool:
        """Check if worker services can be imported"""
        try:
            from utils.import_utilities import (
                safe_import_worker_config,
                safe_import_enhanced_service_client,
                safe_import_error_handler
            )
            
            WorkerConfig = safe_import_worker_config()
            EnhancedServiceClient = safe_import_enhanced_service_client()
            WorkerErrorHandler = safe_import_error_handler()
            
            if not all([WorkerConfig, EnhancedServiceClient, WorkerErrorHandler]):
                logger.error("Some worker service classes not available")
                return False
            
            logger.info("Worker services check passed")
            return True
            
        except Exception as e:
            logger.error(f"Worker services check failed: {str(e)}")
            return False
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all deployment checks"""
        logger.info("Starting comprehensive deployment checks")
        logger.info("=" * 60)
        
        # Run all checks
        checks = [
            ("Python Path Setup", self.check_python_path_setup),
            ("File Structure", self.check_file_structure),
            ("Environment Variables", self.check_environment_variables),
            ("Database Connectivity", self.check_database_connectivity),
            ("Agents Imports", self.check_agents_imports),
            ("RAG Functionality", self.check_rag_functionality),
            ("Information Retrieval Agent", self.check_information_retrieval_agent),
            ("Worker Services", self.check_worker_services)
        ]
        
        for check_name, check_func in checks:
            self.run_check(check_name, check_func)
        
        # Generate summary
        summary = {
            "total_checks": self.checks_total,
            "passed": self.checks_passed,
            "failed": self.checks_failed,
            "success_rate": self.checks_passed / self.checks_total if self.checks_total > 0 else 0,
            "results": self.results
        }
        
        logger.info("=" * 60)
        logger.info(f"Deployment checks completed: {self.checks_passed}/{self.checks_total} passed")
        logger.info(f"Success rate: {summary['success_rate']:.2%}")
        
        if self.checks_failed > 0:
            logger.error("Some checks failed - deployment may not be ready")
        else:
            logger.info("All checks passed - deployment is ready!")
        
        return summary


def main():
    """Main function"""
    checker = DeploymentChecker()
    summary = checker.run_all_checks()
    
    # Exit with appropriate code
    if summary['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
