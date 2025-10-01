#!/usr/bin/env python3
"""
FM-027 Staging Investigation

This script uses the Supabase MCP tools to investigate the timing issues
in the Insurance Navigator document processing pipeline.

Key Areas of Investigation:
1. Job Status Update Timing
2. File Access Timing
3. Database Transaction Behavior
4. Race Condition Reproduction
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FM027StagingInvestigator:
    """Investigator for FM-027 timing issues using Supabase MCP tools"""
    
    def __init__(self):
        self.test_user_id = str(uuid.uuid4())
        self.test_results = []
        
        logger.info("FM027 Staging Investigator initialized")
    
    async def run_staging_investigation(self):
        """Run investigation using staging Supabase"""
        logger.info("Starting FM-027 staging investigation")
        
        try:
            # Phase 1: Database Analysis
            await self.analyze_database_state()
            
            # Phase 2: Job Status Analysis
            await self.analyze_job_status_patterns()
            
            # Phase 3: File Access Analysis
            await self.analyze_file_access_patterns()
            
            # Phase 4: Race Condition Analysis
            await self.analyze_race_conditions()
            
            # Generate comprehensive report
            await self.generate_investigation_report()
            
        except Exception as e:
            logger.error(f"Staging investigation failed: {str(e)}", exc_info=True)
            raise
    
    async def analyze_database_state(self):
        """Analyze current database state"""
        logger.info("=== Phase 1: Database State Analysis ===")
        
        analysis = {
            "phase": "database_state_analysis",
            "start_time": datetime.utcnow().isoformat(),
            "findings": []
        }
        
        try:
            # Get current job status distribution
            job_status_query = """
                SELECT status, COUNT(*) as count
                FROM upload_pipeline.upload_jobs
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY status
                ORDER BY count DESC
            """
            
            # This would be called via MCP tool in actual execution
            # For now, we'll simulate the analysis
            analysis["findings"].append({
                "metric": "job_status_distribution",
                "description": "Distribution of job statuses in last 24 hours",
                "query": job_status_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            # Get failed jobs analysis
            failed_jobs_query = """
                SELECT 
                    status,
                    last_error,
                    COUNT(*) as count,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_processing_time
                FROM upload_pipeline.upload_jobs
                WHERE status LIKE 'failed_%'
                AND created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY status, last_error
                ORDER BY count DESC
            """
            
            analysis["findings"].append({
                "metric": "failed_jobs_analysis",
                "description": "Analysis of failed jobs and their errors",
                "query": failed_jobs_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            # Get timing analysis
            timing_query = """
                SELECT 
                    status,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_duration,
                    MIN(EXTRACT(EPOCH FROM (updated_at - created_at))) as min_duration,
                    MAX(EXTRACT(EPOCH FROM (updated_at - created_at))) as max_duration,
                    COUNT(*) as count
                FROM upload_pipeline.upload_jobs
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY status
                ORDER BY avg_duration
            """
            
            analysis["findings"].append({
                "metric": "timing_analysis",
                "description": "Analysis of job processing timing",
                "query": timing_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            logger.info("Database state analysis completed")
            
        except Exception as e:
            analysis["error"] = str(e)
            logger.error(f"Database state analysis failed: {str(e)}")
        
        analysis["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(analysis)
    
    async def analyze_job_status_patterns(self):
        """Analyze job status transition patterns"""
        logger.info("=== Phase 2: Job Status Pattern Analysis ===")
        
        analysis = {
            "phase": "job_status_pattern_analysis",
            "start_time": datetime.utcnow().isoformat(),
            "findings": []
        }
        
        try:
            # Analyze status transitions
            status_transition_query = """
                WITH status_transitions AS (
                    SELECT 
                        job_id,
                        status,
                        LAG(status) OVER (PARTITION BY job_id ORDER BY updated_at) as previous_status,
                        updated_at,
                        LAG(updated_at) OVER (PARTITION BY job_id ORDER BY updated_at) as previous_updated_at
                    FROM upload_pipeline.upload_jobs
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                )
                SELECT 
                    previous_status,
                    status as current_status,
                    COUNT(*) as transition_count,
                    AVG(EXTRACT(EPOCH FROM (updated_at - previous_updated_at))) as avg_transition_time
                FROM status_transitions
                WHERE previous_status IS NOT NULL
                GROUP BY previous_status, status
                ORDER BY transition_count DESC
            """
            
            analysis["findings"].append({
                "metric": "status_transitions",
                "description": "Analysis of job status transitions and timing",
                "query": status_transition_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            # Analyze stuck jobs
            stuck_jobs_query = """
                SELECT 
                    job_id,
                    status,
                    created_at,
                    updated_at,
                    EXTRACT(EPOCH FROM (NOW() - updated_at)) as seconds_since_update
                FROM upload_pipeline.upload_jobs
                WHERE status IN ('uploaded', 'parse_queued', 'parsed', 'chunking', 'embedding_queued')
                AND updated_at < NOW() - INTERVAL '1 hour'
                ORDER BY seconds_since_update DESC
                LIMIT 20
            """
            
            analysis["findings"].append({
                "metric": "stuck_jobs",
                "description": "Analysis of jobs that appear to be stuck",
                "query": stuck_jobs_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            # Analyze race conditions
            race_condition_query = """
                SELECT 
                    job_id,
                    status,
                    created_at,
                    updated_at,
                    EXTRACT(EPOCH FROM (updated_at - created_at)) as processing_time
                FROM upload_pipeline.upload_jobs
                WHERE status = 'failed_parse'
                AND last_error LIKE '%not accessible%'
                AND created_at >= NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 20
            """
            
            analysis["findings"].append({
                "metric": "race_condition_evidence",
                "description": "Analysis of jobs that failed due to file access issues",
                "query": race_condition_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            logger.info("Job status pattern analysis completed")
            
        except Exception as e:
            analysis["error"] = str(e)
            logger.error(f"Job status pattern analysis failed: {str(e)}")
        
        analysis["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(analysis)
    
    async def analyze_file_access_patterns(self):
        """Analyze file access patterns and timing"""
        logger.info("=== Phase 3: File Access Pattern Analysis ===")
        
        analysis = {
            "phase": "file_access_pattern_analysis",
            "start_time": datetime.utcnow().isoformat(),
            "findings": []
        }
        
        try:
            # Analyze file upload timing
            file_upload_timing_query = """
                SELECT 
                    d.document_id,
                    d.raw_path,
                    d.created_at as document_created,
                    uj.created_at as job_created,
                    uj.updated_at as job_updated,
                    EXTRACT(EPOCH FROM (uj.updated_at - d.created_at)) as upload_to_processing_time
                FROM upload_pipeline.documents d
                JOIN upload_pipeline.upload_jobs uj ON d.document_id = uj.document_id
                WHERE d.created_at >= NOW() - INTERVAL '24 hours'
                AND uj.status = 'uploaded'
                ORDER BY upload_to_processing_time
            """
            
            analysis["findings"].append({
                "metric": "file_upload_timing",
                "description": "Analysis of file upload to processing timing",
                "query": file_upload_timing_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            # Analyze file access failures
            file_access_failure_query = """
                SELECT 
                    uj.job_id,
                    d.raw_path,
                    uj.status,
                    uj.last_error,
                    uj.created_at,
                    uj.updated_at,
                    EXTRACT(EPOCH FROM (uj.updated_at - uj.created_at)) as failure_time
                FROM upload_pipeline.upload_jobs uj
                JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                WHERE uj.status = 'failed_parse'
                AND (uj.last_error LIKE '%not accessible%' OR uj.last_error LIKE '%storage%')
                AND uj.created_at >= NOW() - INTERVAL '24 hours'
                ORDER BY uj.created_at DESC
            """
            
            analysis["findings"].append({
                "metric": "file_access_failures",
                "description": "Analysis of file access failures",
                "query": file_access_failure_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            # Analyze storage path patterns
            storage_path_query = """
                SELECT 
                    raw_path,
                    COUNT(*) as count,
                    AVG(bytes_len) as avg_file_size,
                    MIN(created_at) as first_upload,
                    MAX(created_at) as last_upload
                FROM upload_pipeline.documents
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY raw_path
                ORDER BY count DESC
                LIMIT 20
            """
            
            analysis["findings"].append({
                "metric": "storage_path_patterns",
                "description": "Analysis of storage path patterns and file sizes",
                "query": storage_path_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            logger.info("File access pattern analysis completed")
            
        except Exception as e:
            analysis["error"] = str(e)
            logger.error(f"File access pattern analysis failed: {str(e)}")
        
        analysis["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(analysis)
    
    async def analyze_race_conditions(self):
        """Analyze race conditions and timing issues"""
        logger.info("=== Phase 4: Race Condition Analysis ===")
        
        analysis = {
            "phase": "race_condition_analysis",
            "start_time": datetime.utcnow().isoformat(),
            "findings": []
        }
        
        try:
            # Analyze concurrent job processing
            concurrent_jobs_query = """
                WITH job_timing AS (
                    SELECT 
                        job_id,
                        document_id,
                        status,
                        created_at,
                        updated_at,
                        EXTRACT(EPOCH FROM (updated_at - created_at)) as processing_time
                    FROM upload_pipeline.upload_jobs
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                )
                SELECT 
                    DATE_TRUNC('minute', created_at) as minute_bucket,
                    COUNT(*) as jobs_created,
                    COUNT(CASE WHEN status = 'failed_parse' THEN 1 END) as failed_jobs,
                    AVG(processing_time) as avg_processing_time
                FROM job_timing
                GROUP BY minute_bucket
                HAVING COUNT(*) > 1
                ORDER BY minute_bucket DESC
            """
            
            analysis["findings"].append({
                "metric": "concurrent_job_processing",
                "description": "Analysis of concurrent job processing and failures",
                "query": concurrent_jobs_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            # Analyze timing windows
            timing_window_query = """
                SELECT 
                    status,
                    COUNT(*) as count,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_duration,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (updated_at - created_at))) as median_duration,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (updated_at - created_at))) as p95_duration
                FROM upload_pipeline.upload_jobs
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY status
                ORDER BY avg_duration
            """
            
            analysis["findings"].append({
                "metric": "timing_windows",
                "description": "Analysis of job processing timing windows",
                "query": timing_window_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            # Analyze error patterns
            error_pattern_query = """
                SELECT 
                    last_error,
                    COUNT(*) as error_count,
                    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_failure_time
                FROM upload_pipeline.upload_jobs
                WHERE status = 'failed_parse'
                AND last_error IS NOT NULL
                AND created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY last_error
                ORDER BY error_count DESC
                LIMIT 10
            """
            
            analysis["findings"].append({
                "metric": "error_patterns",
                "description": "Analysis of error patterns and failure timing",
                "query": error_pattern_query,
                "note": "Would be executed via mcp_supabase_staging_execute_sql"
            })
            
            logger.info("Race condition analysis completed")
            
        except Exception as e:
            analysis["error"] = str(e)
            logger.error(f"Race condition analysis failed: {str(e)}")
        
        analysis["end_time"] = datetime.utcnow().isoformat()
        self.test_results.append(analysis)
    
    async def generate_investigation_report(self):
        """Generate comprehensive investigation report"""
        logger.info("Generating FM-027 investigation report")
        
        report = {
            "investigation_id": str(uuid.uuid4()),
            "investigation_name": "FM-027 Staging Investigation",
            "start_time": self.test_results[0]["start_time"] if self.test_results else datetime.utcnow().isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "environment": {
                "supabase_url": "https://dfgzeastcxnoqshgyotp.supabase.co",
                "investigation_type": "staging_analysis"
            },
            "analysis_results": self.test_results,
            "summary": self._generate_summary(),
            "recommendations": self._generate_recommendations(),
            "next_steps": self._generate_next_steps()
        }
        
        # Save report to file
        report_filename = f"fm027_staging_investigation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Investigation report saved to {report_filename}")
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate investigation summary"""
        summary = {
            "total_phases": len(self.test_results),
            "completed_phases": sum(1 for phase in self.test_results if "error" not in phase),
            "failed_phases": sum(1 for phase in self.test_results if "error" in phase),
            "key_queries": [],
            "investigation_focus": [
                "Job status transition timing",
                "File access failure patterns",
                "Race condition evidence",
                "Database consistency issues"
            ]
        }
        
        # Collect key queries from all phases
        for phase in self.test_results:
            if "findings" in phase:
                for finding in phase["findings"]:
                    summary["key_queries"].append({
                        "phase": phase["phase"],
                        "metric": finding["metric"],
                        "description": finding["description"],
                        "query": finding["query"]
                    })
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on investigation"""
        recommendations = [
            "Execute the provided SQL queries against staging database to gather actual data",
            "Analyze job status transition timing to identify bottlenecks",
            "Investigate file access failure patterns to understand race conditions",
            "Monitor concurrent job processing to identify timing issues",
            "Implement file existence checks before processing",
            "Add retry mechanisms for failed file access",
            "Implement job status update delays to ensure file availability",
            "Add comprehensive logging for timing analysis",
            "Consider implementing circuit breaker pattern for file access failures",
            "Add monitoring and alerting for race condition detection"
        ]
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generate next steps for the investigation"""
        next_steps = [
            "Run the provided SQL queries against staging database using MCP tools",
            "Analyze the query results to identify specific timing issues",
            "Create targeted tests to reproduce identified race conditions",
            "Implement and test solutions based on findings",
            "Monitor production system for similar issues",
            "Document findings and solutions for future reference"
        ]
        
        return next_steps
    
    def _print_summary(self, report: Dict[str, Any]):
        """Print investigation summary to console"""
        print("\n" + "="*80)
        print("FM-027 STAGING INVESTIGATION SUMMARY")
        print("="*80)
        
        summary = report["summary"]
        print(f"Total Phases: {summary['total_phases']}")
        print(f"Completed Phases: {summary['completed_phases']}")
        print(f"Failed Phases: {summary['failed_phases']}")
        
        print("\nInvestigation Focus:")
        for focus in summary["investigation_focus"]:
            print(f"  • {focus}")
        
        print(f"\nKey Queries Generated: {len(summary['key_queries'])}")
        
        print("\nRecommendations:")
        for recommendation in report["recommendations"]:
            print(f"  • {recommendation}")
        
        print("\nNext Steps:")
        for step in report["next_steps"]:
            print(f"  • {step}")
        
        print("\n" + "="*80)


async def main():
    """Main function to run the FM-027 staging investigation"""
    investigator = FM027StagingInvestigator()
    
    try:
        await investigator.run_staging_investigation()
    except Exception as e:
        logger.error(f"Investigation failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
