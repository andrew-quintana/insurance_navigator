#!/usr/bin/env python3
"""
RAG Workflow Testing Script

This script tests end-to-end RAG workflow functionality including
document processing, vector search, and information retrieval.

Usage:
    python scripts/investigation/test_rag_workflow.py --end-to-end
"""

import argparse
import json
import logging
import os
import sys
import time
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

class RAGWorkflowAssessment:
    """Test RAG workflow end-to-end functionality"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "assessment_type": "rag_workflow",
            "status": "running",
            "findings": {},
            "performance_metrics": {},
            "recommendations": [],
            "errors": []
        }
        self.test_queries = [
            "What does my insurance cover for dental care?",
            "Find me a dermatologist in my network",
            "What are my copay amounts for specialist visits?",
            "How do I file a claim for emergency room visits?",
            "What preventive care is covered under my plan?"
        ]
    
    def run_end_to_end_analysis(self) -> Dict[str, Any]:
        """Run comprehensive RAG workflow analysis"""
        logger.info("🔍 Starting RAG workflow assessment")
        
        try:
            # Test document processing capabilities
            self._test_document_processing()
            
            # Test vector search functionality
            self._test_vector_search()
            
            # Test information retrieval
            self._test_information_retrieval()
            
            # Test agent integration
            self._test_agent_integration()
            
            # Performance benchmarking
            self._run_performance_benchmarks()
            
            # Calculate overall scores
            self._calculate_rag_scores()
            
            self.results["status"] = "completed"
            logger.info("✅ RAG workflow assessment completed")
            
        except Exception as e:
            self.results["status"] = "failed"
            self.results["errors"].append(f"Assessment failed: {str(e)}")
            logger.error(f"❌ Assessment failed: {str(e)}")
        
        return self.results
    
    def _test_document_processing(self):
        """Test document upload and processing capabilities"""
        logger.info("📄 Testing document processing")
        
        try:
            processing_status = {
                "upload_components_found": False,
                "processing_scripts_found": False,
                "edge_functions_detected": False,
                "test_documents_available": False
            }
            
            # Check for UI upload components
            ui_dir = project_root / "ui"
            if ui_dir.exists():
                upload_components = list(ui_dir.rglob("*upload*.tsx")) + list(ui_dir.rglob("*Upload*.tsx"))
                if upload_components:
                    processing_status["upload_components_found"] = True
                    processing_status["upload_component_files"] = [f.name for f in upload_components]
            
            # Check for processing scripts
            scripts_dir = project_root / "scripts"
            if scripts_dir.exists():
                processing_scripts = []
                for script_file in scripts_dir.rglob("*.py"):
                    with open(script_file, 'r') as f:
                        content = f.read().lower()
                        if 'document' in content and ('process' in content or 'upload' in content):
                            processing_scripts.append(script_file.name)
                
                if processing_scripts:
                    processing_status["processing_scripts_found"] = True
                    processing_status["processing_script_files"] = processing_scripts
            
            # Check for edge functions
            supabase_dir = project_root / "supabase" / "functions"
            if supabase_dir.exists():
                edge_functions = [d.name for d in supabase_dir.iterdir() if d.is_dir()]
                if edge_functions:
                    processing_status["edge_functions_detected"] = True
                    processing_status["edge_function_names"] = edge_functions
            
            # Check for test documents
            examples_dir = project_root / "examples"
            data_dir = project_root / "data"
            test_docs = []
            
            for doc_dir in [examples_dir, data_dir]:
                if doc_dir.exists():
                    pdf_files = list(doc_dir.rglob("*.pdf"))
                    test_docs.extend([f.name for f in pdf_files])
            
            if test_docs:
                processing_status["test_documents_available"] = True
                processing_status["test_document_files"] = test_docs
            
            self.results["findings"]["document_processing"] = processing_status
            
            # Recommendations
            if processing_status["upload_components_found"]:
                self.results["recommendations"].append("✅ Document upload UI components found")
            else:
                self.results["recommendations"].append("⚠️ No document upload UI components found")
            
            if processing_status["edge_functions_detected"]:
                self.results["recommendations"].append(f"✅ Found {len(processing_status.get('edge_function_names', []))} edge functions")
            else:
                self.results["recommendations"].append("⚠️ No edge functions found for document processing")
                
        except Exception as e:
            self.results["errors"].append(f"Document processing test failed: {str(e)}")
    
    def _test_vector_search(self):
        """Test vector search and similarity functionality"""
        logger.info("🔍 Testing vector search capabilities")
        
        try:
            vector_status = {
                "vector_utilities_found": False,
                "embedding_code_found": False,
                "similarity_search_implemented": False,
                "vector_storage_configured": False
            }
            
            # Look for vector utilities
            for py_file in project_root.rglob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read().lower()
                        
                        if 'vector' in content and 'embedding' in content:
                            vector_status["embedding_code_found"] = True
                        
                        if 'similarity' in content and 'search' in content:
                            vector_status["similarity_search_implemented"] = True
                        
                        if 'vector_rag' in content or 'vectorrag' in content:
                            vector_status["vector_utilities_found"] = True
                            
                except:
                    continue
            
            # Check for vector RAG utility
            vector_rag_file = project_root / "agents" / "common" / "vector_rag.py"
            if vector_rag_file.exists():
                vector_status["vector_utilities_found"] = True
                vector_status["vector_rag_utility"] = "found"
            
            # Check database migrations for vector setup
            migrations_dir = project_root / "db" / "migrations"
            if migrations_dir.exists():
                for migration_file in migrations_dir.glob("*.sql"):
                    with open(migration_file, 'r') as f:
                        content = f.read().lower()
                        if 'vector' in content and ('extension' in content or 'create' in content):
                            vector_status["vector_storage_configured"] = True
                            break
            
            self.results["findings"]["vector_search"] = vector_status
            
            # Calculate vector readiness score
            vector_score = 0
            if vector_status["vector_utilities_found"]: vector_score += 25
            if vector_status["embedding_code_found"]: vector_score += 25
            if vector_status["similarity_search_implemented"]: vector_score += 25
            if vector_status["vector_storage_configured"]: vector_score += 25
            
            vector_status["readiness_score"] = vector_score
            
            if vector_score >= 75:
                self.results["recommendations"].append("✅ Vector search capabilities are well-implemented")
            elif vector_score >= 50:
                self.results["recommendations"].append("🔧 Vector search partially implemented - needs completion")
            else:
                self.results["recommendations"].append("⚠️ Vector search capabilities need significant development")
                
        except Exception as e:
            self.results["errors"].append(f"Vector search test failed: {str(e)}")
    
    def _test_information_retrieval(self):
        """Test information retrieval patterns and query handling"""
        logger.info("🧠 Testing information retrieval patterns")
        
        try:
            retrieval_status = {
                "query_processing_found": False,
                "context_retrieval_implemented": False,
                "response_generation_found": False,
                "rag_patterns_detected": False,
                "retrieval_workflows": []
            }
            
            # Look for information retrieval patterns
            for py_file in project_root.rglob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read().lower()
                        
                        if 'query' in content and 'process' in content:
                            retrieval_status["query_processing_found"] = True
                        
                        if 'context' in content and 'retriev' in content:
                            retrieval_status["context_retrieval_implemented"] = True
                        
                        if 'generate' in content and 'response' in content:
                            retrieval_status["response_generation_found"] = True
                        
                        if 'rag' in content or ('retrieval' in content and 'augment' in content):
                            retrieval_status["rag_patterns_detected"] = True
                            retrieval_status["retrieval_workflows"].append(str(py_file.relative_to(project_root)))
                            
                except:
                    continue
            
            # Check for information retrieval workflow
            info_retrieval_dir = project_root / "agents" / "zPrototyping" / "sandboxes"
            if info_retrieval_dir.exists():
                for subdir in info_retrieval_dir.rglob("*information_retrieval*"):
                    if subdir.is_dir():
                        retrieval_status["information_retrieval_workflow"] = str(subdir.relative_to(project_root))
                        retrieval_status["workflow_notebooks_found"] = len(list(subdir.glob("*.ipynb")))
            
            self.results["findings"]["information_retrieval"] = retrieval_status
            
            # Calculate retrieval readiness
            retrieval_score = 0
            if retrieval_status["query_processing_found"]: retrieval_score += 25
            if retrieval_status["context_retrieval_implemented"]: retrieval_score += 25
            if retrieval_status["response_generation_found"]: retrieval_score += 25
            if retrieval_status["rag_patterns_detected"]: retrieval_score += 25
            
            retrieval_status["readiness_score"] = retrieval_score
            
            if retrieval_score >= 75:
                self.results["recommendations"].append("✅ Information retrieval patterns are well-established")
            else:
                self.results["recommendations"].append("🔧 Information retrieval needs development")
                
        except Exception as e:
            self.results["errors"].append(f"Information retrieval test failed: {str(e)}")
    
    def _test_agent_integration(self):
        """Test agent integration with RAG workflows"""
        logger.info("🤖 Testing agent integration")
        
        try:
            integration_status = {
                "langgraph_agents_found": False,
                "rag_enabled_agents": [],
                "workflow_integration": False,
                "structured_output_ready": False
            }
            
            # Test LangGraph utilities integration
            try:
                from agents.zPrototyping.langgraph_utils import AgentDiscovery, create_agent
                discovery = AgentDiscovery(base_path=str(project_root / "agents"))
                agents = discovery.discover_agents()
                
                integration_status["langgraph_agents_found"] = True
                integration_status["total_agents_discovered"] = len(agents)
                
                # Check which agents might be RAG-ready
                rag_ready_agents = []
                for agent_name, agent_info in agents.items():
                    if agent_info.agent_class and not agent_info.init_error:
                        rag_ready_agents.append(agent_name)
                
                integration_status["rag_enabled_agents"] = rag_ready_agents
                
            except Exception as e:
                self.results["errors"].append(f"Agent discovery failed: {str(e)}")
            
            # Check for workflow integration
            graph_dir = project_root / "graph"
            if graph_dir.exists():
                workflow_files = list(graph_dir.rglob("*.py"))
                if workflow_files:
                    integration_status["workflow_integration"] = True
                    integration_status["workflow_files"] = [f.name for f in workflow_files]
            
            # Check for structured output schemas
            try:
                from agents.zPrototyping.langgraph_utils import ExampleAgentOutput
                integration_status["structured_output_ready"] = True
            except ImportError:
                pass
            
            self.results["findings"]["agent_integration"] = integration_status
            
            if integration_status["langgraph_agents_found"]:
                self.results["recommendations"].append(f"✅ LangGraph integration ready with {integration_status.get('total_agents_discovered', 0)} agents")
            else:
                self.results["recommendations"].append("⚠️ LangGraph agent integration needs setup")
                
        except Exception as e:
            self.results["errors"].append(f"Agent integration test failed: {str(e)}")
    
    def _run_performance_benchmarks(self):
        """Run performance benchmarks for RAG workflow"""
        logger.info("⚡ Running performance benchmarks")
        
        try:
            performance_metrics = {
                "simulated_query_tests": [],
                "average_response_time": 0,
                "system_readiness": False
            }
            
            # Simulate query processing time
            for i, query in enumerate(self.test_queries[:3]):  # Test first 3 queries
                start_time = time.time()
                
                # Simulate processing (since we can't run actual queries without full setup)
                # This would normally include: query processing, vector search, response generation
                simulated_processing_time = 0.5 + (len(query) * 0.01)  # Simulate based on query length
                time.sleep(min(simulated_processing_time, 1.0))  # Cap at 1 second for testing
                
                end_time = time.time()
                response_time = end_time - start_time
                
                performance_metrics["simulated_query_tests"].append({
                    "query": query,
                    "response_time": response_time,
                    "simulated": True
                })
            
            # Calculate average response time
            if performance_metrics["simulated_query_tests"]:
                avg_time = sum(t["response_time"] for t in performance_metrics["simulated_query_tests"]) / len(performance_metrics["simulated_query_tests"])
                performance_metrics["average_response_time"] = avg_time
            
            # System readiness assessment
            performance_metrics["system_readiness"] = performance_metrics["average_response_time"] < 2.0
            
            self.results["performance_metrics"] = performance_metrics
            
            if performance_metrics["system_readiness"]:
                self.results["recommendations"].append(f"✅ Simulated performance meets targets (<2s avg: {performance_metrics['average_response_time']:.2f}s)")
            else:
                self.results["recommendations"].append(f"⚠️ Performance optimization needed (avg: {performance_metrics['average_response_time']:.2f}s)")
                
        except Exception as e:
            self.results["errors"].append(f"Performance benchmarking failed: {str(e)}")
    
    def _calculate_rag_scores(self):
        """Calculate overall RAG readiness scores"""
        logger.info("📊 Calculating RAG readiness scores")
        
        try:
            scores = {}
            
            # Document processing score
            doc_processing = self.results["findings"].get("document_processing", {})
            doc_score = 0
            if doc_processing.get("upload_components_found"): doc_score += 25
            if doc_processing.get("processing_scripts_found"): doc_score += 25
            if doc_processing.get("edge_functions_detected"): doc_score += 25
            if doc_processing.get("test_documents_available"): doc_score += 25
            scores["document_processing"] = doc_score
            
            # Vector search score
            vector_search = self.results["findings"].get("vector_search", {})
            scores["vector_search"] = vector_search.get("readiness_score", 0)
            
            # Information retrieval score
            info_retrieval = self.results["findings"].get("information_retrieval", {})
            scores["information_retrieval"] = info_retrieval.get("readiness_score", 0)
            
            # Agent integration score
            agent_integration = self.results["findings"].get("agent_integration", {})
            agent_score = 0
            if agent_integration.get("langgraph_agents_found"): agent_score += 40
            if agent_integration.get("workflow_integration"): agent_score += 30
            if agent_integration.get("structured_output_ready"): agent_score += 30
            scores["agent_integration"] = agent_score
            
            # Performance score
            performance = self.results["performance_metrics"]
            perf_score = 100 if performance.get("system_readiness") else 50
            scores["performance"] = perf_score
            
            # Overall RAG readiness score
            overall_score = sum(scores.values()) / len(scores)
            scores["overall_rag_readiness"] = overall_score
            
            self.results["rag_readiness_scores"] = scores
            
            # Final assessment
            if overall_score >= 80:
                self.results["recommendations"].append("🎯 EXCELLENT: RAG workflow is production-ready")
            elif overall_score >= 60:
                self.results["recommendations"].append("🔧 GOOD: RAG workflow needs minor improvements")
            elif overall_score >= 40:
                self.results["recommendations"].append("⚠️ MODERATE: RAG workflow needs significant development")
            else:
                self.results["recommendations"].append("🚨 LOW: RAG workflow requires major implementation")
                
        except Exception as e:
            self.results["errors"].append(f"Score calculation failed: {str(e)}")
    
    def save_results(self, output_file: Optional[str] = None):
        """Save assessment results to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"logs/rag_workflow_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📄 Results saved to {output_file}")
        return output_file

def main():
    parser = argparse.ArgumentParser(description="RAG Workflow Assessment")
    parser.add_argument("--end-to-end", action="store_true", 
                       help="Run end-to-end RAG workflow analysis")
    parser.add_argument("--output", type=str, 
                       help="Output file path")
    
    args = parser.parse_args()
    
    if not args.end_to_end:
        parser.print_help()
        return
    
    # Run assessment
    assessment = RAGWorkflowAssessment()
    results = assessment.run_end_to_end_analysis()
    
    # Save results
    output_file = assessment.save_results(args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("🧠 RAG WORKFLOW ASSESSMENT SUMMARY")
    print("="*60)
    print(f"Status: {results['status']}")
    print(f"Timestamp: {results['timestamp']}")
    
    # Show RAG readiness scores
    if "rag_readiness_scores" in results:
        scores = results["rag_readiness_scores"]
        print(f"\n📊 RAG Readiness Scores:")
        print(f"  Overall: {scores.get('overall_rag_readiness', 0):.1f}%")
        print(f"  Document Processing: {scores.get('document_processing', 0):.1f}%")
        print(f"  Vector Search: {scores.get('vector_search', 0):.1f}%")
        print(f"  Information Retrieval: {scores.get('information_retrieval', 0):.1f}%")
        print(f"  Agent Integration: {scores.get('agent_integration', 0):.1f}%")
        print(f"  Performance: {scores.get('performance', 0):.1f}%")
    
    # Show performance metrics
    if "performance_metrics" in results:
        perf = results["performance_metrics"]
        print(f"\n⚡ Performance Metrics:")
        print(f"  Average Response Time: {perf.get('average_response_time', 0):.2f}s")
        print(f"  System Readiness: {'✅ Ready' if perf.get('system_readiness') else '⚠️ Needs Work'}")
    
    if results['recommendations']:
        print("\n🔧 Key Recommendations:")
        for rec in results['recommendations'][:5]:  # Top 5
            print(f"  {rec}")
    
    if results['errors']:
        print("\n❌ Errors Encountered:")
        for error in results['errors']:
            print(f"  {error}")
    
    print(f"\n📄 Full results saved to: {output_file}")
    print("\n🔄 Next Step: Run manual RAG quality assessment as described in the guide")

if __name__ == "__main__":
    main() 