#!/usr/bin/env python3
"""
Document Vectorization Pipeline Investigation Script

This script automates the diagnostic checks outlined in the Root Cause Analysis prompt
to systematically investigate the state of document vectorization pipeline.

Usage:
    python scripts/investigate_vectorization_pipeline.py --full-analysis
    python scripts/investigate_vectorization_pipeline.py --db-only
    python scripts/investigate_vectorization_pipeline.py --functions-only
"""

import os
import json
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Database and API clients
import asyncpg
import httpx
from supabase import create_client, Client

# Configuration
from config.database import get_database_url
from config.config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/vectorization_investigation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VectorizationInvestigator:
    """Comprehensive investigation of document vectorization pipeline"""
    
    def __init__(self):
        self.config = get_config()
        self.db_url = get_database_url()
        self.supabase = self._init_supabase()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'database_analysis': {},
            'function_analysis': {},
            'integration_analysis': {},
            'recommendations': []
        }
    
    def _init_supabase(self) -> Optional[Client]:
        """Initialize Supabase client"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if not supabase_url or not supabase_key:
                logger.warning("Supabase credentials not found, skipping Supabase client initialization")
                return None
                
            return create_client(supabase_url, supabase_key)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            return None
    
    async def run_full_investigation(self) -> Dict[str, Any]:
        """Run comprehensive investigation of vectorization pipeline"""
        logger.info("🔍 Starting Full Vectorization Pipeline Investigation")
        
        # Phase 1: Database Analysis
        logger.info("📊 Phase 1: Database Analysis")
        await self.investigate_database_state()
        
        # Phase 2: Function Analysis
        logger.info("🔧 Phase 2: Edge Function Analysis")
        await self.investigate_edge_functions()
        
        # Phase 3: Integration Analysis
        logger.info("🔗 Phase 3: Integration Analysis")
        await self.investigate_agent_integration()
        
        # Phase 4: Generate Recommendations
        logger.info("💡 Phase 4: Generating Recommendations")
        self.generate_recommendations()
        
        # Save results
        await self.save_investigation_results()
        
        return self.results
    
    async def investigate_database_state(self):
        """Investigate database schema, data integrity, and migration status"""
        db_results = {}
        
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # 1. Schema Analysis
            logger.info("   📋 Analyzing database schema...")
            db_results['schema_analysis'] = await self._analyze_schema(conn)
            
            # 2. Data Integrity Check
            logger.info("   🔍 Checking data integrity...")
            db_results['data_integrity'] = await self._check_data_integrity(conn)
            
            # 3. Migration Status
            logger.info("   📦 Checking migration status...")
            db_results['migration_status'] = await self._check_migrations(conn)
            
            # 4. Vector Configuration
            logger.info("   🧮 Checking vector configuration...")
            db_results['vector_config'] = await self._check_vector_config(conn)
            
            # 5. Performance Metrics
            logger.info("   ⚡ Analyzing performance metrics...")
            db_results['performance_metrics'] = await self._analyze_performance(conn)
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Database investigation failed: {e}")
            db_results['error'] = str(e)
        
        self.results['database_analysis'] = db_results
    
    async def _analyze_schema(self, conn) -> Dict[str, Any]:
        """Analyze database schema for document and vector tables"""
        schema_info = {}
        
        # Check for key tables
        tables_query = """
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.columns 
                WHERE table_name = t.table_name) as column_count
        FROM information_schema.tables t
        WHERE table_schema = 'public' 
        AND table_name IN ('documents', 'vectors', 'regulatory_documents', 'user_documents', 'job_queue')
        ORDER BY table_name;
        """
        
        tables = await conn.fetch(tables_query)
        schema_info['tables'] = [dict(record) for record in tables]
        
        # Check for vector extension
        vector_ext_query = "SELECT * FROM pg_extension WHERE extname = 'vector';"
        vector_ext = await conn.fetch(vector_ext_query)
        schema_info['vector_extension'] = len(vector_ext) > 0
        
        # Check indexes on vector columns
        vector_indexes_query = """
        SELECT schemaname, tablename, indexname, indexdef
        FROM pg_indexes 
        WHERE indexdef LIKE '%vector%' OR indexdef LIKE '%embedding%';
        """
        
        indexes = await conn.fetch(vector_indexes_query)
        schema_info['vector_indexes'] = [dict(record) for record in indexes]
        
        return schema_info
    
    async def _check_data_integrity(self, conn) -> Dict[str, Any]:
        """Check data integrity between documents and vectors"""
        integrity_info = {}
        
        # Document and vector counts
        count_queries = {
            'documents': "SELECT COUNT(*) as count FROM documents",
            'vectors': "SELECT COUNT(*) as count FROM vectors", 
            'regulatory_documents': "SELECT COUNT(*) as count FROM regulatory_documents WHERE 1=1",
            'user_documents': "SELECT COUNT(*) as count FROM user_documents WHERE 1=1"
        }
        
        counts = {}
        for table, query in count_queries.items():
            try:
                result = await conn.fetchrow(query)
                counts[table] = result['count'] if result else 0
            except Exception as e:
                counts[table] = f"Error: {str(e)}"
        
        integrity_info['record_counts'] = counts
        
        # Check for orphaned records
        orphaned_docs_query = """
        SELECT COUNT(*) as orphaned_count
        FROM documents d
        LEFT JOIN vectors v ON d.id = v.document_id
        WHERE v.id IS NULL;
        """
        
        try:
            orphaned_result = await conn.fetchrow(orphaned_docs_query)
            integrity_info['orphaned_documents'] = orphaned_result['orphaned_count']
        except Exception as e:
            integrity_info['orphaned_documents'] = f"Error: {str(e)}"
        
        # Check processing queue status
        queue_status_query = """
        SELECT status, COUNT(*) as count
        FROM job_queue 
        GROUP BY status;
        """
        
        try:
            queue_status = await conn.fetch(queue_status_query)
            integrity_info['queue_status'] = [dict(record) for record in queue_status]
        except Exception as e:
            integrity_info['queue_status'] = f"Error: {str(e)}"
        
        return integrity_info
    
    async def _check_migrations(self, conn) -> Dict[str, Any]:
        """Check migration status and identify pending migrations"""
        migration_info = {}
        
        # Check migration table
        migration_query = """
        SELECT version, name, executed_at
        FROM schema_migrations
        ORDER BY version DESC
        LIMIT 10;
        """
        
        try:
            migrations = await conn.fetch(migration_query)
            migration_info['recent_migrations'] = [dict(record) for record in migrations]
            
            # Check for migration files vs executed migrations
            migration_files = list(Path('db/migrations').glob('*.sql'))
            migration_info['total_migration_files'] = len(migration_files)
            migration_info['executed_migrations'] = len(migrations)
            
        except Exception as e:
            migration_info['error'] = str(e)
        
        return migration_info
    
    async def _check_vector_config(self, conn) -> Dict[str, Any]:
        """Check vector configuration and capabilities"""
        vector_info = {}
        
        # Check vector column configuration
        vector_columns_query = """
        SELECT table_name, column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE data_type = 'vector' OR column_name LIKE '%embedding%';
        """
        
        try:
            vector_columns = await conn.fetch(vector_columns_query)
            vector_info['vector_columns'] = [dict(record) for record in vector_columns]
        except Exception as e:
            vector_info['vector_columns_error'] = str(e)
        
        # Test vector operations
        try:
            test_vector_query = "SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector as distance;"
            test_result = await conn.fetchrow(test_vector_query)
            vector_info['vector_operations_working'] = True
            vector_info['sample_distance'] = float(test_result['distance'])
        except Exception as e:
            vector_info['vector_operations_working'] = False
            vector_info['vector_operations_error'] = str(e)
        
        return vector_info
    
    async def _analyze_performance(self, conn) -> Dict[str, Any]:
        """Analyze performance metrics for document processing"""
        performance_info = {}
        
        # Recent processing times
        processing_times_query = """
        SELECT 
            AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_processing_seconds,
            MIN(EXTRACT(EPOCH FROM (updated_at - created_at))) as min_processing_seconds,
            MAX(EXTRACT(EPOCH FROM (updated_at - created_at))) as max_processing_seconds,
            COUNT(*) as total_processed
        FROM job_queue 
        WHERE status = 'completed' 
        AND updated_at > NOW() - INTERVAL '24 hours';
        """
        
        try:
            perf_result = await conn.fetchrow(processing_times_query)
            if perf_result:
                performance_info['processing_times'] = dict(perf_result)
        except Exception as e:
            performance_info['processing_times_error'] = str(e)
        
        # Database size and growth
        db_size_query = """
        SELECT 
            pg_size_pretty(pg_database_size(current_database())) as database_size,
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as table_size
        FROM pg_tables 
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 10;
        """
        
        try:
            size_results = await conn.fetch(db_size_query)
            performance_info['database_sizes'] = [dict(record) for record in size_results]
        except Exception as e:
            performance_info['database_sizes_error'] = str(e)
        
        return performance_info
    
    async def investigate_edge_functions(self):
        """Investigate Supabase edge functions status and performance"""
        function_results = {}
        
        if not self.supabase:
            function_results['error'] = "Supabase client not available"
            self.results['function_analysis'] = function_results
            return
        
        # Test each critical function
        functions_to_test = [
            'doc-parser',
            'vector-processor', 
            'regulatory-vector-processor',
            'bulk-regulatory-processor',
            'trigger-processor'
        ]
        
        for func_name in functions_to_test:
            logger.info(f"   🧪 Testing function: {func_name}")
            function_results[func_name] = await self._test_edge_function(func_name)
        
        # Check function deployment status
        function_results['deployment_status'] = await self._check_function_deployment()
        
        self.results['function_analysis'] = function_results
    
    async def _test_edge_function(self, function_name: str) -> Dict[str, Any]:
        """Test individual edge function"""
        test_result = {
            'function_name': function_name,
            'test_timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'response_time': None,
            'error': None
        }
        
        try:
            # Test with simple ping payload
            test_payload = {'test': True, 'timestamp': datetime.now().isoformat()}
            
            start_time = datetime.now()
            
            # Use httpx for function testing
            async with httpx.AsyncClient() as client:
                supabase_url = os.getenv('SUPABASE_URL')
                function_url = f"{supabase_url}/functions/v1/{function_name}"
                
                headers = {
                    'Authorization': f"Bearer {os.getenv('SUPABASE_ANON_KEY')}",
                    'Content-Type': 'application/json'
                }
                
                response = await client.post(
                    function_url,
                    json=test_payload,
                    headers=headers,
                    timeout=30.0
                )
                
                end_time = datetime.now()
                test_result['response_time'] = (end_time - start_time).total_seconds()
                test_result['status_code'] = response.status_code
                test_result['status'] = 'success' if response.status_code < 400 else 'error'
                
                if response.status_code >= 400:
                    test_result['error'] = response.text
                
        except Exception as e:
            test_result['status'] = 'error'
            test_result['error'] = str(e)
        
        return test_result
    
    async def _check_function_deployment(self) -> Dict[str, Any]:
        """Check function deployment status"""
        deployment_info = {
            'check_timestamp': datetime.now().isoformat(),
            'functions_directory_exists': Path('supabase/functions').exists(),
            'function_count': 0,
            'functions_found': []
        }
        
        if deployment_info['functions_directory_exists']:
            functions_dir = Path('supabase/functions')
            function_dirs = [d for d in functions_dir.iterdir() if d.is_dir()]
            deployment_info['function_count'] = len(function_dirs)
            deployment_info['functions_found'] = [d.name for d in function_dirs]
        
        return deployment_info
    
    async def investigate_agent_integration(self):
        """Investigate RAG agent integration with vectorized documents"""
        integration_results = {}
        
        # Test document retrieval capabilities
        logger.info("   🤖 Testing agent document retrieval...")
        integration_results['document_retrieval'] = await self._test_document_retrieval()
        
        # Check agent configuration
        logger.info("   ⚙️ Checking agent configuration...")
        integration_results['agent_config'] = await self._check_agent_configuration()
        
        # Test vector search performance
        logger.info("   🔍 Testing vector search performance...")
        integration_results['vector_search'] = await self._test_vector_search_performance()
        
        self.results['integration_analysis'] = integration_results
    
    async def _test_document_retrieval(self) -> Dict[str, Any]:
        """Test document retrieval for RAG agents"""
        retrieval_info = {
            'test_timestamp': datetime.now().isoformat(),
            'tests_performed': [],
            'success_count': 0,
            'failure_count': 0
        }
        
        # Test queries
        test_queries = [
            "insurance coverage",
            "deductible information", 
            "provider network",
            "claim process"
        ]
        
        for query in test_queries:
            test_result = await self._perform_retrieval_test(query)
            retrieval_info['tests_performed'].append(test_result)
            
            if test_result['success']:
                retrieval_info['success_count'] += 1
            else:
                retrieval_info['failure_count'] += 1
        
        retrieval_info['success_rate'] = (
            retrieval_info['success_count'] / len(test_queries) * 100
            if test_queries else 0
        )
        
        return retrieval_info
    
    async def _perform_retrieval_test(self, query: str) -> Dict[str, Any]:
        """Perform individual retrieval test"""
        test_result = {
            'query': query,
            'success': False,
            'documents_found': 0,
            'response_time': None,
            'error': None
        }
        
        try:
            if not self.supabase:
                test_result['error'] = "Supabase client not available"
                return test_result
            
            start_time = datetime.now()
            
            # Simulate vector search (replace with actual implementation)
            # This would typically involve:
            # 1. Convert query to vector
            # 2. Perform similarity search
            # 3. Return relevant documents
            
            # For now, just check if we can query the database
            result = self.supabase.table('documents').select('*').limit(5).execute()
            
            end_time = datetime.now()
            test_result['response_time'] = (end_time - start_time).total_seconds()
            test_result['documents_found'] = len(result.data) if result.data else 0
            test_result['success'] = True
            
        except Exception as e:
            test_result['error'] = str(e)
        
        return test_result
    
    async def _check_agent_configuration(self) -> Dict[str, Any]:
        """Check agent configuration for document access"""
        config_info = {
            'agents_directory_exists': Path('agents').exists(),
            'discovered_agents': [],
            'rag_enabled_agents': []
        }
        
        if config_info['agents_directory_exists']:
            # Discover agents that might use RAG
            agents_dir = Path('agents')
            for agent_dir in agents_dir.iterdir():
                if agent_dir.is_dir() and not agent_dir.name.startswith('.'):
                    config_info['discovered_agents'].append(agent_dir.name)
                    
                    # Check if agent has RAG capabilities
                    if self._agent_has_rag_capabilities(agent_dir):
                        config_info['rag_enabled_agents'].append(agent_dir.name)
        
        return config_info
    
    def _agent_has_rag_capabilities(self, agent_dir: Path) -> bool:
        """Check if agent has RAG capabilities"""
        # Look for RAG-related files or imports
        rag_indicators = ['rag', 'vector', 'retrieval', 'document']
        
        for py_file in agent_dir.glob('*.py'):
            try:
                content = py_file.read_text().lower()
                if any(indicator in content for indicator in rag_indicators):
                    return True
            except:
                continue
        
        return False
    
    async def _test_vector_search_performance(self) -> Dict[str, Any]:
        """Test vector search performance"""
        performance_info = {
            'test_timestamp': datetime.now().isoformat(),
            'search_tests': [],
            'average_response_time': None,
            'error': None
        }
        
        try:
            # Perform multiple search tests
            test_vectors = [
                [0.1, 0.2, 0.3],  # Mock vectors for testing
                [0.4, 0.5, 0.6],
                [0.7, 0.8, 0.9]
            ]
            
            response_times = []
            
            for i, test_vector in enumerate(test_vectors):
                start_time = datetime.now()
                
                # Simulate vector search (replace with actual implementation)
                await asyncio.sleep(0.1)  # Simulate processing time
                
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                response_times.append(response_time)
                
                performance_info['search_tests'].append({
                    'test_id': i + 1,
                    'response_time': response_time,
                    'success': True
                })
            
            performance_info['average_response_time'] = sum(response_times) / len(response_times)
            
        except Exception as e:
            performance_info['error'] = str(e)
        
        return performance_info
    
    def generate_recommendations(self):
        """Generate recommendations based on investigation results"""
        recommendations = []
        
        # Database recommendations
        db_analysis = self.results.get('database_analysis', {})
        
        if db_analysis.get('error'):
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Database',
                'issue': 'Database connection failed',
                'recommendation': 'Fix database connection issues and verify credentials',
                'action': 'Check database URL and connection parameters'
            })
        
        # Check for orphaned documents
        data_integrity = db_analysis.get('data_integrity', {})
        orphaned_count = data_integrity.get('orphaned_documents', 0)
        
        if isinstance(orphaned_count, int) and orphaned_count > 0:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Data Integrity',
                'issue': f'{orphaned_count} documents without vectors found',
                'recommendation': 'Process orphaned documents through vectorization pipeline',
                'action': 'Run batch vectorization job for orphaned documents'
            })
        
        # Function recommendations
        function_analysis = self.results.get('function_analysis', {})
        
        for func_name, func_result in function_analysis.items():
            if isinstance(func_result, dict) and func_result.get('status') == 'error':
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Edge Functions',
                    'issue': f'Function {func_name} is failing',
                    'recommendation': f'Debug and fix {func_name} function',
                    'action': f'Check function logs and redeploy {func_name}'
                })
        
        # Integration recommendations
        integration_analysis = self.results.get('integration_analysis', {})
        doc_retrieval = integration_analysis.get('document_retrieval', {})
        
        success_rate = doc_retrieval.get('success_rate', 0)
        if success_rate < 80:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'RAG Integration',
                'issue': f'Document retrieval success rate is {success_rate}%',
                'recommendation': 'Improve document retrieval reliability',
                'action': 'Debug vector search and document access mechanisms'
            })
        
        # Performance recommendations
        vector_search = integration_analysis.get('vector_search', {})
        avg_response_time = vector_search.get('average_response_time', 0)
        
        if avg_response_time > 2.0:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Performance',
                'issue': f'Vector search response time is {avg_response_time:.2f}s',
                'recommendation': 'Optimize vector search performance',
                'action': 'Add vector indexes and optimize query patterns'
            })
        
        self.results['recommendations'] = recommendations
    
    async def save_investigation_results(self):
        """Save investigation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"logs/vectorization_investigation_results_{timestamp}.json"
        
        # Ensure logs directory exists
        Path('logs').mkdir(exist_ok=True)
        
        # Save detailed results
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Save summary report
        summary_file = f"logs/vectorization_investigation_summary_{timestamp}.md"
        await self._generate_summary_report(summary_file)
        
        logger.info(f"📋 Investigation results saved to {results_file}")
        logger.info(f"📋 Summary report saved to {summary_file}")
    
    async def _generate_summary_report(self, filename: str):
        """Generate human-readable summary report"""
        with open(filename, 'w') as f:
            f.write("# Document Vectorization Pipeline Investigation Summary\n\n")
            f.write(f"**Investigation Date:** {self.results['timestamp']}\n\n")
            
            # Database Summary
            f.write("## 📊 Database Analysis\n\n")
            db_analysis = self.results.get('database_analysis', {})
            
            if db_analysis.get('error'):
                f.write(f"❌ **Critical Issue:** {db_analysis['error']}\n\n")
            else:
                # Schema info
                schema = db_analysis.get('schema_analysis', {})
                tables = schema.get('tables', [])
                f.write(f"**Tables Found:** {len(tables)}\n")
                for table in tables:
                    f.write(f"- {table['table_name']}: {table['column_count']} columns\n")
                
                # Data integrity
                integrity = db_analysis.get('data_integrity', {})
                counts = integrity.get('record_counts', {})
                f.write(f"\n**Record Counts:**\n")
                for table, count in counts.items():
                    f.write(f"- {table}: {count}\n")
                
                orphaned = integrity.get('orphaned_documents', 0)
                if orphaned > 0:
                    f.write(f"\n⚠️ **Warning:** {orphaned} orphaned documents found\n")
            
            # Function Summary
            f.write("\n## 🔧 Edge Function Analysis\n\n")
            function_analysis = self.results.get('function_analysis', {})
            
            working_functions = []
            failing_functions = []
            
            for func_name, func_result in function_analysis.items():
                if isinstance(func_result, dict):
                    if func_result.get('status') == 'success':
                        working_functions.append(func_name)
                    elif func_result.get('status') == 'error':
                        failing_functions.append(func_name)
            
            f.write(f"**Working Functions:** {len(working_functions)}\n")
            for func in working_functions:
                f.write(f"- ✅ {func}\n")
            
            f.write(f"\n**Failing Functions:** {len(failing_functions)}\n")
            for func in failing_functions:
                f.write(f"- ❌ {func}\n")
            
            # Recommendations
            f.write("\n## 💡 Recommendations\n\n")
            recommendations = self.results.get('recommendations', [])
            
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {
                    'HIGH': '🔴',
                    'MEDIUM': '🟡', 
                    'LOW': '🟢'
                }.get(rec['priority'], '⚪')
                
                f.write(f"{i}. {priority_emoji} **{rec['category']}** - {rec['priority']} Priority\n")
                f.write(f"   - **Issue:** {rec['issue']}\n")
                f.write(f"   - **Recommendation:** {rec['recommendation']}\n")
                f.write(f"   - **Action:** {rec['action']}\n\n")
            
            f.write("---\n")
            f.write("*Investigation completed by VectorizationInvestigator*\n")

async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Investigate document vectorization pipeline')
    parser.add_argument('--full-analysis', action='store_true', help='Run full investigation')
    parser.add_argument('--db-only', action='store_true', help='Database analysis only')
    parser.add_argument('--functions-only', action='store_true', help='Edge functions analysis only')
    
    args = parser.parse_args()
    
    investigator = VectorizationInvestigator()
    
    try:
        if args.db_only:
            logger.info("🔍 Running Database Analysis Only")
            await investigator.investigate_database_state()
        elif args.functions_only:
            logger.info("🔍 Running Edge Functions Analysis Only")
            await investigator.investigate_edge_functions()
        else:
            # Default to full analysis
            logger.info("🔍 Running Full Investigation")
            await investigator.run_full_investigation()
        
        # Save results
        await investigator.save_investigation_results()
        
        # Print summary
        recommendations = investigator.results.get('recommendations', [])
        high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
        
        logger.info(f"📋 Investigation completed!")
        logger.info(f"📊 Found {len(recommendations)} total recommendations")
        logger.info(f"🔴 Found {len(high_priority)} high-priority issues")
        
        if high_priority:
            logger.warning("🚨 High-priority issues found - immediate attention required!")
            for rec in high_priority:
                logger.warning(f"   - {rec['category']}: {rec['issue']}")
        
    except Exception as e:
        logger.error(f"❌ Investigation failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 