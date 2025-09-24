#!/usr/bin/env python3
"""
Phase 2 Comprehensive Component Testing Report
Generate a comprehensive report based on actual project structure and capabilities
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("phase2_report")

class Phase2ComprehensiveReport:
    """Generate comprehensive Phase 2 component testing report."""
    
    def __init__(self):
        self.start_time = datetime.now()
        
    def analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze the actual project structure."""
        analysis = {
            "backend_structure": self._analyze_backend_structure(),
            "frontend_structure": self._analyze_frontend_structure(),
            "database_structure": self._analyze_database_structure(),
            "deployment_structure": self._analyze_deployment_structure(),
            "testing_structure": self._analyze_testing_structure()
        }
        return analysis
    
    def _analyze_backend_structure(self) -> Dict[str, Any]:
        """Analyze backend structure."""
        backend_analysis = {
            "fastapi_app": {
                "main_py_exists": os.path.exists("main.py"),
                "main_py_importable": self._test_import("main"),
                "fastapi_app_defined": self._check_fastapi_app()
            },
            "core_modules": {
                "database": os.path.exists("core/database.py"),
                "service_manager": os.path.exists("core/service_manager.py"),
                "agent_integration": os.path.exists("core/agent_integration.py")
            },
            "backend_services": {
                "auth": os.path.exists("backend/shared/auth.py"),
                "workers": os.path.exists("backend/workers"),
                "integration": os.path.exists("backend/integration")
            },
            "requirements": {
                "main_requirements": os.path.exists("requirements.txt"),
                "api_requirements": os.path.exists("requirements-api.txt"),
                "worker_requirements": os.path.exists("requirements-worker.txt"),
                "testing_requirements": os.path.exists("requirements-testing.txt")
            }
        }
        return backend_analysis
    
    def _analyze_frontend_structure(self) -> Dict[str, Any]:
        """Analyze frontend structure."""
        frontend_analysis = {
            "ui_structure": {
                "ui_directory": os.path.exists("ui"),
                "ui_files": len([f for f in os.listdir("ui") if f.endswith(('.tsx', '.ts', '.js', '.jsx'))]) if os.path.exists("ui") else 0
            },
            "package_management": {
                "package_json": os.path.exists("package.json"),
                "package_lock": os.path.exists("package-lock.json"),
                "node_modules": os.path.exists("node_modules")
            },
            "vercel_config": {
                "vercel_json": os.path.exists("vercel.json"),
                "vercelignore": os.path.exists(".vercelignore"),
                "vercel_directory": os.path.exists(".vercel")
            },
            "nextjs_config": {
                "next_config": os.path.exists("next.config.js") or os.path.exists("next.config.ts"),
                "app_directory": os.path.exists("app") or os.path.exists("pages"),
                "components_directory": os.path.exists("components") or os.path.exists("ui/components")
            }
        }
        return frontend_analysis
    
    def _analyze_database_structure(self) -> Dict[str, Any]:
        """Analyze database structure."""
        db_analysis = {
            "supabase_config": {
                "config_toml": os.path.exists("supabase/config.toml"),
                "migrations": os.path.exists("supabase/migrations"),
                "seed_sql": os.path.exists("supabase/seed.sql"),
                "production_config": os.path.exists("supabase/production.config.json")
            },
            "database_modules": {
                "core_database": os.path.exists("core/database.py"),
                "db_config": os.path.exists("db/config.py"),
                "db_services": os.path.exists("db/services")
            },
            "environment_configs": {
                "env_development": os.path.exists(".env.development"),
                "env_staging": os.path.exists(".env.staging"),
                "env_production": os.path.exists(".env.production"),
                "env_local": os.path.exists(".env.local")
            }
        }
        return db_analysis
    
    def _analyze_deployment_structure(self) -> Dict[str, Any]:
        """Analyze deployment structure."""
        deployment_analysis = {
            "render_configs": {
                "render_yaml": os.path.exists("render.yaml"),
                "upload_pipeline": os.path.exists("render-upload-pipeline.yaml"),
                "worker_pipeline": os.path.exists("render-upload-pipeline-worker.yaml")
            },
            "docker_configs": {
                "dockerfile": os.path.exists("Dockerfile"),
                "docker_compose": os.path.exists("docker-compose.yml"),
                "docker_directory": os.path.exists("docker")
            },
            "vercel_configs": {
                "vercel_json": os.path.exists("vercel.json"),
                "vercelignore": os.path.exists(".vercelignore")
            }
        }
        return deployment_analysis
    
    def _analyze_testing_structure(self) -> Dict[str, Any]:
        """Analyze testing structure."""
        testing_analysis = {
            "test_directories": {
                "tests_directory": os.path.exists("tests"),
                "unit_tests": os.path.exists("tests/unit"),
                "integration_tests": os.path.exists("tests/integration")
            },
            "test_configs": {
                "pytest_ini": os.path.exists("pytest.ini"),
                "jest_config": os.path.exists("jest.config.js"),
                "test_requirements": os.path.exists("requirements-testing.txt")
            },
            "test_scripts": {
                "test_runners": len([f for f in os.listdir(".") if f.startswith("test_") and f.endswith(".py")]),
                "component_tests": len([f for f in os.listdir(".") if "test" in f and f.endswith(".py")])
            }
        }
        return testing_analysis
    
    def _test_import(self, module_name: str) -> bool:
        """Test if a module can be imported."""
        try:
            __import__(module_name)
            return True
        except:
            return False
    
    def _check_fastapi_app(self) -> bool:
        """Check if FastAPI app is defined in main.py."""
        try:
            import main
            return hasattr(main, 'app')
        except:
            return False
    
    def generate_component_testing_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on project structure analysis."""
        recommendations = []
        
        # Backend recommendations
        if not analysis["backend_structure"]["fastapi_app"]["main_py_importable"]:
            recommendations.append("Fix main.py import issues to enable FastAPI testing")
        
        if not analysis["backend_structure"]["requirements"]["main_requirements"]:
            recommendations.append("Create requirements.txt for backend dependencies")
        
        # Frontend recommendations
        if not analysis["frontend_structure"]["package_management"]["package_json"]:
            recommendations.append("Create package.json for frontend dependencies and scripts")
        
        if not analysis["frontend_structure"]["vercel_config"]["vercel_json"]:
            recommendations.append("Create vercel.json for Vercel deployment configuration")
        
        if analysis["frontend_structure"]["ui_structure"]["ui_files"] == 0:
            recommendations.append("Add React/Next.js components to ui directory")
        
        # Database recommendations
        if not analysis["database_structure"]["supabase_config"]["config_toml"]:
            recommendations.append("Initialize Supabase configuration with supabase init")
        
        if not analysis["database_structure"]["environment_configs"]["env_development"]:
            recommendations.append("Create .env.development file with development database settings")
        
        # Deployment recommendations
        if not analysis["deployment_structure"]["render_configs"]["render_yaml"]:
            recommendations.append("Create render.yaml for Render deployment configuration")
        
        if not analysis["deployment_structure"]["docker_configs"]["dockerfile"]:
            recommendations.append("Create Dockerfile for containerized deployment")
        
        # Testing recommendations
        if not analysis["testing_structure"]["test_directories"]["tests_directory"]:
            recommendations.append("Create tests directory structure for organized testing")
        
        if not analysis["testing_structure"]["test_configs"]["pytest_ini"]:
            recommendations.append("Create pytest.ini for Python testing configuration")
        
        return recommendations
    
    def generate_phase2_testing_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a realistic Phase 2 testing plan based on actual project structure."""
        testing_plan = {
            "immediate_tests": [],
            "infrastructure_required": [],
            "mock_testing_approach": [],
            "deployment_validation": []
        }
        
        # Immediate tests that can be run
        if analysis["backend_structure"]["fastapi_app"]["main_py_importable"]:
            testing_plan["immediate_tests"].extend([
                "FastAPI application import and basic structure validation",
                "Core module import testing",
                "Database connection configuration testing",
                "Authentication module structure validation"
            ])
        
        if analysis["frontend_structure"]["ui_structure"]["ui_directory"]:
            testing_plan["immediate_tests"].extend([
                "UI component structure validation",
                "Frontend build process testing (if package.json exists)",
                "Vercel configuration validation"
            ])
        
        # Infrastructure required for full testing
        testing_plan["infrastructure_required"].extend([
            "Local development environment setup with proper dependencies",
            "Database connection configuration and test data",
            "External API mock services for testing",
            "Vercel CLI setup for frontend testing",
            "Render deployment configuration for backend testing"
        ])
        
        # Mock testing approach
        testing_plan["mock_testing_approach"].extend([
            "Mock external API calls for database and AI services",
            "Simulate Render and Vercel environments locally",
            "Use test databases for database integration testing",
            "Mock authentication flows for security testing"
        ])
        
        # Deployment validation
        testing_plan["deployment_validation"].extend([
            "Validate Render configuration files",
            "Validate Vercel configuration files",
            "Test Docker container builds",
            "Validate environment variable configurations"
        ])
        
        return testing_plan
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate the comprehensive Phase 2 report."""
        analysis = self.analyze_project_structure()
        recommendations = self.generate_component_testing_recommendations(analysis)
        testing_plan = self.generate_phase2_testing_plan(analysis)
        
        # Calculate overall readiness score
        total_checks = sum(len(category) for category in analysis.values() if isinstance(category, dict))
        passed_checks = sum(
            sum(1 for check in category.values() if check is True) 
            for category in analysis.values() 
            if isinstance(category, dict)
        )
        readiness_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        comprehensive_report = {
            "phase": "Phase 2 - Component Testing Analysis",
            "timestamp": datetime.now().isoformat(),
            "project_analysis": analysis,
            "readiness_assessment": {
                "overall_score": readiness_score,
                "backend_readiness": self._calculate_category_score(analysis["backend_structure"]),
                "frontend_readiness": self._calculate_category_score(analysis["frontend_structure"]),
                "database_readiness": self._calculate_category_score(analysis["database_structure"]),
                "deployment_readiness": self._calculate_category_score(analysis["deployment_structure"]),
                "testing_readiness": self._calculate_category_score(analysis["testing_structure"])
            },
            "recommendations": recommendations,
            "testing_plan": testing_plan,
            "success_criteria_validation": {
                "project_structure_complete": readiness_score >= 70,
                "backend_components_ready": self._calculate_category_score(analysis["backend_structure"]) >= 60,
                "frontend_components_ready": self._calculate_category_score(analysis["frontend_structure"]) >= 40,
                "database_integration_ready": self._calculate_category_score(analysis["database_structure"]) >= 60,
                "deployment_configs_ready": self._calculate_category_score(analysis["deployment_structure"]) >= 50,
                "testing_framework_ready": self._calculate_category_score(analysis["testing_structure"]) >= 50
            },
            "next_steps": [
                "Address critical infrastructure gaps identified in recommendations",
                "Set up proper development environment with all dependencies",
                "Create missing configuration files for deployment platforms",
                "Implement mock testing approach for components that can't be fully tested",
                "Proceed with incremental component testing as infrastructure becomes available"
            ]
        }
        
        return comprehensive_report
    
    def _calculate_category_score(self, category: Dict[str, Any]) -> float:
        """Calculate readiness score for a category."""
        if not isinstance(category, dict):
            return 0.0
        
        total_checks = 0
        passed_checks = 0
        
        for item in category.values():
            if isinstance(item, dict):
                for check in item.values():
                    if isinstance(check, bool):
                        total_checks += 1
                        if check:
                            passed_checks += 1
            elif isinstance(item, bool):
                total_checks += 1
                if item:
                    passed_checks += 1
            elif isinstance(item, int):
                total_checks += 1
                if item > 0:
                    passed_checks += 1
        
        return (passed_checks / total_checks * 100) if total_checks > 0 else 0.0
    
    def save_report(self, report: Dict[str, Any]) -> str:
        """Save the comprehensive report to file."""
        os.makedirs("test-results", exist_ok=True)
        report_path = "test-results/phase2_comprehensive_analysis_report.json"
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        return report_path
    
    def print_report_summary(self, report: Dict[str, Any]):
        """Print a summary of the comprehensive report."""
        print("=" * 80)
        print("PHASE 2 COMPONENT TESTING - COMPREHENSIVE ANALYSIS")
        print("=" * 80)
        print(f"Analysis Time: {report['timestamp']}")
        print(f"Overall Readiness Score: {report['readiness_assessment']['overall_score']:.1f}%")
        print("=" * 80)
        
        print("\n📊 COMPONENT READINESS BREAKDOWN:")
        for component, score in report['readiness_assessment'].items():
            if component != 'overall_score':
                print(f"  {component.replace('_', ' ').title()}: {score:.1f}%")
        
        print("\n✅ SUCCESS CRITERIA VALIDATION:")
        for criterion, passed in report['success_criteria_validation'].items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} {criterion.replace('_', ' ').title()}")
        
        print(f"\n💡 RECOMMENDATIONS ({len(report['recommendations'])} items):")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print(f"\n🎯 TESTING PLAN:")
        print(f"  Immediate Tests: {len(report['testing_plan']['immediate_tests'])} items")
        print(f"  Infrastructure Required: {len(report['testing_plan']['infrastructure_required'])} items")
        print(f"  Mock Testing Approach: {len(report['testing_plan']['mock_testing_approach'])} items")
        print(f"  Deployment Validation: {len(report['testing_plan']['deployment_validation'])} items")
        
        print(f"\n🚀 NEXT STEPS:")
        for i, step in enumerate(report['next_steps'], 1):
            print(f"  {i}. {step}")
        
        print("\n" + "=" * 80)
        if report['readiness_assessment']['overall_score'] >= 70:
            print("🎉 PROJECT IS READY FOR PHASE 2 COMPONENT TESTING")
        else:
            print("⚠️ PROJECT NEEDS INFRASTRUCTURE IMPROVEMENTS BEFORE PHASE 2")
        print("=" * 80)

async def main():
    """Main execution function."""
    print("=" * 80)
    print("PHASE 2 COMPONENT TESTING - COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    print(f"Project Root: {project_root}")
    print(f"Start Time: {datetime.now().isoformat()}")
    print("=" * 80)
    
    reporter = Phase2ComprehensiveReport()
    report = reporter.generate_comprehensive_report()
    report_path = reporter.save_report(report)
    reporter.print_report_summary(report)
    
    print(f"\n📄 Comprehensive analysis report saved to: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
