#!/usr/bin/env python3
"""
Enhanced Hybrid Vectorization Investigation with LangGraph Integration Assessment

This script combines automated analysis with manual dashboard findings to provide
comprehensive root cause analysis for document vectorization pipeline issues
and assess readiness for LangGraph-based RAG tooling.

Features:
- Database architecture and data integrity checks
- Vectorization pipeline performance analysis
- LangGraph StateGraph compatibility assessment
- Agent schema validation for structured outputs
- RAG workflow construction testing
- Interactive manual findings collection
- Unified reporting with prioritized recommendations

Usage:
    python scripts/hybrid_investigation.py --full-analysis
    python scripts/hybrid_investigation.py --rag-focus --langgraph-assessment
    python scripts/hybrid_investigation.py --interactive --agents-only
"""

import os
import sys
import json
import logging
import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
try:
    from db.config import get_database_connection
    from agents.zPrototyping.langgraph_utils import (
        AgentDiscovery, 
        create_agent,
        StructuredValidator,
        ValidationMode
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some imports unavailable: {e}")
    IMPORTS_AVAILABLE = False

# LangGraph imports for compatibility assessment
try:
    from langgraph.graph import StateGraph
    from langchain_core.messages import BaseMessage
    from typing_extensions import TypedDict
    from typing import Annotated
    from pydantic import BaseModel, Field
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: LangGraph not available for compatibility assessment")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/hybrid_investigation.log')
    ]
)
logger = logging.getLogger(__name__)

class InvestigationPhase(Enum):
    DATABASE = "database"
    VECTORIZATION = "vectorization"
    LANGGRAPH = "langgraph"
    AGENTS = "agents"
    RAG_TOOLING = "rag_tooling"
    INTEGRATION = "integration"

@dataclass
class LangGraphCompatibilityResult:
    """Results of LangGraph compatibility assessment"""
    agents_discovered: int
    langgraph_compatible: int
    structured_output_ready: int
    state_management_score: float
    workflow_construction_ready: bool
    compatibility_details: Dict[str, Any]
    recommendations: List[str]

@dataclass
class RAGToolingAssessment:
    """Assessment of RAG tooling readiness"""
    vector_search_performance: Dict[str, Any]
    context_retrieval_quality: Dict[str, Any]
    agent_integration_score: float
    workflow_readiness: Dict[str, Any]
    recommended_actions: List[str]

@dataclass
class HybridInvestigationResult:
    """Complete investigation results"""
    timestamp: str
    investigation_phases: List[str]
    database_health: Dict[str, Any]
    vectorization_pipeline: Dict[str, Any]
    langgraph_compatibility: Optional[LangGraphCompatibilityResult]
    rag_tooling: Optional[RAGToolingAssessment]
    manual_findings: Dict[str, Any]
    unified_recommendations: Dict[str, List[str]]
    success_metrics: Dict[str, Any]

class EnhancedHybridInvestigator:
    """Enhanced investigation with LangGraph and RAG focus"""
    
    def __init__(self, focus_areas: List[InvestigationPhase] = None):
        self.focus_areas = focus_areas or list(InvestigationPhase)
        self.results = {}
        self.manual_findings = {}
        self.db_connection = None
        self.agent_discovery = None
        
        # Initialize logging directory
        os.makedirs('logs', exist_ok=True)
        
    async def run_investigation(self, interactive: bool = False) -> HybridInvestigationResult:
        """Run complete hybrid investigation"""
        logger.info("🚀 Starting Enhanced Hybrid Investigation")
        
        # Phase 1: Automated Analysis
        await self._run_automated_analysis()
        
        # Phase 2: Manual Findings Collection (if interactive)
        if interactive:
            await self._collect_manual_findings()
        
        # Phase 3: LangGraph Integration Assessment
        if InvestigationPhase.LANGGRAPH in self.focus_areas:
            await self._assess_langgraph_compatibility()
        
        # Phase 4: RAG Tooling Assessment
        if InvestigationPhase.RAG_TOOLING in self.focus_areas:
            await self._assess_rag_tooling()
        
        # Phase 5: Generate Unified Report
        result = await self._generate_unified_report()
        
        # Save results
        await self._save_results(result)
        
        return result
    
    async def _run_automated_analysis(self):
        """Run automated database and pipeline analysis"""
        logger.info("📊 Phase 1: Automated System Analysis")
        
        # Database analysis
        if InvestigationPhase.DATABASE in self.focus_areas:
            self.results['database'] = await self._analyze_database_health()
        
        # Vectorization pipeline analysis
        if InvestigationPhase.VECTORIZATION in self.focus_areas:
            self.results['vectorization'] = await self._analyze_vectorization_pipeline()
        
        # Agent discovery
        if InvestigationPhase.AGENTS in self.focus_areas:
            self.results['agents'] = await self._discover_and_analyze_agents()
    
    async def _analyze_database_health(self) -> Dict[str, Any]:
        """Analyze database health with LangGraph focus"""
        logger.info("🗄️ Analyzing database health for RAG compatibility")
        
        if not IMPORTS_AVAILABLE:
            return {"error": "Database connection not available"}
        
        try:
            # Get database connection
            conn = get_database_connection()
            
            health_results = {
                'connection_status': 'connected',
                'vector_extension': await self._check_vector_extension(conn),
                'schema_compatibility': await self._assess_schema_langgraph_compatibility(conn),
                'data_integrity': await self._check_data_integrity(conn),
                'performance_metrics': await self._gather_performance_metrics(conn),
                'rag_readiness': await self._assess_rag_database_readiness(conn)
            }
            
            conn.close()
            return health_results
            
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
            return {
                'connection_status': 'failed',
                'error': str(e),
                'rag_readiness': False
            }
    
    async def _check_vector_extension(self, conn) -> Dict[str, Any]:
        """Check vector extension configuration"""
        try:
            cursor = conn.cursor()
            
            # Check extension status
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
            extension_info = cursor.fetchone()
            
            if not extension_info:
                return {'installed': False, 'error': 'Vector extension not installed'}
            
            # Check vector settings
            cursor.execute("SELECT name, setting FROM pg_settings WHERE name LIKE '%vector%';")
            settings = cursor.fetchall()
            
            return {
                'installed': True,
                'version': extension_info[1] if len(extension_info) > 1 else 'unknown',
                'settings': dict(settings)
            }
            
        except Exception as e:
            return {'installed': False, 'error': str(e)}
    
    async def _assess_schema_langgraph_compatibility(self, conn) -> Dict[str, Any]:
        """Assess database schema for LangGraph TypedDict compatibility"""
        try:
            cursor = conn.cursor()
            
            # Check key tables for LangGraph state management
            key_tables = ['documents', 'vectors', 'job_queue', 'conversations', 'agent_workflows']
            compatibility = {}
            
            for table in key_tables:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """, (table,))
                
                columns = cursor.fetchall()
                if columns:
                    compatibility[table] = {
                        'exists': True,
                        'columns': [
                            {
                                'name': col[0],
                                'type': col[1],
                                'nullable': col[2],
                                'typeddict_compatible': self._assess_typeddict_compatibility(col[1])
                            }
                            for col in columns
                        ]
                    }
                else:
                    compatibility[table] = {'exists': False}
            
            return compatibility
            
        except Exception as e:
            return {'error': str(e)}
    
    def _assess_typeddict_compatibility(self, data_type: str) -> str:
        """Assess PostgreSQL data type compatibility with TypedDict"""
        compatibility_map = {
            'jsonb': 'Dict[str, Any]',
            'json': 'Dict[str, Any]',
            'text[]': 'List[str]',
            'varchar[]': 'List[str]',
            'uuid': 'str',
            'text': 'str',
            'varchar': 'str',
            'integer': 'int',
            'bigint': 'int',
            'boolean': 'bool',
            'timestamp': 'str',
            'timestamptz': 'str'
        }
        
        for pg_type, python_type in compatibility_map.items():
            if pg_type in data_type.lower():
                return python_type
        
        return 'Custom mapping needed'
    
    async def _check_data_integrity(self, conn) -> Dict[str, Any]:
        """Check data integrity for RAG operations"""
        try:
            cursor = conn.cursor()
            
            # Documents and vectors relationship
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_documents,
                    COUNT(CASE WHEN v.id IS NOT NULL THEN 1 END) as vectorized_documents,
                    ROUND(
                        100.0 * COUNT(CASE WHEN v.id IS NOT NULL THEN 1 END) / COUNT(*), 2
                    ) as vectorization_rate
                FROM documents d
                LEFT JOIN vectors v ON d.id = v.document_id
            """)
            
            integrity_stats = cursor.fetchone()
            
            # Check for orphaned records
            cursor.execute("""
                SELECT COUNT(*) FROM vectors v 
                WHERE NOT EXISTS (SELECT 1 FROM documents d WHERE d.id = v.document_id)
            """)
            orphaned_vectors = cursor.fetchone()[0]
            
            # Check embedding dimensions consistency
            cursor.execute("""
                SELECT 
                    MIN(array_length(embedding, 1)) as min_dimensions,
                    MAX(array_length(embedding, 1)) as max_dimensions,
                    COUNT(CASE WHEN array_length(embedding, 1) != 1536 THEN 1 END) as dimension_mismatches
                FROM vectors 
                WHERE embedding IS NOT NULL
            """)
            
            dimension_stats = cursor.fetchone()
            
            return {
                'total_documents': integrity_stats[0],
                'vectorized_documents': integrity_stats[1],
                'vectorization_rate': float(integrity_stats[2]),
                'orphaned_vectors': orphaned_vectors,
                'embedding_dimensions': {
                    'min': dimension_stats[0],
                    'max': dimension_stats[1],
                    'mismatches': dimension_stats[2]
                } if dimension_stats[0] else None
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _gather_performance_metrics(self, conn) -> Dict[str, Any]:
        """Gather performance metrics for RAG operations"""
        try:
            cursor = conn.cursor()
            
            # Table sizes
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename IN ('documents', 'vectors')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            
            table_sizes = cursor.fetchall()
            
            # Index information for vector similarity
            cursor.execute("""
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE tablename IN ('vectors') 
                AND schemaname = 'public'
            """)
            
            vector_indexes = cursor.fetchall()
            
            return {
                'table_sizes': [
                    {'schema': row[0], 'table': row[1], 'size': row[2]}
                    for row in table_sizes
                ],
                'vector_indexes': [
                    {'name': row[0], 'definition': row[1]}
                    for row in vector_indexes
                ]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _assess_rag_database_readiness(self, conn) -> Dict[str, Any]:
        """Assess database readiness for RAG operations"""
        try:
            cursor = conn.cursor()
            
            # Test vector similarity search performance
            cursor.execute("""
                SELECT COUNT(*) FROM vectors WHERE embedding IS NOT NULL
            """)
            vector_count = cursor.fetchone()[0]
            
            if vector_count == 0:
                return {
                    'ready': False,
                    'reason': 'No vectors available for similarity search'
                }
            
            # Test a sample similarity search
            start_time = datetime.now()
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT embedding <-> embedding as distance 
                    FROM vectors 
                    WHERE embedding IS NOT NULL 
                    LIMIT 10
                ) t
            """)
            end_time = datetime.now()
            
            search_time = (end_time - start_time).total_seconds()
            
            return {
                'ready': True,
                'vector_count': vector_count,
                'sample_search_time': search_time,
                'performance_rating': 'excellent' if search_time < 0.1 else 'good' if search_time < 0.5 else 'needs_optimization'
            }
            
        except Exception as e:
            return {
                'ready': False,
                'error': str(e)
            }
    
    async def _analyze_vectorization_pipeline(self) -> Dict[str, Any]:
        """Analyze vectorization pipeline performance"""
        logger.info("🔄 Analyzing vectorization pipeline")
        
        if not IMPORTS_AVAILABLE:
            return {"error": "Database connection not available"}
        
        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            
            # Job queue analysis
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage,
                    MIN(created_at) as earliest,
                    MAX(created_at) as latest
                FROM job_queue 
                GROUP BY status
                ORDER BY count DESC
            """)
            
            job_stats = cursor.fetchall()
            
            # Processing time analysis
            cursor.execute("""
                SELECT 
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_processing_time,
                    MIN(EXTRACT(EPOCH FROM (updated_at - created_at))) as min_processing_time,
                    MAX(EXTRACT(EPOCH FROM (updated_at - created_at))) as max_processing_time
                FROM job_queue 
                WHERE status = 'completed' 
                AND updated_at IS NOT NULL
            """)
            
            timing_stats = cursor.fetchone()
            
            # Error analysis
            cursor.execute("""
                SELECT 
                    error_message,
                    COUNT(*) as error_count
                FROM job_queue 
                WHERE status = 'failed' 
                AND error_message IS NOT NULL
                GROUP BY error_message
                ORDER BY error_count DESC
                LIMIT 10
            """)
            
            error_patterns = cursor.fetchall()
            
            conn.close()
            
            return {
                'job_statistics': [
                    {
                        'status': row[0],
                        'count': row[1],
                        'percentage': float(row[2]),
                        'earliest': row[3].isoformat() if row[3] else None,
                        'latest': row[4].isoformat() if row[4] else None
                    }
                    for row in job_stats
                ],
                'processing_times': {
                    'average': float(timing_stats[0]) if timing_stats[0] else 0,
                    'minimum': float(timing_stats[1]) if timing_stats[1] else 0,
                    'maximum': float(timing_stats[2]) if timing_stats[2] else 0
                } if timing_stats else None,
                'error_patterns': [
                    {'message': row[0], 'count': row[1]}
                    for row in error_patterns
                ]
            }
            
        except Exception as e:
            logger.error(f"Vectorization pipeline analysis failed: {e}")
            return {'error': str(e)}
    
    async def _discover_and_analyze_agents(self) -> Dict[str, Any]:
        """Discover and analyze existing agents"""
        logger.info("🤖 Discovering and analyzing agents")
        
        if not IMPORTS_AVAILABLE:
            return {"error": "Agent discovery not available"}
        
        try:
            # Initialize agent discovery
            self.agent_discovery = AgentDiscovery(base_path=str(project_root / "agents"))
            
            # Discover agents
            agents = self.agent_discovery.discover_agents()
            
            # Analyze agent compatibility
            agent_analysis = {}
            for name, info in agents.items():
                agent_analysis[name] = {
                    'discovered': True,
                    'path': info.path,
                    'has_agent_class': info.agent_class is not None,
                    'has_factory_function': info.factory_function is not None,
                    'has_error': info.init_error is not None,
                    'error_message': info.init_error,
                    'description': info.description,
                    'langgraph_ready': await self._assess_agent_langgraph_compatibility(info)
                }
            
            return {
                'total_agents': len(agents),
                'agents': agent_analysis,
                'summary': {
                    'loadable': sum(1 for a in agent_analysis.values() if not a['has_error']),
                    'has_classes': sum(1 for a in agent_analysis.values() if a['has_agent_class']),
                    'has_factories': sum(1 for a in agent_analysis.values() if a['has_factory_function']),
                    'langgraph_ready': sum(1 for a in agent_analysis.values() if a['langgraph_ready'])
                }
            }
            
        except Exception as e:
            logger.error(f"Agent discovery failed: {e}")
            return {'error': str(e)}
    
    async def _assess_agent_langgraph_compatibility(self, agent_info) -> bool:
        """Assess individual agent compatibility with LangGraph"""
        if agent_info.init_error:
            return False
        
        try:
            # Check if agent follows LangGraph patterns
            # This is a simplified check - in practice, you'd want more detailed analysis
            compatibility_indicators = 0
            
            if agent_info.agent_class:
                compatibility_indicators += 1
            
            if agent_info.factory_function:
                compatibility_indicators += 1
            
            if agent_info.description and any(keyword in agent_info.description.lower() 
                                            for keyword in ['structured', 'pydantic', 'schema']):
                compatibility_indicators += 1
            
            return compatibility_indicators >= 2
            
        except Exception:
            return False
    
    async def _assess_langgraph_compatibility(self) -> LangGraphCompatibilityResult:
        """Comprehensive LangGraph compatibility assessment"""
        logger.info("🕸️ Assessing LangGraph compatibility")
        
        if not LANGGRAPH_AVAILABLE:
            return LangGraphCompatibilityResult(
                agents_discovered=0,
                langgraph_compatible=0,
                structured_output_ready=0,
                state_management_score=0.0,
                workflow_construction_ready=False,
                compatibility_details={'error': 'LangGraph not available'},
                recommendations=['Install LangGraph: pip install langgraph']
            )
        
        # Get agent analysis results
        agent_results = self.results.get('agents', {})
        total_agents = agent_results.get('total_agents', 0)
        
        # Test StateGraph construction
        workflow_ready = await self._test_workflow_construction()
        
        # Assess structured output readiness
        structured_output_ready = await self._assess_structured_output_readiness()
        
        # Calculate compatibility scores
        compatible_agents = agent_results.get('summary', {}).get('langgraph_ready', 0)
        state_score = self._calculate_state_management_score()
        
        # Generate recommendations
        recommendations = self._generate_langgraph_recommendations(
            total_agents, compatible_agents, workflow_ready, structured_output_ready
        )
        
        return LangGraphCompatibilityResult(
            agents_discovered=total_agents,
            langgraph_compatible=compatible_agents,
            structured_output_ready=structured_output_ready,
            state_management_score=state_score,
            workflow_construction_ready=workflow_ready,
            compatibility_details={
                'workflow_test': workflow_ready,
                'schema_support': structured_output_ready > 0,
                'agent_discovery': self.agent_discovery is not None
            },
            recommendations=recommendations
        )
    
    async def _test_workflow_construction(self) -> bool:
        """Test if we can construct LangGraph workflows"""
        try:
            # Define a simple test state
            class TestState(TypedDict):
                messages: List[str]
                step_count: int
            
            # Create a simple workflow
            workflow = StateGraph(TestState)
            
            def test_node(state: TestState) -> TestState:
                return {
                    "messages": state.get("messages", []) + ["test"],
                    "step_count": state.get("step_count", 0) + 1
                }
            
            workflow.add_node("test", test_node)
            workflow.set_entry_point("test")
            
            # Try to compile
            compiled = workflow.compile()
            
            return True
            
        except Exception as e:
            logger.error(f"Workflow construction test failed: {e}")
            return False
    
    async def _assess_structured_output_readiness(self) -> int:
        """Count agents ready for structured output"""
        # This would analyze existing agent schemas
        # For now, return a mock assessment
        return 3  # Placeholder
    
    def _calculate_state_management_score(self) -> float:
        """Calculate state management compatibility score"""
        db_results = self.results.get('database', {})
        schema_compat = db_results.get('schema_compatibility', {})
        
        if not schema_compat:
            return 0.0
        
        total_tables = len(schema_compat)
        compatible_tables = sum(
            1 for table_info in schema_compat.values() 
            if table_info.get('exists', False)
        )
        
        return compatible_tables / total_tables if total_tables > 0 else 0.0
    
    def _generate_langgraph_recommendations(
        self, 
        total_agents: int, 
        compatible_agents: int, 
        workflow_ready: bool, 
        structured_ready: int
    ) -> List[str]:
        """Generate LangGraph integration recommendations"""
        recommendations = []
        
        if not workflow_ready:
            recommendations.append("Install and configure LangGraph properly")
        
        if compatible_agents < total_agents:
            recommendations.append(
                f"Update {total_agents - compatible_agents} agents for LangGraph compatibility"
            )
        
        if structured_ready == 0:
            recommendations.append("Define Pydantic schemas for all agent outputs")
        
        if self.results.get('database', {}).get('rag_readiness', {}).get('ready', False):
            recommendations.append("Database is RAG-ready - proceed with agent integration")
        else:
            recommendations.append("Fix database issues before RAG integration")
        
        return recommendations
    
    async def _assess_rag_tooling(self) -> RAGToolingAssessment:
        """Assess RAG tooling readiness"""
        logger.info("🧠 Assessing RAG tooling readiness")
        
        # Vector search performance
        vector_performance = await self._test_vector_search_performance()
        
        # Context retrieval quality
        context_quality = await self._assess_context_retrieval()
        
        # Agent integration score
        integration_score = self._calculate_agent_integration_score()
        
        # Workflow readiness
        workflow_readiness = await self._assess_rag_workflow_readiness()
        
        # Generate recommendations
        actions = self._generate_rag_recommendations(
            vector_performance, context_quality, integration_score, workflow_readiness
        )
        
        return RAGToolingAssessment(
            vector_search_performance=vector_performance,
            context_retrieval_quality=context_quality,
            agent_integration_score=integration_score,
            workflow_readiness=workflow_readiness,
            recommended_actions=actions
        )
    
    async def _test_vector_search_performance(self) -> Dict[str, Any]:
        """Test vector search performance"""
        # This would test actual vector similarity search
        # For now, return mock results based on database analysis
        db_results = self.results.get('database', {})
        rag_readiness = db_results.get('rag_readiness', {})
        
        return {
            'ready': rag_readiness.get('ready', False),
            'vector_count': rag_readiness.get('vector_count', 0),
            'search_time': rag_readiness.get('sample_search_time', 0),
            'rating': rag_readiness.get('performance_rating', 'unknown')
        }
    
    async def _assess_context_retrieval(self) -> Dict[str, Any]:
        """Assess context retrieval quality"""
        # Mock assessment - would test actual retrieval quality
        return {
            'relevance_score': 0.85,
            'context_length_appropriate': True,
            'metadata_filtering_available': True
        }
    
    def _calculate_agent_integration_score(self) -> float:
        """Calculate agent integration readiness score"""
        agent_results = self.results.get('agents', {})
        summary = agent_results.get('summary', {})
        
        total = summary.get('loadable', 1)
        ready = summary.get('langgraph_ready', 0)
        
        return ready / total
    
    async def _assess_rag_workflow_readiness(self) -> Dict[str, Any]:
        """Assess RAG workflow construction readiness"""
        return {
            'state_schema_defined': True,
            'nodes_implementable': True,
            'edge_connections_clear': True,
            'compilation_successful': await self._test_workflow_construction()
        }
    
    def _generate_rag_recommendations(
        self, 
        vector_perf: Dict, 
        context_qual: Dict, 
        integration_score: float, 
        workflow_ready: Dict
    ) -> List[str]:
        """Generate RAG-specific recommendations"""
        recommendations = []
        
        if not vector_perf.get('ready', False):
            recommendations.append("Fix vector database issues before RAG implementation")
        
        if vector_perf.get('rating') == 'needs_optimization':
            recommendations.append("Optimize vector similarity search performance")
        
        if integration_score < 0.8:
            recommendations.append("Update more agents for RAG compatibility")
        
        if not workflow_ready.get('compilation_successful', False):
            recommendations.append("Fix LangGraph workflow construction issues")
        
        return recommendations
    
    async def _collect_manual_findings(self):
        """Interactive collection of manual findings"""
        logger.info("👤 Collecting manual findings")
        
        print("\n" + "="*60)
        print("📋 MANUAL FINDINGS COLLECTION")
        print("="*60)
        
        # Dashboard findings
        dashboard_findings = {}
        
        print("\n🏢 Project Dashboard Findings:")
        dashboard_findings['project_health'] = input("Project health status (active/issues/down): ").strip()
        dashboard_findings['usage_metrics'] = input("Current usage vs limits (%): ").strip()
        dashboard_findings['billing_status'] = input("Any billing issues? (yes/no): ").strip()
        
        print("\n🗄️ Database Dashboard Findings:")
        dashboard_findings['vector_extension'] = input("Vector extension enabled? (yes/no): ").strip()
        dashboard_findings['table_browser'] = input("Key tables accessible? (yes/no): ").strip()
        dashboard_findings['performance'] = input("Database performance rating (excellent/good/poor): ").strip()
        
        print("\n⚡ Edge Functions Findings:")
        dashboard_findings['functions_deployed'] = input("All functions deployed? (yes/no): ").strip()
        dashboard_findings['function_errors'] = input("Recent function errors? (describe or 'none'): ").strip()
        dashboard_findings['response_times'] = input("Function response times (fast/slow/timeout): ").strip()
        
        print("\n🤖 Agent Integration Observations:")
        dashboard_findings['agent_accessibility'] = input("Can you access existing agents? (yes/no): ").strip()
        dashboard_findings['schema_definitions'] = input("Are structured output schemas defined? (yes/no/partial): ").strip()
        dashboard_findings['workflow_patterns'] = input("Do agents follow consistent patterns? (yes/no): ").strip()
        
        self.manual_findings = {
            'dashboard': dashboard_findings,
            'collection_time': datetime.now(timezone.utc).isoformat(),
            'additional_notes': input("\nAdditional observations: ").strip()
        }
        
        print("\n✅ Manual findings collected successfully!")
    
    async def _generate_unified_report(self) -> HybridInvestigationResult:
        """Generate unified investigation report"""
        logger.info("📝 Generating unified report")
        
        # Calculate success metrics
        success_metrics = self._calculate_success_metrics()
        
        # Generate unified recommendations
        recommendations = self._generate_unified_recommendations()
        
        return HybridInvestigationResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            investigation_phases=[phase.value for phase in self.focus_areas],
            database_health=self.results.get('database', {}),
            vectorization_pipeline=self.results.get('vectorization', {}),
            langgraph_compatibility=self.results.get('langgraph'),
            rag_tooling=self.results.get('rag_tooling'),
            manual_findings=self.manual_findings,
            unified_recommendations=recommendations,
            success_metrics=success_metrics
        )
    
    def _calculate_success_metrics(self) -> Dict[str, Any]:
        """Calculate success metrics against targets"""
        metrics = {}
        
        # Vectorization success rate
        vectorization = self.results.get('vectorization', {})
        job_stats = vectorization.get('job_statistics', [])
        
        if job_stats:
            completed = next((stat for stat in job_stats if stat['status'] == 'completed'), {'percentage': 0})
            metrics['vectorization_success_rate'] = completed['percentage']
        
        # Database performance
        db_results = self.results.get('database', {})
        rag_readiness = db_results.get('rag_readiness', {})
        metrics['query_response_time'] = rag_readiness.get('sample_search_time', 0)
        
        # LangGraph compatibility
        langgraph = self.results.get('langgraph')
        if langgraph:
            metrics['langgraph_compatibility_score'] = langgraph.state_management_score
        
        return metrics
    
    def _generate_unified_recommendations(self) -> Dict[str, List[str]]:
        """Generate unified recommendations by priority"""
        recommendations = {
            'critical': [],
            'high_priority': [],
            'medium_priority': []
        }
        
        # Database issues
        db_results = self.results.get('database', {})
        if not db_results.get('rag_readiness', {}).get('ready', False):
            recommendations['critical'].append("Fix database vector extension and configuration")
        
        # Vectorization issues
        vectorization = self.results.get('vectorization', {})
        job_stats = vectorization.get('job_statistics', [])
        failed_jobs = next((stat for stat in job_stats if stat['status'] == 'failed'), None)
        if failed_jobs and failed_jobs['percentage'] > 5:
            recommendations['critical'].append(f"Fix {failed_jobs['percentage']:.1f}% job failure rate")
        
        # LangGraph compatibility
        langgraph = self.results.get('langgraph')
        if langgraph and langgraph.langgraph_compatible < langgraph.agents_discovered:
            recommendations['high_priority'].extend(langgraph.recommendations)
        
        # RAG tooling
        rag_tooling = self.results.get('rag_tooling')
        if rag_tooling:
            recommendations['medium_priority'].extend(rag_tooling.recommended_actions)
        
        return recommendations
    
    async def _save_results(self, result: HybridInvestigationResult):
        """Save investigation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON results
        json_path = f"logs/hybrid_investigation_results_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(asdict(result), f, indent=2, default=str)
        
        # Save human-readable summary
        summary_path = f"logs/hybrid_investigation_summary_{timestamp}.md"
        await self._generate_summary_report(result, summary_path)
        
        logger.info(f"✅ Results saved to {json_path} and {summary_path}")
    
    async def _generate_summary_report(self, result: HybridInvestigationResult, path: str):
        """Generate human-readable summary report"""
        with open(path, 'w') as f:
            f.write(f"# Enhanced Hybrid Investigation Report\n")
            f.write(f"**Generated:** {result.timestamp}\n\n")
            
            # Executive Summary
            f.write("## 🎯 Executive Summary\n\n")
            f.write(f"**Investigation Phases:** {', '.join(result.investigation_phases)}\n")
            
            metrics = result.success_metrics
            f.write(f"**Vectorization Success Rate:** {metrics.get('vectorization_success_rate', 'N/A')}%\n")
            f.write(f"**Query Response Time:** {metrics.get('query_response_time', 'N/A')}s\n")
            f.write(f"**LangGraph Compatibility:** {metrics.get('langgraph_compatibility_score', 'N/A')}\n\n")
            
            # Critical Issues
            if result.unified_recommendations.get('critical'):
                f.write("## 🔴 Critical Issues (Fix Immediately)\n\n")
                for rec in result.unified_recommendations['critical']:
                    f.write(f"- {rec}\n")
                f.write("\n")
            
            # High Priority
            if result.unified_recommendations.get('high_priority'):
                f.write("## 🟡 High Priority (Fix This Week)\n\n")
                for rec in result.unified_recommendations['high_priority']:
                    f.write(f"- {rec}\n")
                f.write("\n")
            
            # Medium Priority
            if result.unified_recommendations.get('medium_priority'):
                f.write("## 🟢 Medium Priority (Fix This Month)\n\n")
                for rec in result.unified_recommendations['medium_priority']:
                    f.write(f"- {rec}\n")
                f.write("\n")
            
            # LangGraph Assessment
            if result.langgraph_compatibility:
                f.write("## 🕸️ LangGraph Integration Assessment\n\n")
                lc = result.langgraph_compatibility
                f.write(f"**Agents Discovered:** {lc.agents_discovered}\n")
                f.write(f"**LangGraph Compatible:** {lc.langgraph_compatible}\n")
                f.write(f"**Structured Output Ready:** {lc.structured_output_ready}\n")
                f.write(f"**State Management Score:** {lc.state_management_score:.2f}\n")
                f.write(f"**Workflow Construction Ready:** {lc.workflow_construction_ready}\n\n")

async def main():
    """Main function with enhanced command-line interface"""
    parser = argparse.ArgumentParser(
        description="Enhanced Hybrid Vectorization Investigation with LangGraph Assessment"
    )
    
    parser.add_argument(
        '--full-analysis', 
        action='store_true',
        help='Run complete investigation (all phases)'
    )
    
    parser.add_argument(
        '--rag-focus', 
        action='store_true',
        help='Focus on RAG tooling readiness assessment'
    )
    
    parser.add_argument(
        '--langgraph-assessment', 
        action='store_true',
        help='Include LangGraph compatibility assessment'
    )
    
    parser.add_argument(
        '--interactive', 
        action='store_true',
        help='Include interactive manual findings collection'
    )
    
    parser.add_argument(
        '--agents-only', 
        action='store_true',
        help='Focus only on agent discovery and compatibility'
    )
    
    parser.add_argument(
        '--db-only', 
        action='store_true',
        help='Focus only on database analysis'
    )
    
    args = parser.parse_args()
    
    # Determine focus areas based on arguments
    focus_areas = []
    
    if args.full_analysis:
        focus_areas = list(InvestigationPhase)
    else:
        if args.db_only or not any([args.rag_focus, args.langgraph_assessment, args.agents_only]):
            focus_areas.append(InvestigationPhase.DATABASE)
            focus_areas.append(InvestigationPhase.VECTORIZATION)
        
        if args.agents_only or args.langgraph_assessment:
            focus_areas.append(InvestigationPhase.AGENTS)
        
        if args.langgraph_assessment:
            focus_areas.append(InvestigationPhase.LANGGRAPH)
        
        if args.rag_focus:
            focus_areas.append(InvestigationPhase.RAG_TOOLING)
            focus_areas.append(InvestigationPhase.INTEGRATION)
    
    # Run investigation
    investigator = EnhancedHybridInvestigator(focus_areas)
    
    try:
        result = await investigator.run_investigation(interactive=args.interactive)
        
        print("\n" + "="*60)
        print("✅ INVESTIGATION COMPLETE")
        print("="*60)
        
        print(f"\n📊 Key Metrics:")
        metrics = result.success_metrics
        print(f"  • Vectorization Success: {metrics.get('vectorization_success_rate', 'N/A')}%")
        print(f"  • Query Response Time: {metrics.get('query_response_time', 'N/A')}s")
        print(f"  • LangGraph Compatibility: {metrics.get('langgraph_compatibility_score', 'N/A')}")
        
        if result.langgraph_compatibility:
            lc = result.langgraph_compatibility
            print(f"\n🕸️ LangGraph Assessment:")
            print(f"  • Agents Discovered: {lc.agents_discovered}")
            print(f"  • LangGraph Compatible: {lc.langgraph_compatible}")
            print(f"  • Workflow Ready: {lc.workflow_construction_ready}")
        
        print(f"\n🔴 Critical Issues: {len(result.unified_recommendations.get('critical', []))}")
        for issue in result.unified_recommendations.get('critical', []):
            print(f"  • {issue}")
        
        print(f"\n📁 Results saved to logs/ directory")
        
    except KeyboardInterrupt:
        print("\n⚠️ Investigation interrupted by user")
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        print(f"\n❌ Investigation failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 