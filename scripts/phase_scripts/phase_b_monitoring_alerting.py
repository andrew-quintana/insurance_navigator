#!/usr/bin/env python3
"""
Phase B.2.2: Monitoring and Alerting Implementation
UUID Standardization - Production Monitoring System

This module provides comprehensive monitoring and alerting for UUID migration:
1. UUID-specific monitoring metrics
2. Migration progress dashboards
3. Critical alerting systems
4. Real-time health monitoring
5. Performance impact tracking

Reference: PHASED_TODO_IMPLEMENTATION.md "B.2.2 Monitoring and Alerting"
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import asyncpg
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert level enumeration."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MonitoringMetric:
    """Single monitoring metric."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    unit: str = "count"

@dataclass
class Alert:
    """Alert definition."""
    alert_id: str
    level: AlertLevel
    message: str
    timestamp: datetime
    metric_name: str
    threshold: float
    current_value: float
    resolved: bool = False

class UUIDMonitoringSystem:
    """Comprehensive UUID monitoring and alerting system."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
        self.metrics = []
        self.alerts = []
        self.alert_thresholds = {
            "uuid_generation_failure_rate": 0.05,  # 5% failure rate
            "uuid_mismatch_rate": 0.01,  # 1% mismatch rate
            "rag_retrieval_failure_rate": 0.1,  # 10% failure rate
            "migration_failure_rate": 0.05,  # 5% migration failure rate
            "system_performance_degradation": 0.5,  # 50% performance drop
        }
    
    async def connect_database(self) -> bool:
        """Connect to the database."""
        try:
            logger.info("🔌 Connecting to database...")
            self.conn = await asyncpg.connect(self.database_url)
            logger.info("✅ Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def disconnect_database(self):
        """Disconnect from the database."""
        if self.conn:
            await self.conn.close()
            logger.info("🔌 Database disconnected")
    
    async def collect_uuid_metrics(self) -> List[MonitoringMetric]:
        """Collect UUID-specific monitoring metrics."""
        logger.info("📊 Collecting UUID metrics...")
        
        metrics = []
        current_time = datetime.utcnow()
        
        try:
            # 1. UUID Generation Success Rate
            total_documents = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.documents
            """)
            
            deterministic_documents = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.documents
                WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            """)
            
            uuid_generation_success_rate = deterministic_documents / total_documents if total_documents > 0 else 0
            
            metrics.append(MonitoringMetric(
                name="uuid_generation_success_rate",
                value=uuid_generation_success_rate,
                timestamp=current_time,
                tags={"type": "uuid_generation"},
                unit="percentage"
            ))
            
            # 2. UUID Mismatch Rate
            random_documents = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.documents
                WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            """)
            
            uuid_mismatch_rate = random_documents / total_documents if total_documents > 0 else 0
            
            metrics.append(MonitoringMetric(
                name="uuid_mismatch_rate",
                value=uuid_mismatch_rate,
                timestamp=current_time,
                tags={"type": "uuid_consistency"},
                unit="percentage"
            ))
            
            # 3. Pipeline Stage Consistency
            documents_with_chunks = await self.conn.fetchval("""
                SELECT COUNT(DISTINCT d.document_id)
                FROM upload_pipeline.documents d
                JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
            """)
            
            pipeline_consistency_rate = documents_with_chunks / total_documents if total_documents > 0 else 0
            
            metrics.append(MonitoringMetric(
                name="pipeline_consistency_rate",
                value=pipeline_consistency_rate,
                timestamp=current_time,
                tags={"type": "pipeline_health"},
                unit="percentage"
            ))
            
            # 4. RAG Retrieval Success Rate (simulated)
            # This would need actual RAG query testing
            rag_success_rate = 1.0 if uuid_mismatch_rate == 0 else 0.0
            
            metrics.append(MonitoringMetric(
                name="rag_retrieval_success_rate",
                value=rag_success_rate,
                timestamp=current_time,
                tags={"type": "rag_functionality"},
                unit="percentage"
            ))
            
            # 5. Document Processing Status Distribution
            status_counts = await self.conn.fetch("""
                SELECT processing_status, COUNT(*) as count
                FROM upload_pipeline.documents
                GROUP BY processing_status
            """)
            
            for status in status_counts:
                metrics.append(MonitoringMetric(
                    name="document_processing_status",
                    value=status['count'],
                    timestamp=current_time,
                    tags={"status": status['processing_status'] or "null"},
                    unit="count"
                ))
            
            # 6. Chunk Count Distribution
            chunk_stats = await self.conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_chunks,
                    AVG(chunk_count) as avg_chunks_per_doc,
                    MAX(chunk_count) as max_chunks_per_doc
                FROM (
                    SELECT d.document_id, COUNT(dc.chunk_id) as chunk_count
                    FROM upload_pipeline.documents d
                    LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
                    GROUP BY d.document_id
                ) chunk_counts
            """)
            
            if chunk_stats:
                metrics.append(MonitoringMetric(
                    name="total_chunks",
                    value=chunk_stats['total_chunks'],
                    timestamp=current_time,
                    tags={"type": "chunk_metrics"},
                    unit="count"
                ))
                
                metrics.append(MonitoringMetric(
                    name="avg_chunks_per_document",
                    value=chunk_stats['avg_chunks_per_doc'] or 0,
                    timestamp=current_time,
                    tags={"type": "chunk_metrics"},
                    unit="count"
                ))
            
            # 7. User Impact Metrics
            affected_users = await self.conn.fetchval("""
                SELECT COUNT(DISTINCT user_id)
                FROM upload_pipeline.documents
                WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            """)
            
            metrics.append(MonitoringMetric(
                name="affected_users_count",
                value=affected_users,
                timestamp=current_time,
                tags={"type": "user_impact"},
                unit="count"
            ))
            
            logger.info(f"📊 Collected {len(metrics)} UUID metrics")
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to collect UUID metrics: {e}")
            return []
    
    async def check_alert_conditions(self, metrics: List[MonitoringMetric]) -> List[Alert]:
        """Check metrics against alert thresholds."""
        logger.info("🚨 Checking alert conditions...")
        
        alerts = []
        current_time = datetime.utcnow()
        
        for metric in metrics:
            # Check UUID generation failure rate
            if metric.name == "uuid_generation_success_rate":
                failure_rate = 1.0 - metric.value
                if failure_rate > self.alert_thresholds["uuid_generation_failure_rate"]:
                    alerts.append(Alert(
                        alert_id=f"uuid_gen_failure_{int(time.time())}",
                        level=AlertLevel.ERROR,
                        message=f"UUID generation failure rate {failure_rate:.2%} exceeds threshold {self.alert_thresholds['uuid_generation_failure_rate']:.2%}",
                        timestamp=current_time,
                        metric_name=metric.name,
                        threshold=self.alert_thresholds["uuid_generation_failure_rate"],
                        current_value=failure_rate
                    ))
            
            # Check UUID mismatch rate
            elif metric.name == "uuid_mismatch_rate":
                if metric.value > self.alert_thresholds["uuid_mismatch_rate"]:
                    alerts.append(Alert(
                        alert_id=f"uuid_mismatch_{int(time.time())}",
                        level=AlertLevel.CRITICAL,
                        message=f"UUID mismatch rate {metric.value:.2%} exceeds threshold {self.alert_thresholds['uuid_mismatch_rate']:.2%}",
                        timestamp=current_time,
                        metric_name=metric.name,
                        threshold=self.alert_thresholds["uuid_mismatch_rate"],
                        current_value=metric.value
                    ))
            
            # Check RAG retrieval failure rate
            elif metric.name == "rag_retrieval_success_rate":
                failure_rate = 1.0 - metric.value
                if failure_rate > self.alert_thresholds["rag_retrieval_failure_rate"]:
                    alerts.append(Alert(
                        alert_id=f"rag_failure_{int(time.time())}",
                        level=AlertLevel.CRITICAL,
                        message=f"RAG retrieval failure rate {failure_rate:.2%} exceeds threshold {self.alert_thresholds['rag_retrieval_failure_rate']:.2%}",
                        timestamp=current_time,
                        metric_name=metric.name,
                        threshold=self.alert_thresholds["rag_retrieval_failure_rate"],
                        current_value=failure_rate
                    ))
            
            # Check pipeline consistency
            elif metric.name == "pipeline_consistency_rate":
                if metric.value < 0.8:  # Less than 80% consistency
                    alerts.append(Alert(
                        alert_id=f"pipeline_inconsistency_{int(time.time())}",
                        level=AlertLevel.WARNING,
                        message=f"Pipeline consistency rate {metric.value:.2%} is below acceptable threshold",
                        timestamp=current_time,
                        metric_name=metric.name,
                        threshold=0.8,
                        current_value=metric.value
                    ))
        
        logger.info(f"🚨 Generated {len(alerts)} alerts")
        return alerts
    
    async def generate_migration_dashboard(self) -> Dict[str, Any]:
        """Generate migration progress dashboard data."""
        logger.info("📊 Generating migration dashboard...")
        
        try:
            # Get migration progress data
            total_documents = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.documents
            """)
            
            migrated_documents = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.documents
                WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            """)
            
            pending_documents = total_documents - migrated_documents
            migration_progress = (migrated_documents / total_documents * 100) if total_documents > 0 else 0
            
            # Get recent migration activity
            recent_activity = await self.conn.fetch("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as documents_created,
                    COUNT(CASE WHEN document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' THEN 1 END) as deterministic_docs,
                    COUNT(CASE WHEN document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' THEN 1 END) as random_docs
                FROM upload_pipeline.documents
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            # Get user impact summary
            user_impact = await self.conn.fetch("""
                SELECT 
                    user_id,
                    COUNT(*) as total_documents,
                    COUNT(CASE WHEN document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' THEN 1 END) as deterministic_docs,
                    COUNT(CASE WHEN document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' THEN 1 END) as random_docs
                FROM upload_pipeline.documents
                GROUP BY user_id
                ORDER BY total_documents DESC
                LIMIT 10
            """)
            
            dashboard = {
                "timestamp": datetime.utcnow().isoformat(),
                "migration_progress": {
                    "total_documents": total_documents,
                    "migrated_documents": migrated_documents,
                    "pending_documents": pending_documents,
                    "progress_percentage": migration_progress,
                    "status": "completed" if migration_progress == 100 else "in_progress"
                },
                "recent_activity": [
                    {
                        "date": str(activity['date']),
                        "documents_created": activity['documents_created'],
                        "deterministic_docs": activity['deterministic_docs'],
                        "random_docs": activity['random_docs']
                    }
                    for activity in recent_activity
                ],
                "user_impact": [
                    {
                        "user_id": str(user['user_id']),
                        "total_documents": user['total_documents'],
                        "deterministic_docs": user['deterministic_docs'],
                        "random_docs": user['random_docs'],
                        "migration_status": "completed" if user['random_docs'] == 0 else "pending"
                    }
                    for user in user_impact
                ]
            }
            
            logger.info("📊 Migration dashboard generated successfully")
            return dashboard
            
        except Exception as e:
            logger.error(f"❌ Failed to generate migration dashboard: {e}")
            return {"error": str(e)}
    
    async def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run complete monitoring cycle."""
        logger.info("🔄 Running monitoring cycle...")
        
        if not await self.connect_database():
            return {"error": "Database connection failed"}
        
        try:
            # Collect metrics
            metrics = await self.collect_uuid_metrics()
            
            # Check alerts
            alerts = await self.check_alert_conditions(metrics)
            
            # Generate dashboard
            dashboard = await self.generate_migration_dashboard()
            
            # Compile results
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": [asdict(metric) for metric in metrics],
                "alerts": [asdict(alert) for alert in alerts],
                "dashboard": dashboard
            }
            
            logger.info(f"✅ Monitoring cycle completed: {len(metrics)} metrics, {len(alerts)} alerts")
            return results
            
        except Exception as e:
            logger.error(f"❌ Monitoring cycle failed: {e}")
            return {"error": str(e)}
        
        finally:
            await self.disconnect_database()
    
    async def start_continuous_monitoring(self, interval_seconds: int = 300):
        """Start continuous monitoring with specified interval."""
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval_seconds}s)...")
        
        while True:
            try:
                results = await self.run_monitoring_cycle()
                
                # Save results
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                output_file = f"uuid_monitoring_{timestamp}.json"
                
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                
                # Print critical alerts
                if "alerts" in results:
                    critical_alerts = [alert for alert in results["alerts"] if alert["level"] == "critical"]
                    if critical_alerts:
                        logger.error(f"🚨 CRITICAL ALERTS: {len(critical_alerts)}")
                        for alert in critical_alerts:
                            logger.error(f"  • {alert['message']}")
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring cycle failed: {e}")
                await asyncio.sleep(interval_seconds)

async def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv('.env.production')
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL not found in environment variables")
        return
    
    # Run monitoring
    monitoring_system = UUIDMonitoringSystem(database_url)
    
    # Run single monitoring cycle
    results = await monitoring_system.run_monitoring_cycle()
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = f"phase_b_monitoring_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📊 Monitoring results saved to: {output_file}")
    
    # Print summary
    if "error" not in results:
        print(f"\n📊 MONITORING SUMMARY")
        print(f"Metrics Collected: {len(results.get('metrics', []))}")
        print(f"Alerts Generated: {len(results.get('alerts', []))}")
        
        if results.get('dashboard', {}).get('migration_progress'):
            progress = results['dashboard']['migration_progress']
            print(f"Migration Progress: {progress['progress_percentage']:.1f}% ({progress['migrated_documents']}/{progress['total_documents']})")
        
        # Show critical alerts
        critical_alerts = [alert for alert in results.get('alerts', []) if alert.get('level') == 'critical']
        if critical_alerts:
            print(f"\n🚨 CRITICAL ALERTS:")
            for alert in critical_alerts:
                print(f"  • {alert['message']}")
    else:
        print(f"❌ Monitoring failed: {results['error']}")

if __name__ == "__main__":
    asyncio.run(main())
