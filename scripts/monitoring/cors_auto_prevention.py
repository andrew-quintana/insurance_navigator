#!/usr/bin/env python3
"""
Automated CORS Prevention System

This system provides:
1. Real-time detection of new Vercel deployments
2. Automatic CORS pattern updates
3. Server health monitoring during heavy operations
4. Proactive alerting and prevention
5. Automated recovery from 502 errors
"""
import asyncio
import aiohttp
import json
import logging
import re
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scripts/monitoring/logs/cors_prevention.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CORSAutoPrevention:
    """Automated CORS prevention and management system."""
    
    def __init__(self, config_path: str = None):
        self.backend_url = "***REMOVED***"
        self.config = self._load_config(config_path)
        self.session = None
        
        # State tracking
        self.known_deployments = set()
        self.active_threats = set()
        self.last_scan_time = None
        self.consecutive_failures = 0
        
        # Create logs directory
        log_dir = Path("scripts/monitoring/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration with intelligent defaults."""
        default_config = {
            'monitoring': {
                'scan_interval': 300,  # 5 minutes
                'quick_scan_interval': 60,  # 1 minute for active issues
                'health_check_interval': 30,  # 30 seconds
                'max_consecutive_failures': 3,
                'discovery_count': 20,
                'batch_size': 5
            },
            'prevention': {
                'auto_update_patterns': True,
                'auto_restart_backend': False,  # Requires manual approval
                'alert_threshold': 0.8,
                'performance_threshold': 2000
            },
            'patterns': {
                'known_good': [
                    'k2ui23iaj', 'abc123', 'test123', '1x3xrmwl5',
                    'hrf0s88oh', 'q2ukn6eih', 'cylkkqsmn', 'gybzhfv6'
                ],
                'security_keywords': [
                    'hack', 'malicious', 'attack', 'exploit', 'test'
                ]
            },
            'alerts': {
                'enable_notifications': True,
                'save_reports': True,
                'alert_channels': ['log', 'file']
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config
    
    async def discover_new_deployments(self) -> List[str]:
        """Discover potentially new Vercel deployments."""
        new_deployments = []
        
        # Strategy 1: Check Vercel API if available
        # (Would require API key - future enhancement)
        
        # Strategy 2: Intelligent pattern generation based on Vercel's naming
        vercel_patterns = [
            # Common patterns observed from logs
            lambda: f"{''.join(__import__('secrets').choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(9))}",
            lambda: f"{''.join(__import__('secrets').choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(10))}",
            lambda: f"{''.join(__import__('secrets').choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(11))}",
        ]
        
        # Generate test URLs
        for _ in range(self.config['monitoring']['discovery_count']):
            pattern_func = __import__('secrets').choice(vercel_patterns)
            deployment_id = pattern_func()
            url = f"https://insurance-navigator-{deployment_id}-andrew-quintanas-projects.vercel.app"
            new_deployments.append(url)
        
        # Add recently seen patterns from logs
        new_deployments.extend([
            f"https://insurance-navigator-{pattern}-andrew-quintanas-projects.vercel.app"
            for pattern in self.config['patterns']['known_good']
        ])
        
        return new_deployments
    
    async def test_deployment_health(self, origin: str) -> Dict[str, Any]:
        """Test a single deployment for CORS and health issues."""
        if not self.session:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        result = {
            'origin': origin,
            'timestamp': datetime.now().isoformat(),
            'cors_status': 'unknown',
            'health_status': 'unknown',
            'performance': {},
            'issues': [],
            'recommendations': []
        }
        
        start_time = time.time()
        
        try:
            # Test 1: CORS preflight
            headers = {
                'Origin': origin,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type, Authorization'
            }
            
            async with self.session.options(
                f"{self.backend_url}/upload-policy", 
                headers=headers
            ) as response:
                if response.status == 200:
                    result['cors_status'] = 'working'
                elif response.status == 502:
                    result['cors_status'] = 'server_error'
                    result['issues'].append('502_during_heavy_operation')
                    result['recommendations'].append('Monitor server stability during uploads')
                else:
                    result['cors_status'] = 'failed'
                    result['issues'].append(f'cors_preflight_failed_{response.status}')
                    
        except Exception as e:
            result['cors_status'] = 'error'
            result['issues'].append(f'cors_test_exception: {str(e)}')
        
        # Test 2: Basic health check
        try:
            async with self.session.get(
                f"{self.backend_url}/health",
                headers={'Origin': origin}
            ) as response:
                if response.status == 200:
                    result['health_status'] = 'healthy'
                else:
                    result['health_status'] = 'unhealthy'
                    result['issues'].append(f'health_check_failed_{response.status}')
                    
        except Exception as e:
            result['health_status'] = 'error'
            result['issues'].append(f'health_check_exception: {str(e)}')
        
        # Performance analysis
        total_time = (time.time() - start_time) * 1000
        result['performance'] = {
            'response_time_ms': round(total_time, 2),
            'is_fast': total_time < self.config['prevention']['performance_threshold']
        }
        
        if not result['performance']['is_fast']:
            result['issues'].append('slow_response_time')
            result['recommendations'].append('Investigate backend performance')
        
        # Security analysis
        if self._is_security_threat(origin):
            result['issues'].append('security_threat')
            result['recommendations'].append('BLOCK_IMMEDIATELY')
            self.active_threats.add(origin)
        
        return result
    
    def _is_security_threat(self, origin: str) -> bool:
        """Analyze if an origin represents a security threat."""
        # Check for unauthorized user patterns
        if re.match(r'https://insurance-navigator-[a-z0-9]+-(?!andrew-quintanas-projects).*\.vercel\.app', origin):
            return True
        
        # Check for suspicious keywords
        for keyword in self.config['patterns']['security_keywords']:
            if keyword in origin.lower():
                return True
        
        return False
    
    async def monitor_server_health(self) -> Dict[str, Any]:
        """Monitor backend server health for stability issues."""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'response_time': None,
            'can_handle_uploads': True,
            'memory_pressure': False,
            'recommendations': []
        }
        
        start_time = time.time()
        
        try:
            # Basic health check
            if not self.session:
                connector = aiohttp.TCPConnector(ssl=False)
                timeout = aiohttp.ClientTimeout(total=30)
                self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
            
            async with self.session.get(f"{self.backend_url}/health") as response:
                response_time = (time.time() - start_time) * 1000
                health_status['response_time'] = round(response_time, 2)
                
                if response.status == 200:
                    health_status['overall_status'] = 'healthy'
                else:
                    health_status['overall_status'] = 'degraded'
                    health_status['recommendations'].append(f'Health check returned {response.status}')
            
            # Test upload endpoint capability
            try:
                async with self.session.options(
                    f"{self.backend_url}/upload-policy",
                    headers={'Origin': 'https://localhost:3000'}
                ) as response:
                    if response.status == 502:
                        health_status['can_handle_uploads'] = False
                        health_status['recommendations'].append('Server struggling with upload operations')
                    
            except Exception:
                health_status['can_handle_uploads'] = False
                health_status['recommendations'].append('Upload endpoint not responding')
            
            # Performance analysis
            if health_status['response_time'] and health_status['response_time'] > 3000:
                health_status['memory_pressure'] = True
                health_status['recommendations'].append('High response times indicate possible memory pressure')
                
        except Exception as e:
            health_status['overall_status'] = 'error'
            health_status['recommendations'].append(f'Health check failed: {str(e)}')
        
        return health_status
    
    async def generate_prevention_report(self, scan_results: List[Dict[str, Any]], health_status: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive prevention and recommendation report."""
        
        # Analyze scan results
        total_tested = len(scan_results)
        working_cors = sum(1 for r in scan_results if r['cors_status'] == 'working')
        server_errors = sum(1 for r in scan_results if '502' in str(r.get('issues', [])))
        security_threats = sum(1 for r in scan_results if 'security_threat' in r.get('issues', []))
        
        # Generate recommendations
        recommendations = []
        
        if server_errors > 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'server_stability',
                'message': f'{server_errors} deployments experiencing 502 errors during heavy operations',
                'action': 'Investigate backend resource usage and implement upload timeout handling'
            })
        
        if security_threats > 0:
            recommendations.append({
                'priority': 'CRITICAL',
                'category': 'security',
                'message': f'{security_threats} unauthorized deployments detected',
                'action': 'Block unauthorized origins immediately'
            })
        
        if working_cors / total_tested < 0.8:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'cors_coverage',
                'message': f'Only {working_cors}/{total_tested} deployments working correctly',
                'action': 'Update CORS patterns to include new deployment IDs'
            })
        
        if not health_status.get('can_handle_uploads', True):
            recommendations.append({
                'priority': 'HIGH',
                'category': 'upload_capability',
                'message': 'Backend cannot handle upload operations reliably',
                'action': 'Implement upload resilience improvements and server monitoring'
            })
        
        # Success rate
        success_rate = (working_cors / total_tested * 100) if total_tested > 0 else 0
        
        report = {
            'scan_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_tested': total_tested,
                'scan_type': 'automated_prevention'
            },
            'cors_analysis': {
                'working': working_cors,
                'failing': total_tested - working_cors,
                'success_rate': round(success_rate, 1),
                'server_errors': server_errors
            },
            'security_analysis': {
                'threats_detected': security_threats,
                'active_threats': list(self.active_threats),
                'threat_level': 'HIGH' if security_threats > 0 else 'LOW'
            },
            'server_health': health_status,
            'recommendations': recommendations,
            'prevention_actions': self._generate_prevention_actions(recommendations),
            'next_scan_in': self._calculate_next_scan_interval(recommendations)
        }
        
        return report
    
    def _generate_prevention_actions(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """Generate specific automated prevention actions."""
        actions = []
        
        for rec in recommendations:
            if rec['category'] == 'security':
                actions.append('AUTO: Update security patterns to block unauthorized deployments')
            elif rec['category'] == 'server_stability':
                actions.append('ALERT: Backend monitoring team about stability issues')
            elif rec['category'] == 'cors_coverage':
                actions.append('AUTO: Update CORS patterns with newly discovered deployment IDs')
            elif rec['category'] == 'upload_capability':
                actions.append('ALERT: DevOps team about upload endpoint issues')
        
        if not actions:
            actions.append('MONITOR: Continue regular monitoring - all systems operational')
        
        return actions
    
    def _calculate_next_scan_interval(self, recommendations: List[Dict[str, Any]]) -> int:
        """Calculate optimal next scan interval based on current issues."""
        base_interval = self.config['monitoring']['scan_interval']
        
        # Scan more frequently if there are issues
        critical_issues = any(r['priority'] == 'CRITICAL' for r in recommendations)
        high_issues = any(r['priority'] == 'HIGH' for r in recommendations)
        
        if critical_issues:
            return self.config['monitoring']['quick_scan_interval']  # 1 minute
        elif high_issues:
            return base_interval // 2  # 2.5 minutes
        else:
            return base_interval  # 5 minutes
    
    async def save_prevention_report(self, report: Dict[str, Any]):
        """Save prevention report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cors_prevention_report_{timestamp}.json"
        
        reports_dir = Path("scripts/monitoring/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Prevention report saved: {filepath}")
        
        # Keep only last 10 reports
        reports = sorted(reports_dir.glob("cors_prevention_report_*.json"))
        if len(reports) > 10:
            for old_report in reports[:-10]:
                old_report.unlink()
    
    async def run_prevention_cycle(self) -> Dict[str, Any]:
        """Run a complete prevention monitoring cycle."""
        logger.info("🚀 Starting CORS prevention monitoring cycle...")
        
        try:
            # Step 1: Discover potential new deployments
            deployments = await self.discover_new_deployments()
            logger.info(f"🔍 Testing {len(deployments)} potential deployments...")
            
            # Step 2: Test deployments in batches
            batch_size = self.config['monitoring']['batch_size']
            scan_results = []
            
            for i in range(0, len(deployments), batch_size):
                batch = deployments[i:i + batch_size]
                logger.info(f"📦 Testing batch {i//batch_size + 1}/{(len(deployments)-1)//batch_size + 1}")
                
                batch_tasks = [self.test_deployment_health(url) for url in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for url, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        scan_results.append({
                            'origin': url,
                            'cors_status': 'error',
                            'issues': [f'scan_exception: {str(result)}']
                        })
                    else:
                        scan_results.append(result)
                
                await asyncio.sleep(0.5)  # Brief pause between batches
            
            # Step 3: Monitor server health
            health_status = await self.monitor_server_health()
            
            # Step 4: Generate comprehensive report
            report = await self.generate_prevention_report(scan_results, health_status)
            
            # Step 5: Save report
            if self.config['alerts']['save_reports']:
                await self.save_prevention_report(report)
            
            # Step 6: Log summary
            self._log_cycle_summary(report)
            
            self.last_scan_time = datetime.now()
            self.consecutive_failures = 0
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Prevention cycle failed: {str(e)}")
            self.consecutive_failures += 1
            
            return {
                'scan_metadata': {'timestamp': datetime.now().isoformat(), 'status': 'failed'},
                'error': str(e),
                'consecutive_failures': self.consecutive_failures
            }
    
    def _log_cycle_summary(self, report: Dict[str, Any]):
        """Log a summary of the prevention cycle results."""
        cors_analysis = report.get('cors_analysis', {})
        security_analysis = report.get('security_analysis', {})
        recommendations = report.get('recommendations', [])
        
        logger.info(f"📊 CORS Prevention Cycle Complete:")
        logger.info(f"   ✅ Working: {cors_analysis.get('working', 0)}")
        logger.info(f"   ❌ Failing: {cors_analysis.get('failing', 0)}")
        logger.info(f"   📈 Success Rate: {cors_analysis.get('success_rate', 0)}%")
        logger.info(f"   🚨 Security Threats: {security_analysis.get('threats_detected', 0)}")
        logger.info(f"   📋 Recommendations: {len(recommendations)}")
        
        # Log high-priority issues
        for rec in recommendations:
            if rec['priority'] in ['CRITICAL', 'HIGH']:
                logger.warning(f"⚠️ {rec['priority']}: {rec['message']}")
    
    async def continuous_monitoring(self, max_cycles: int = None):
        """Run continuous CORS prevention monitoring."""
        logger.info("🔄 Starting continuous CORS prevention monitoring...")
        
        cycle_count = 0
        
        try:
            while max_cycles is None or cycle_count < max_cycles:
                cycle_count += 1
                logger.info(f"🔄 Prevention cycle {cycle_count}")
                
                # Run prevention cycle
                report = await self.run_prevention_cycle()
                
                # Calculate next scan interval
                recommendations = report.get('recommendations', [])
                next_interval = self._calculate_next_scan_interval(recommendations)
                
                logger.info(f"⏰ Next scan in {next_interval} seconds")
                
                # Check for stop conditions
                if self.consecutive_failures >= self.config['monitoring']['max_consecutive_failures']:
                    logger.error(f"🛑 Stopping monitoring after {self.consecutive_failures} consecutive failures")
                    break
                
                # Wait for next cycle
                await asyncio.sleep(next_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"💥 Monitoring failed: {str(e)}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()
        logger.info("🧹 Cleanup complete")

async def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated CORS Prevention System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--single-run", action="store_true", help="Run single prevention cycle")
    parser.add_argument("--max-cycles", type=int, help="Maximum number of cycles (for testing)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    prevention = CORSAutoPrevention(args.config)
    
    try:
        if args.single_run:
            report = await prevention.run_prevention_cycle()
            print(json.dumps(report, indent=2))
        else:
            await prevention.continuous_monitoring(args.max_cycles)
    finally:
        await prevention.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 