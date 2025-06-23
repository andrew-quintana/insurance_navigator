#!/usr/bin/env python3
"""
LangGraph Compatibility Assessment Script

This script tests the compatibility of existing agents with LangGraph patterns
and assesses readiness for RAG tooling integration.

Usage:
    python scripts/investigation/test_langgraph_compatibility.py --agent-discovery
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LangGraphCompatibilityAssessment:
    """Assess LangGraph compatibility and RAG readiness"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "assessment_type": "langgraph_compatibility",
            "status": "running",
            "findings": {},
            "compatibility_scores": {},
            "recommendations": [],
            "errors": []
        }
    
    def run_agent_discovery_analysis(self) -> Dict[str, Any]:
        """Run agent discovery and compatibility analysis"""
        logger.info("🔍 Starting LangGraph compatibility assessment")
        
        try:
            # Test LangGraph utilities
            self._test_langgraph_utilities()
            
            # Discover existing agents
            self._discover_agents()
            
            # Test agent compatibility
            self._test_agent_compatibility()
            
            # Check schema readiness
            self._check_schema_readiness()
            
            # Assess workflow patterns
            self._assess_workflow_patterns()
            
            # Calculate overall compatibility score
            self._calculate_compatibility_scores()
            
            self.results["status"] = "completed"
            logger.info("✅ LangGraph compatibility assessment completed")
            
        except Exception as e:
            self.results["status"] = "failed"
            self.results["errors"].append(f"Assessment failed: {str(e)}")
            logger.error(f"❌ Assessment failed: {str(e)}")
        
        return self.results
    
    def _test_langgraph_utilities(self):
        """Test LangGraph utilities availability and functionality"""
        logger.info("🧰 Testing LangGraph utilities")
        
        try:
            # Test LangGraph imports
            langgraph_available = False
            try:
                from langgraph.graph import StateGraph, END
                from langgraph.graph.message import add_messages
                langgraph_available = True
            except ImportError as e:
                self.results["errors"].append(f"LangGraph import failed: {str(e)}")
            
            # Test our utilities
            utilities_available = False
            utilities_features = {}
            try:
                from agents.zPrototyping.langgraph_utils import (
                    AgentDiscovery, 
                    create_agent,
                    WorkflowBuilder,
                    StructuredValidator
                )
                utilities_available = True
                utilities_features = {
                    "agent_discovery": True,
                    "unified_agent_creation": True,
                    "workflow_builder": True,
                    "structured_validation": True
                }
            except ImportError as e:
                self.results["errors"].append(f"LangGraph utilities import failed: {str(e)}")
                utilities_features = {
                    "agent_discovery": False,
                    "unified_agent_creation": False,
                    "workflow_builder": False,
                    "structured_validation": False
                }
            
            utilities_status = {
                "langgraph_core_available": langgraph_available,
                "custom_utilities_available": utilities_available,
                "features": utilities_features
            }
            
            self.results["findings"]["utilities"] = utilities_status
            
            if langgraph_available and utilities_available:
                self.results["recommendations"].append("✅ LangGraph and custom utilities are available")
            else:
                self.results["recommendations"].append("⚠️ LangGraph dependencies missing - install requirements")
                
        except Exception as e:
            self.results["errors"].append(f"Utilities test failed: {str(e)}")
    
    def _discover_agents(self):
        """Discover and catalog existing agents"""
        logger.info("🔍 Discovering existing agents")
        
        try:
            agents_dir = project_root / "agents"
            discovered_agents = {}
            
            if agents_dir.exists():
                for agent_dir in agents_dir.iterdir():
                    if agent_dir.is_dir() and not agent_dir.name.startswith('.'):
                        agent_info = self._analyze_agent_directory(agent_dir)
                        if agent_info:
                            discovered_agents[agent_dir.name] = agent_info
            
            # Test agent discovery utility
            discovery_utility_works = False
            utility_agent_count = 0
            try:
                from agents.zPrototyping.langgraph_utils import AgentDiscovery
                discovery = AgentDiscovery(base_path=str(agents_dir))
                discovered_by_utility = discovery.discover_agents()
                discovery_utility_works = True
                utility_agent_count = len(discovered_by_utility)
                
            except Exception as e:
                self.results["errors"].append(f"Agent discovery utility failed: {str(e)}")
            
            discovery_results = {
                "manual_discovery_count": len(discovered_agents),
                "utility_discovery_count": utility_agent_count,
                "discovery_utility_works": discovery_utility_works,
                "agents_found": list(discovered_agents.keys()),
                "agent_details": discovered_agents
            }
            
            self.results["findings"]["agent_discovery"] = discovery_results
            
            if discovery_results["manual_discovery_count"] > 0:
                self.results["recommendations"].append(f"✅ Found {discovery_results['manual_discovery_count']} agent directories")
            else:
                self.results["recommendations"].append("⚠️ No agent directories found")
                
        except Exception as e:
            self.results["errors"].append(f"Agent discovery failed: {str(e)}")
    
    def _analyze_agent_directory(self, agent_dir: Path) -> Optional[Dict[str, Any]]:
        """Analyze individual agent directory structure"""
        try:
            agent_info = {
                "has_main_file": False,
                "has_prompts": False,
                "has_examples": False,
                "has_models": False,
                "has_tests": False,
                "file_count": 0,
                "structure_score": 0
            }
            
            # Check for main agent file
            main_files = list(agent_dir.glob("*.py"))
            if main_files:
                agent_info["has_main_file"] = True
                agent_info["main_files"] = [f.name for f in main_files]
            
            # Check for prompts directory
            prompts_dir = agent_dir / "prompts"
            if prompts_dir.exists():
                agent_info["has_prompts"] = True
                prompt_files = list(prompts_dir.rglob("*.md")) + list(prompts_dir.rglob("*.txt"))
                agent_info["prompt_files"] = [f.name for f in prompt_files]
            
            # Check for examples
            examples_dir = agent_dir / "examples"
            if examples_dir.exists():
                agent_info["has_examples"] = True
                example_files = list(examples_dir.rglob("*.json")) + list(examples_dir.rglob("*.md"))
                agent_info["example_files"] = [f.name for f in example_files]
            
            # Check for models
            models_dir = agent_dir / "models"
            if models_dir.exists():
                agent_info["has_models"] = True
                model_files = list(models_dir.glob("*.py"))
                agent_info["model_files"] = [f.name for f in model_files]
            
            # Check for tests
            tests_dir = agent_dir / "tests"
            if tests_dir.exists():
                agent_info["has_tests"] = True
                test_files = list(tests_dir.glob("*.py"))
                agent_info["test_files"] = [f.name for f in test_files]
            
            # Calculate structure score
            score = 0
            if agent_info["has_main_file"]: score += 30
            if agent_info["has_prompts"]: score += 25
            if agent_info["has_examples"]: score += 20
            if agent_info["has_models"]: score += 15
            if agent_info["has_tests"]: score += 10
            
            agent_info["structure_score"] = score
            agent_info["file_count"] = len(list(agent_dir.rglob("*.py")))
            
            return agent_info
            
        except Exception as e:
            logger.warning(f"Failed to analyze agent directory {agent_dir.name}: {str(e)}")
            return None
    
    def _test_agent_compatibility(self):
        """Test existing agents for LangGraph compatibility"""
        logger.info("🔧 Testing agent LangGraph compatibility")
        
        try:
            compatibility_results = {}
            
            # Test agent loading with our utilities
            try:
                from agents.zPrototyping.langgraph_utils import AgentDiscovery
                discovery = AgentDiscovery(base_path=str(project_root / "agents"))
                agents = discovery.discover_agents()
                
                for agent_name, agent_info in agents.items():
                    compat_score = self._calculate_agent_compatibility(agent_info)
                    compatibility_results[agent_name] = compat_score
                    
            except Exception as e:
                self.results["errors"].append(f"Agent compatibility testing failed: {str(e)}")
            
            self.results["findings"]["agent_compatibility"] = compatibility_results
            
            # Calculate average compatibility
            if compatibility_results:
                avg_compatibility = sum(r["score"] for r in compatibility_results.values()) / len(compatibility_results)
                self.results["recommendations"].append(f"📊 Average agent compatibility: {avg_compatibility:.1f}%")
            
        except Exception as e:
            self.results["errors"].append(f"Agent compatibility test failed: {str(e)}")
    
    def _calculate_agent_compatibility(self, agent_info) -> Dict[str, Any]:
        """Calculate compatibility score for individual agent"""
        score = 0
        issues = []
        strengths = []
        
        # Check if agent class exists
        if agent_info.agent_class:
            score += 40
            strengths.append("Has agent class")
        else:
            issues.append("Missing agent class")
        
        # Check if factory function exists
        if agent_info.factory_function:
            score += 20
            strengths.append("Has factory function")
        else:
            issues.append("Missing factory function")
        
        # Check for initialization errors
        if agent_info.init_error:
            score -= 30
            issues.append(f"Initialization error: {agent_info.init_error[:50]}...")
        else:
            score += 20
            strengths.append("No initialization errors")
        
        # Check description availability
        if agent_info.description:
            score += 10
            strengths.append("Has description")
        
        # Ensure score is between 0-100
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "issues": issues,
            "strengths": strengths,
            "langgraph_ready": score >= 70
        }
    
    def _check_schema_readiness(self):
        """Check for Pydantic schemas and structured output readiness"""
        logger.info("📋 Checking schema readiness")
        
        try:
            schema_analysis = {
                "pydantic_models_found": 0,
                "schema_files": [],
                "example_schemas_available": False,
                "validation_patterns": []
            }
            
            # Look for Pydantic models
            for py_file in project_root.rglob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        if 'BaseModel' in content and 'pydantic' in content:
                            schema_analysis["pydantic_models_found"] += 1
                            schema_analysis["schema_files"].append(str(py_file.relative_to(project_root)))
                except:
                    continue
            
            # Check for example schemas in utilities
            try:
                from agents.zPrototyping.langgraph_utils import ExampleAgentOutput, ChainOfThoughtOutput
                schema_analysis["example_schemas_available"] = True
                schema_analysis["available_schemas"] = ["ExampleAgentOutput", "ChainOfThoughtOutput"]
            except ImportError:
                schema_analysis["example_schemas_available"] = False
            
            self.results["findings"]["schema_readiness"] = schema_analysis
            
            if schema_analysis["pydantic_models_found"] > 0:
                self.results["recommendations"].append(f"✅ Found {schema_analysis['pydantic_models_found']} Pydantic models")
            else:
                self.results["recommendations"].append("⚠️ No Pydantic models found - create schemas for structured output")
                
        except Exception as e:
            self.results["errors"].append(f"Schema readiness check failed: {str(e)}")
    
    def _assess_workflow_patterns(self):
        """Assess workflow construction readiness"""
        logger.info("🕸️ Assessing workflow patterns")
        
        try:
            workflow_assessment = {
                "workflow_builder_available": False,
                "state_schemas_defined": False,
                "existing_workflows": [],
                "graph_files_found": 0
            }
            
            # Test workflow builder availability
            try:
                from agents.zPrototyping.langgraph_utils import WorkflowBuilder, WorkflowState
                workflow_assessment["workflow_builder_available"] = True
                workflow_assessment["state_schemas_defined"] = True
            except ImportError:
                pass
            
            # Look for existing workflow/graph files
            for py_file in project_root.rglob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        if 'StateGraph' in content or 'workflow' in content.lower():
                            workflow_assessment["graph_files_found"] += 1
                            workflow_assessment["existing_workflows"].append(str(py_file.relative_to(project_root)))
                except:
                    continue
            
            # Check graph directory
            graph_dir = project_root / "graph"
            if graph_dir.exists():
                workflow_assessment["graph_directory_exists"] = True
                graph_files = list(graph_dir.rglob("*.py"))
                workflow_assessment["graph_directory_files"] = len(graph_files)
            
            self.results["findings"]["workflow_patterns"] = workflow_assessment
            
            if workflow_assessment["workflow_builder_available"]:
                self.results["recommendations"].append("✅ Workflow builder utilities available")
            else:
                self.results["recommendations"].append("⚠️ Workflow builder not available - check LangGraph utilities")
                
        except Exception as e:
            self.results["errors"].append(f"Workflow assessment failed: {str(e)}")
    
    def _calculate_compatibility_scores(self):
        """Calculate overall compatibility scores"""
        logger.info("📊 Calculating compatibility scores")
        
        try:
            scores = {}
            
            # Utilities score
            utilities = self.results["findings"].get("utilities", {})
            utilities_score = 0
            if utilities.get("langgraph_core_available"): utilities_score += 50
            if utilities.get("custom_utilities_available"): utilities_score += 50
            scores["utilities"] = utilities_score
            
            # Agent discovery score
            discovery = self.results["findings"].get("agent_discovery", {})
            discovery_score = 0
            if discovery.get("manual_discovery_count", 0) > 0: discovery_score += 40
            if discovery.get("discovery_utility_works"): discovery_score += 40
            if discovery.get("manual_discovery_count", 0) >= 5: discovery_score += 20
            scores["agent_discovery"] = discovery_score
            
            # Schema readiness score
            schemas = self.results["findings"].get("schema_readiness", {})
            schema_score = 0
            if schemas.get("pydantic_models_found", 0) > 0: schema_score += 60
            if schemas.get("example_schemas_available"): schema_score += 40
            scores["schema_readiness"] = schema_score
            
            # Workflow patterns score
            workflows = self.results["findings"].get("workflow_patterns", {})
            workflow_score = 0
            if workflows.get("workflow_builder_available"): workflow_score += 50
            if workflows.get("state_schemas_defined"): workflow_score += 30
            if workflows.get("graph_files_found", 0) > 0: workflow_score += 20
            scores["workflow_patterns"] = workflow_score
            
            # Overall score
            overall_score = sum(scores.values()) / len(scores)
            scores["overall"] = overall_score
            
            self.results["compatibility_scores"] = scores
            
            # Add readiness assessment
            if overall_score >= 80:
                self.results["recommendations"].append("🎯 EXCELLENT: System is ready for LangGraph integration")
            elif overall_score >= 60:
                self.results["recommendations"].append("🔧 GOOD: System needs minor modifications for LangGraph")
            elif overall_score >= 40:
                self.results["recommendations"].append("⚠️ MODERATE: System needs significant work for LangGraph")
            else:
                self.results["recommendations"].append("🚨 LOW: System requires major restructuring for LangGraph")
                
        except Exception as e:
            self.results["errors"].append(f"Score calculation failed: {str(e)}")
    
    def save_results(self, output_file: Optional[str] = None):
        """Save assessment results to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"logs/langgraph_compatibility_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📄 Results saved to {output_file}")
        return output_file

def main():
    parser = argparse.ArgumentParser(description="LangGraph Compatibility Assessment")
    parser.add_argument("--agent-discovery", action="store_true", 
                       help="Run agent discovery and compatibility analysis")
    parser.add_argument("--output", type=str, 
                       help="Output file path")
    
    args = parser.parse_args()
    
    if not args.agent_discovery:
        parser.print_help()
        return
    
    # Run assessment
    assessment = LangGraphCompatibilityAssessment()
    results = assessment.run_agent_discovery_analysis()
    
    # Save results
    output_file = assessment.save_results(args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("🧠 LANGGRAPH COMPATIBILITY ASSESSMENT SUMMARY")
    print("="*60)
    print(f"Status: {results['status']}")
    print(f"Timestamp: {results['timestamp']}")
    
    # Show compatibility scores
    if "compatibility_scores" in results:
        scores = results["compatibility_scores"]
        print(f"\n📊 Compatibility Scores:")
        print(f"  Overall: {scores.get('overall', 0):.1f}%")
        print(f"  Utilities: {scores.get('utilities', 0):.1f}%")
        print(f"  Agent Discovery: {scores.get('agent_discovery', 0):.1f}%")
        print(f"  Schema Readiness: {scores.get('schema_readiness', 0):.1f}%")
        print(f"  Workflow Patterns: {scores.get('workflow_patterns', 0):.1f}%")
    
    if results['recommendations']:
        print("\n🔧 Key Recommendations:")
        for rec in results['recommendations'][:5]:  # Top 5
            print(f"  {rec}")
    
    if results['errors']:
        print("\n❌ Errors Encountered:")
        for error in results['errors']:
            print(f"  {error}")
    
    print(f"\n📄 Full results saved to: {output_file}")
    print("\n🔄 Next Step: Run manual agent architecture review as described in the guide")

if __name__ == "__main__":
    main() 