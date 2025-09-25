"""
Phase 2 Cloud Performance Monitor

This module implements comprehensive performance monitoring for cloud deployment,
tracking response times, database performance, and comparing against local baselines.

Based on RFC001.md interface contracts and Phase 1 foundation.
"""

import asyncio
import aiohttp
import json
import time
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    query_times: Dict[str, float]
    connection_pool: Dict[str, int]
    throughput: float
    error_rate: float
    avg_response_time: float

@dataclass
class PerformanceBaseline:
    """Performance baseline from local integration"""
    target_metrics: Dict[str, float]
    thresholds: Dict[str, float]
    local_integration_data: Dict[str, Any]

@dataclass
class PerformanceSnapshot:
    """Snapshot of current performance metrics"""
    timestamp: datetime
    response_times: Dict[str, float]
    database_metrics: DatabaseMetrics
    baseline_comparison: Dict[str, Any]
    alerts: List[str]

class CloudPerformanceMonitor:
    """
    Monitors performance metrics in cloud environment
    
    Implements RFC001.md interface contracts for Phase 2 performance monitoring
    """
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """Initialize the performance monitor"""
        self.config = config or self._load_default_config()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Performance baselines from local integration (003/integration/001)
        self.baseline = PerformanceBaseline(
            target_metrics={
                "average_response_time": 322.2,  # ms from Artillery.js testing
                "processing_success_rate": 100.0,  # %
                "load_test_requests": 4814,  # requests handled successfully
                "concurrent_users": 50,  # users supported
                "database_query_time": 200.0,  # ms for simple queries
                "database_connection_time": 100.0,  # ms
                "frontend_load_time": 3000.0,  # ms
                "api_response_time": 2000.0  # ms
            },
            thresholds={
                "error_rate_threshold": 1.0,  # % maximum acceptable
                "response_time_degradation": 1.5,  # 50% degradation threshold
                "database_timeout": 500.0,  # ms
                "connection_pool_utilization": 80.0  # % maximum
            },
            local_integration_data={
                "artillery_test_results": {
                    "total_requests": 4814,
                    "successful_requests": 4814,
                    "failed_requests": 0,
                    "average_response_time": 322.2,
                    "min_response_time": 150.0,
                    "max_response_time": 800.0,
                    "p95_response_time": 450.0,
                    "p99_response_time": 600.0
                },
                "cross_browser_compatibility": {
                    "chrome": 100.0,
                    "firefox": 100.0,
                    "safari": 100.0
                },
                "real_system_integration": {
                    "llamaparse_success_rate": 100.0,
                    "openai_success_rate": 100.0,
                    "document_processing_success": 100.0
                }
            }
        )
        
        # Performance tracking
        self.performance_history: List[PerformanceSnapshot] = []
        self.alert_thresholds = {
            "response_time_alert": 1000.0,  # ms
            "error_rate_alert": 5.0,  # %
            "database_timeout_alert": 1000.0,  # ms
            "connection_pool_alert": 90.0  # %
        }
    
    def _load_default_config(self) -> Dict[str, str]:
        """Load default configuration for cloud services"""
        return {
            "vercel_url": "https://insurance-navigator.vercel.app",
            "api_url": "https://insurance-navigator-api.onrender.com",
            "worker_url": "https://insurance-navigator-worker.onrender.com",
            "supabase_url": "https://znvwzkdblknkkztqyfnu.supabase.co"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=50)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def monitor_response_times(self) -> Dict[str, float]:
        """
        Monitor API response times
        
        Returns:
            Dict mapping endpoint to average response time in ms
        """
        logger.info("Monitoring response times across all endpoints")
        
        endpoints = {
            "frontend": self.config['vercel_url'],
            "api_health": f"{self.config['api_url']}/health",
            "api_upload": f"{self.config['api_url']}/api/upload-pipeline/upload",
            "api_chat": f"{self.config['api_url']}/chat",
            "supabase_auth": f"{self.config['supabase_url']}/auth/v1/health",
            "supabase_db": f"{self.config['supabase_url']}/rest/v1/"
        }
        
        response_times = {}
        
        for name, url in endpoints.items():
            try:
                start_time = time.time()
                
                async with self.session.get(url, timeout=10) as response:
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    response_times[name] = response_time
                    
                    logger.debug(f"{name}: {response_time:.2f}ms (HTTP {response.status})")
                    
            except asyncio.TimeoutError:
                response_times[name] = 10000.0  # 10 second timeout
                logger.warning(f"{name}: Timeout (>10s)")
            except Exception as e:
                response_times[name] = -1.0  # Error indicator
                logger.error(f"{name}: Error - {e}")
        
        return response_times
    
    async def monitor_database_performance(self) -> DatabaseMetrics:
        """
        Monitor database performance
        
        Returns:
            DatabaseMetrics with query performance and connection details
        """
        logger.info("Monitoring database performance")
        
        try:
            # Test database connectivity and query performance
            query_times = {}
            connection_pool = {"active": 0, "idle": 0, "total": 0}
            error_rate = 0.0
            throughput = 0.0
            
            # Test 1: Simple health check query
            start_time = time.time()
            async with self.session.get(
                f"{self.config['supabase_url']}/rest/v1/",
                headers={"apikey": "test_key"},
                timeout=5
            ) as response:
                query_times["health_check"] = (time.time() - start_time) * 1000
                if response.status >= 400:
                    error_rate += 1.0
            
            # Test 2: Authentication service performance
            start_time = time.time()
            async with self.session.get(
                f"{self.config['supabase_url']}/auth/v1/health",
                timeout=5
            ) as response:
                query_times["auth_service"] = (time.time() - start_time) * 1000
                if response.status >= 400:
                    error_rate += 1.0
            
            # Test 3: Storage service performance
            start_time = time.time()
            async with self.session.get(
                f"{self.config['supabase_url']}/storage/v1/",
                headers={"apikey": "test_key"},
                timeout=5
            ) as response:
                query_times["storage_service"] = (time.time() - start_time) * 1000
                if response.status >= 400:
                    error_rate += 1.0
            
            # Calculate average response time
            avg_response_time = statistics.mean(query_times.values()) if query_times else 0.0
            
            # Calculate throughput (requests per second)
            total_time = sum(query_times.values()) / 1000  # Convert to seconds
            throughput = len(query_times) / total_time if total_time > 0 else 0.0
            
            # Calculate error rate
            error_rate = (error_rate / len(query_times)) * 100 if query_times else 0.0
            
            return DatabaseMetrics(
                query_times=query_times,
                connection_pool=connection_pool,
                throughput=throughput,
                error_rate=error_rate,
                avg_response_time=avg_response_time
            )
            
        except Exception as e:
            logger.error(f"Database performance monitoring failed: {e}")
            return DatabaseMetrics(
                query_times={},
                connection_pool={"active": 0, "idle": 0, "total": 0},
                throughput=0.0,
                error_rate=100.0,
                avg_response_time=0.0
            )
    
    async def get_performance_baseline(self) -> PerformanceBaseline:
        """
        Get performance baseline from local integration
        
        Returns:
            PerformanceBaseline with target metrics and thresholds
        """
        logger.info("Retrieving performance baseline from local integration")
        
        # The baseline is already set in __init__, but we can enhance it with current data
        current_metrics = await self.monitor_response_times()
        current_db_metrics = await self.monitor_database_performance()
        
        # Update baseline with current cloud performance for comparison
        enhanced_baseline = PerformanceBaseline(
            target_metrics=self.baseline.target_metrics.copy(),
            thresholds=self.baseline.thresholds.copy(),
            local_integration_data=self.baseline.local_integration_data.copy()
        )
        
        # Add current cloud performance for comparison
        enhanced_baseline.local_integration_data["current_cloud_performance"] = {
            "response_times": current_metrics,
            "database_metrics": asdict(current_db_metrics),
            "timestamp": datetime.now().isoformat()
        }
        
        return enhanced_baseline
    
    async def take_performance_snapshot(self) -> PerformanceSnapshot:
        """
        Take a comprehensive performance snapshot
        
        Returns:
            PerformanceSnapshot with current performance metrics
        """
        logger.info("Taking performance snapshot")
        
        # Collect current metrics
        response_times = await self.monitor_response_times()
        database_metrics = await self.monitor_database_performance()
        
        # Compare with baseline
        baseline_comparison = self._compare_with_baseline(response_times, database_metrics)
        
        # Check for alerts
        alerts = self._check_performance_alerts(response_times, database_metrics)
        
        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(),
            response_times=response_times,
            database_metrics=database_metrics,
            baseline_comparison=baseline_comparison,
            alerts=alerts
        )
        
        # Store in history
        self.performance_history.append(snapshot)
        
        # Keep only last 100 snapshots
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        return snapshot
    
    async def monitor_performance_trends(self, duration_minutes: int = 10) -> Dict[str, Any]:
        """
        Monitor performance trends over time
        
        Args:
            duration_minutes: Duration to analyze trends
            
        Returns:
            Dict with trend analysis
        """
        logger.info(f"Analyzing performance trends over {duration_minutes} minutes")
        
        # Take current snapshot
        current_snapshot = await self.take_performance_snapshot()
        
        # Filter history for the specified duration
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_snapshots = [
            s for s in self.performance_history 
            if s.timestamp >= cutoff_time
        ]
        
        if len(recent_snapshots) < 2:
            return {
                "trend_analysis": "insufficient_data",
                "snapshots_analyzed": len(recent_snapshots),
                "duration_minutes": duration_minutes
            }
        
        # Analyze trends
        response_time_trends = {}
        database_trends = {}
        
        # Response time trends
        for endpoint in recent_snapshots[0].response_times.keys():
            times = [s.response_times.get(endpoint, 0) for s in recent_snapshots]
            if times:
                response_time_trends[endpoint] = {
                    "min": min(times),
                    "max": max(times),
                    "avg": statistics.mean(times),
                    "trend": "improving" if times[-1] < times[0] else "degrading"
                }
        
        # Database trends
        db_times = [s.database_metrics.avg_response_time for s in recent_snapshots]
        if db_times:
            database_trends = {
                "min": min(db_times),
                "max": max(db_times),
                "avg": statistics.mean(db_times),
                "trend": "improving" if db_times[-1] < db_times[0] else "degrading"
            }
        
        return {
            "trend_analysis": "completed",
            "snapshots_analyzed": len(recent_snapshots),
            "duration_minutes": duration_minutes,
            "response_time_trends": response_time_trends,
            "database_trends": database_trends,
            "overall_trend": "stable",  # Could be calculated based on trends
            "alerts_generated": len(current_snapshot.alerts)
        }
    
    def _compare_with_baseline(self, response_times: Dict[str, float], 
                             database_metrics: DatabaseMetrics) -> Dict[str, Any]:
        """Compare current performance with baseline"""
        
        comparison = {
            "response_time_comparison": {},
            "database_comparison": {},
            "overall_performance": "unknown"
        }
        
        # Compare response times
        baseline_response_time = self.baseline.target_metrics["average_response_time"]
        current_avg_response_time = statistics.mean(response_times.values()) if response_times else 0
        
        comparison["response_time_comparison"] = {
            "baseline": baseline_response_time,
            "current": current_avg_response_time,
            "ratio": current_avg_response_time / baseline_response_time if baseline_response_time > 0 else 0,
            "status": "within_baseline" if current_avg_response_time <= baseline_response_time * 1.5 else "degraded"
        }
        
        # Compare database performance
        baseline_db_time = self.baseline.target_metrics["database_query_time"]
        current_db_time = database_metrics.avg_response_time
        
        comparison["database_comparison"] = {
            "baseline": baseline_db_time,
            "current": current_db_time,
            "ratio": current_db_time / baseline_db_time if baseline_db_time > 0 else 0,
            "status": "within_baseline" if current_db_time <= baseline_db_time * 1.5 else "degraded"
        }
        
        # Overall performance assessment
        response_ok = comparison["response_time_comparison"]["status"] == "within_baseline"
        db_ok = comparison["database_comparison"]["status"] == "within_baseline"
        error_ok = database_metrics.error_rate <= self.baseline.thresholds["error_rate_threshold"]
        
        if response_ok and db_ok and error_ok:
            comparison["overall_performance"] = "excellent"
        elif response_ok and db_ok:
            comparison["overall_performance"] = "good"
        elif response_ok or db_ok:
            comparison["overall_performance"] = "acceptable"
        else:
            comparison["overall_performance"] = "poor"
        
        return comparison
    
    def _check_performance_alerts(self, response_times: Dict[str, float], 
                                database_metrics: DatabaseMetrics) -> List[str]:
        """Check for performance alerts"""
        
        alerts = []
        
        # Response time alerts
        for endpoint, response_time in response_times.items():
            if response_time > self.alert_thresholds["response_time_alert"]:
                alerts.append(f"High response time for {endpoint}: {response_time:.2f}ms")
        
        # Error rate alerts
        if database_metrics.error_rate > self.alert_thresholds["error_rate_alert"]:
            alerts.append(f"High error rate: {database_metrics.error_rate:.2f}%")
        
        # Database timeout alerts
        if database_metrics.avg_response_time > self.alert_thresholds["database_timeout_alert"]:
            alerts.append(f"Database timeout: {database_metrics.avg_response_time:.2f}ms")
        
        return alerts
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Returns:
            Dict with complete performance analysis
        """
        logger.info("Generating comprehensive performance report")
        
        # Take current snapshot
        snapshot = await self.take_performance_snapshot()
        
        # Get baseline
        baseline = await self.get_performance_baseline()
        
        # Analyze trends
        trends = await self.monitor_performance_trends()
        
        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "snapshot": asdict(snapshot),
            "baseline": asdict(baseline),
            "trends": trends,
            "summary": {
                "overall_performance": snapshot.baseline_comparison["overall_performance"],
                "alerts_count": len(snapshot.alerts),
                "baseline_compliance": snapshot.baseline_comparison["response_time_comparison"]["status"],
                "database_performance": snapshot.baseline_comparison["database_comparison"]["status"],
                "recommendations": self._generate_recommendations(snapshot)
            }
        }
        
        return report
    
    def _generate_recommendations(self, snapshot: PerformanceSnapshot) -> List[str]:
        """Generate performance recommendations"""
        
        recommendations = []
        
        # Response time recommendations
        response_comparison = snapshot.baseline_comparison["response_time_comparison"]
        if response_comparison["status"] == "degraded":
            recommendations.append("Consider optimizing API response times - current performance is degraded compared to baseline")
        
        # Database recommendations
        db_comparison = snapshot.baseline_comparison["database_comparison"]
        if db_comparison["status"] == "degraded":
            recommendations.append("Database performance is degraded - consider query optimization or connection pooling")
        
        # Error rate recommendations
        if snapshot.database_metrics.error_rate > 1.0:
            recommendations.append("Error rate is elevated - investigate and resolve underlying issues")
        
        # Alert-based recommendations
        for alert in snapshot.alerts:
            if "response time" in alert.lower():
                recommendations.append("High response times detected - consider scaling or optimization")
            elif "error rate" in alert.lower():
                recommendations.append("High error rates detected - investigate service health")
            elif "timeout" in alert.lower():
                recommendations.append("Timeout issues detected - check network connectivity and service health")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable parameters - continue monitoring")
        
        return recommendations

# Example usage and testing
async def main():
    """Example usage of the CloudPerformanceMonitor"""
    
    async with CloudPerformanceMonitor() as monitor:
        # Take a performance snapshot
        snapshot = await monitor.take_performance_snapshot()
        
        print(f"Performance Snapshot:")
        print(f"Timestamp: {snapshot.timestamp}")
        print(f"Overall Performance: {snapshot.baseline_comparison['overall_performance']}")
        print(f"Alerts: {len(snapshot.alerts)}")
        
        if snapshot.alerts:
            print("Alerts:")
            for alert in snapshot.alerts:
                print(f"  - {alert}")
        
        # Generate comprehensive report
        report = await monitor.generate_performance_report()
        
        # Save report
        report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Performance report saved to: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
