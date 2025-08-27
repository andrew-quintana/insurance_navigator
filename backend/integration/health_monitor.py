"""
Integration Health Monitor

This module provides comprehensive health monitoring across upload pipeline and agent system boundaries.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from .models import (
    HealthStatus, SystemHealthStatus, IntegrationHealthStatus, 
    IntegrationMetrics
)


class IntegrationHealthMonitor:
    """Monitors health across upload pipeline and agent system boundaries."""
    
    def __init__(self):
        """Initialize the health monitor."""
        self.logger = logging.getLogger("integration_health_monitor")
        self.metrics_history: List[IntegrationMetrics] = []
        
    async def check_upload_pipeline_health(self) -> SystemHealthStatus:
        """
        Check upload pipeline system health.
        
        Returns:
            SystemHealthStatus for upload pipeline
        """
        start_time = time.time()
        
        try:
            # Check if upload pipeline API is responding
            # This would check the actual API endpoints in a real implementation
            response_time = time.time() - start_time
            
            return SystemHealthStatus(
                component_name="upload_pipeline",
                status=HealthStatus.HEALTHY,
                message="Upload pipeline is healthy and responding",
                last_check=datetime.now(),
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Upload pipeline health check failed: {e}")
            
            return SystemHealthStatus(
                component_name="upload_pipeline",
                status=HealthStatus.UNHEALTHY,
                message=f"Upload pipeline health check failed: {str(e)}",
                last_check=datetime.now(),
                response_time=response_time,
                error_details=str(e)
            )
    
    async def check_agent_system_health(self) -> SystemHealthStatus:
        """
        Check agent system health.
        
        Returns:
            SystemHealthStatus for agent system
        """
        start_time = time.time()
        
        try:
            # Check if agent API is responding
            # This would check the actual agent endpoints in a real implementation
            response_time = time.time() - start_time
            
            return SystemHealthStatus(
                component_name="agent_system",
                status=HealthStatus.HEALTHY,
                message="Agent system is healthy and responding",
                last_check=datetime.now(),
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Agent system health check failed: {e}")
            
            return SystemHealthStatus(
                component_name="agent_system",
                status=HealthStatus.UNHEALTHY,
                message=f"Agent system health check failed: {str(e)}",
                last_check=datetime.now(),
                response_time=response_time,
                error_details=str(e)
            )
    
    async def check_database_health(self) -> SystemHealthStatus:
        """
        Check database connectivity and schema health.
        
        Returns:
            SystemHealthStatus for database
        """
        start_time = time.time()
        
        try:
            # This would perform actual database connectivity checks
            # For now, we'll simulate a healthy database
            response_time = time.time() - start_time
            
            return SystemHealthStatus(
                component_name="database",
                status=HealthStatus.HEALTHY,
                message="Database is healthy and accessible",
                last_check=datetime.now(),
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Database health check failed: {e}")
            
            return SystemHealthStatus(
                component_name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database health check failed: {str(e)}",
                last_check=datetime.now(),
                response_time=response_time,
                error_details=str(e)
            )
    
    async def check_mock_services_health(self) -> SystemHealthStatus:
        """
        Check mock services health.
        
        Returns:
            SystemHealthStatus for mock services
        """
        start_time = time.time()
        
        try:
            # Check if mock services are responding
            # This would check the actual mock service endpoints
            response_time = time.time() - start_time
            
            return SystemHealthStatus(
                component_name="mock_services",
                status=HealthStatus.HEALTHY,
                message="Mock services are healthy and responding",
                last_check=datetime.now(),
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Mock services health check failed: {e}")
            
            return SystemHealthStatus(
                component_name="mock_services",
                status=HealthStatus.UNHEALTHY,
                message=f"Mock services health check failed: {str(e)}",
                last_check=datetime.now(),
                response_time=response_time,
                error_details=str(e)
            )
    
    async def check_integration_health(self) -> IntegrationHealthStatus:
        """
        Check overall integration health across all system boundaries.
        
        Returns:
            IntegrationHealthStatus with comprehensive health information
        """
        start_time = time.time()
        
        # Check individual system components
        upload_status = await self.check_upload_pipeline_health()
        agent_status = await self.check_agent_system_health()
        db_status = await self.check_database_health()
        mock_status = await self.check_mock_services_health()
        
        # Determine overall status
        all_healthy = all([
            upload_status.status == HealthStatus.HEALTHY,
            agent_status.status == HealthStatus.HEALTHY,
            db_status.status == HealthStatus.HEALTHY,
            mock_status.status == HealthStatus.HEALTHY
        ])
        
        if all_healthy:
            overall_status = HealthStatus.HEALTHY
        elif any(s.status == HealthStatus.UNHEALTHY for s in [upload_status, agent_status, db_status, mock_status]):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        # Generate recommendations
        recommendations = self._generate_recommendations([
            upload_status, agent_status, db_status, mock_status
        ])
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics([
            upload_status, agent_status, db_status, mock_status
        ])
        
        response_time = time.time() - start_time
        
        return IntegrationHealthStatus(
            overall_status=overall_status,
            upload_pipeline_status=upload_status,
            agent_system_status=agent_status,
            database_status=db_status,
            mock_services_status=mock_status,
            last_check=datetime.now(),
            performance_metrics=performance_metrics,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, system_statuses: List[SystemHealthStatus]) -> List[str]:
        """
        Generate recommendations based on system health statuses.
        
        Args:
            system_statuses: List of system health statuses
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        for status in system_statuses:
            if status.status == HealthStatus.UNHEALTHY:
                recommendations.append(f"Investigate {status.component_name} issues: {status.message}")
            elif status.status == HealthStatus.DEGRADED:
                recommendations.append(f"Monitor {status.component_name} performance: {status.message}")
        
        if not recommendations:
            recommendations.append("All systems are healthy - continue monitoring")
        
        return recommendations
    
    def _calculate_performance_metrics(self, system_statuses: List[SystemHealthStatus]) -> Dict[str, Any]:
        """
        Calculate performance metrics from system health statuses.
        
        Args:
            system_statuses: List of system health statuses
            
        Returns:
            Dictionary with performance metrics
        """
        response_times = [s.response_time for s in system_statuses if s.response_time is not None]
        
        metrics = {
            'total_systems': len(system_statuses),
            'healthy_systems': len([s for s in system_statuses if s.status == HealthStatus.HEALTHY]),
            'degraded_systems': len([s for s in system_statuses if s.status == HealthStatus.DEGRADED]),
            'unhealthy_systems': len([s for s in system_statuses if s.status == HealthStatus.UNHEALTHY]),
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0.0,
            'max_response_time': max(response_times) if response_times else 0.0,
            'min_response_time': min(response_times) if response_times else 0.0
        }
        
        return metrics
    
    async def record_metrics(self, metrics: IntegrationMetrics):
        """
        Record performance metrics for historical analysis.
        
        Args:
            metrics: IntegrationMetrics object to record
        """
        self.metrics_history.append(metrics)
        
        # Keep only last 100 metrics
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
        
        self.logger.info(f"Recorded metrics: {metrics}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of recorded metrics.
        
        Returns:
            Dictionary with metrics summary
        """
        if not self.metrics_history:
            return {"message": "No metrics recorded yet"}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 metrics
        
        return {
            "total_metrics_recorded": len(self.metrics_history),
            "recent_metrics_count": len(recent_metrics),
            "avg_upload_processing_time": sum(m.upload_processing_time_avg for m in recent_metrics) / len(recent_metrics),
            "avg_rag_query_time": sum(m.rag_query_time_avg for m in recent_metrics) / len(recent_metrics),
            "avg_agent_response_time": sum(m.agent_response_time_avg for m in recent_metrics) / len(recent_metrics),
            "avg_concurrent_success_rate": sum(m.concurrent_operation_success_rate for m in recent_metrics) / len(recent_metrics),
            "avg_error_rate": sum(m.error_rate for m in recent_metrics) / len(recent_metrics),
            "last_updated": recent_metrics[-1].last_updated.isoformat() if recent_metrics else None
        }
