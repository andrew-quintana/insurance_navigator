#!/usr/bin/env python3
"""
FM-027 Monitoring System

This module provides comprehensive monitoring for the FM-027 storage access issue,
including metrics collection, alerting, and health checks.
"""

import asyncio
import httpx
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import json
import os

logger = logging.getLogger(__name__)

class FM027Monitor:
    """
    Monitoring system for FM-027 storage access issues.
    """
    
    def __init__(self, base_url: str, service_role_key: str, test_file_path: str):
        self.base_url = base_url
        self.service_role_key = service_role_key
        self.test_file_path = test_file_path
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'network_path_success_rates': {},
            'cf_ray_distribution': {},
            'response_time_stats': [],
            'last_success_time': None,
            'last_failure_time': None,
            'consecutive_failures': 0,
            'max_consecutive_failures': 0
        }
        
    async def test_storage_access(self) -> Dict:
        """Test storage access and collect metrics."""
        url = f'{self.base_url}/storage/v1/object/{self.test_file_path}'
        headers = {
            'apikey': self.service_role_key,
            'authorization': f'Bearer {self.service_role_key}',
            'accept': '*/*',
            'user-agent': 'python-httpx/0.28.1'
        }
        
        start_time = time.time()
        self.metrics['total_requests'] += 1
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                end_time = time.time()
                
                response_time = end_time - start_time
                self.metrics['response_time_stats'].append(response_time)
                
                # Keep only last 100 response times
                if len(self.metrics['response_time_stats']) > 100:
                    self.metrics['response_time_stats'] = self.metrics['response_time_stats'][-100:]
                
                success = response.status_code == 200
                
                if success:
                    self.metrics['successful_requests'] += 1
                    self.metrics['consecutive_failures'] = 0
                    self.metrics['last_success_time'] = datetime.now(timezone.utc).isoformat()
                else:
                    self.metrics['failed_requests'] += 1
                    self.metrics['consecutive_failures'] += 1
                    self.metrics['max_consecutive_failures'] = max(
                        self.metrics['max_consecutive_failures'],
                        self.metrics['consecutive_failures']
                    )
                    self.metrics['last_failure_time'] = datetime.now(timezone.utc).isoformat()
                
                # Track CF-Ray distribution
                cf_ray = response.headers.get('cf-ray', 'N/A')
                if cf_ray not in self.metrics['cf_ray_distribution']:
                    self.metrics['cf_ray_distribution'][cf_ray] = 0
                self.metrics['cf_ray_distribution'][cf_ray] += 1
                
                result = {
                    'success': success,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'cf_ray': cf_ray,
                    'cache_status': response.headers.get('cf-cache-status', 'N/A'),
                    'server': response.headers.get('server', 'N/A'),
                    'content_length': len(response.content) if success else 0,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"FM-027 Monitor: Test result - {response.status_code} - {response_time:.3f}s - CF-Ray: {cf_ray}")
                
                return result
                
        except Exception as e:
            self.metrics['failed_requests'] += 1
            self.metrics['consecutive_failures'] += 1
            self.metrics['max_consecutive_failures'] = max(
                self.metrics['max_consecutive_failures'],
                self.metrics['consecutive_failures']
            )
            self.metrics['last_failure_time'] = datetime.now(timezone.utc).isoformat()
            
            logger.error(f"FM-027 Monitor: Test failed with exception - {e}")
            
            return {
                'success': False,
                'status_code': 0,
                'response_time': 0,
                'cf_ray': 'N/A',
                'cache_status': 'N/A',
                'server': 'N/A',
                'content_length': 0,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_health_status(self) -> Dict:
        """Get current health status."""
        total_requests = self.metrics['total_requests']
        success_rate = (self.metrics['successful_requests'] / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate response time statistics
        response_times = self.metrics['response_time_stats']
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # Determine health status
        if success_rate >= 95 and self.metrics['consecutive_failures'] < 3:
            health_status = 'healthy'
        elif success_rate >= 80 and self.metrics['consecutive_failures'] < 5:
            health_status = 'degraded'
        else:
            health_status = 'unhealthy'
        
        return {
            'health_status': health_status,
            'success_rate': success_rate,
            'total_requests': total_requests,
            'successful_requests': self.metrics['successful_requests'],
            'failed_requests': self.metrics['failed_requests'],
            'consecutive_failures': self.metrics['consecutive_failures'],
            'max_consecutive_failures': self.metrics['max_consecutive_failures'],
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'min_response_time': min_response_time,
            'last_success_time': self.metrics['last_success_time'],
            'last_failure_time': self.metrics['last_failure_time'],
            'cf_ray_distribution': self.metrics['cf_ray_distribution']
        }
    
    def get_metrics_summary(self) -> Dict:
        """Get a summary of all metrics."""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metrics': self.metrics,
            'health_status': self.get_health_status()
        }
    
    async def run_continuous_monitoring(self, interval_seconds: int = 60):
        """Run continuous monitoring with specified interval."""
        logger.info(f"FM-027 Monitor: Starting continuous monitoring with {interval_seconds}s interval")
        
        while True:
            try:
                result = await self.test_storage_access()
                health = self.get_health_status()
                
                # Log health status
                if health['health_status'] == 'unhealthy':
                    logger.error(f"FM-027 Monitor: UNHEALTHY - {health}")
                elif health['health_status'] == 'degraded':
                    logger.warning(f"FM-027 Monitor: DEGRADED - {health}")
                else:
                    logger.info(f"FM-027 Monitor: HEALTHY - Success rate: {health['success_rate']:.1f}%")
                
                # Save metrics to file for external monitoring
                await self._save_metrics_to_file()
                
            except Exception as e:
                logger.error(f"FM-027 Monitor: Error in continuous monitoring - {e}")
            
            await asyncio.sleep(interval_seconds)
    
    async def _save_metrics_to_file(self):
        """Save metrics to file for external monitoring systems."""
        try:
            metrics_file = '/tmp/fm027_metrics.json'
            with open(metrics_file, 'w') as f:
                json.dump(self.get_metrics_summary(), f, indent=2)
        except Exception as e:
            logger.error(f"FM-027 Monitor: Failed to save metrics to file - {e}")

# Health check endpoint for external monitoring
async def fm027_health_check(base_url: str, service_role_key: str, test_file_path: str) -> Dict:
    """Health check function for external monitoring systems."""
    monitor = FM027Monitor(base_url, service_role_key, test_file_path)
    result = await monitor.test_storage_access()
    health = monitor.get_health_status()
    
    return {
        'status': 'healthy' if health['health_status'] == 'healthy' else 'unhealthy',
        'details': health,
        'last_test': result
    }
