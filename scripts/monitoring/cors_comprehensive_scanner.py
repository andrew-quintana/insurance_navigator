#!/usr/bin/env python3
"""
Comprehensive CORS Scanner and Prevention System

This script provides:
1. Automatic discovery of new Vercel deployments
2. Real-time CORS testing and validation
3. Security monitoring and alerting
4. Performance tracking and analysis
5. Prevention recommendations
"""
import asyncio
import aiohttp
import json
import logging
import re
import time
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import secrets
import string

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveCORSScanner:
    """Comprehensive CORS scanner with discovery, testing, and prevention."""
    
    def __init__(self, config_path: str = None):
        self.backend_url = "***REMOVED***"
        self.config = self._load_config(config_path)
        self.session = None
        self._compile_patterns()
        
        # Known deployment tracking
        self.known_deployments = set()
        self.failed_deployments = set()
        self.security_threats = set()
        
        # Performance tracking
        self.response_times = []
        self.error_counts = {}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration with comprehensive defaults."""
        default_config = {
            'backend_url': '***REMOVED***',
            'testing': {
                'timeout': 30,
                'max_retries': 3,
                'batch_size': 10,
                'discovery_count': 50
            },
            'monitoring': {
                'check_interval': 300,  # 5 minutes
                'alert_threshold': 0.8,
                'performance_threshold': 2000,  # 2 seconds
                'max_failures': 5
            },
            'patterns': {
                'localhost': [
                    r'^https?://localhost:\d+$',
                    r'^https?://127\.0\.0\.1:\d+$'
                ],
                'production': [
                    r'^https://insurance-navigator\.vercel\.app$'
                ],
                'vercel_preview': [
                    r'^https://insurance-navigator-[a-z0-9]+-andrew-quintanas-projects\.vercel\.app$'
                ],
                'security_threats': [
                    r'^https://insurance-navigator-[a-z0-9]+-(?!andrew-quintanas-projects).*\.vercel\.app$'
                ]
            },
            'notifications': {
                'slack_webhook': None,
                'email_alerts': [],
                'save_reports': True
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                
        return default_config
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        self.compiled_patterns = {}
        for category, patterns in self.config['patterns'].items():
            self.compiled_patterns[category] = [
                re.compile(pattern) for pattern in patterns
            ]
    
    def validate_origin_comprehensive(self, origin: str) -> Dict[str, Any]:
        """Comprehensive origin validation with detailed analysis."""
        if not origin or not isinstance(origin, str):
            return {
                'valid': False,
                'reason': 'Invalid or empty origin',
                'category': 'invalid',
                'risk_level': 'unknown',
                'security_flags': ['empty_origin']
            }
        
        # Parse URL
        try:
            parsed = urllib.parse.urlparse(origin)
            if not parsed.scheme or not parsed.netloc:
                return {
                    'valid': False,
                    'reason': 'Malformed URL',
                    'category': 'invalid',
                    'risk_level': 'low',
                    'security_flags': ['malformed_url']
                }
        except Exception:
            return {
                'valid': False,
                'reason': 'URL parsing failed',
                'category': 'invalid', 
                'risk_level': 'low',
                'security_flags': ['parsing_error']
            }
        
        # Check against patterns
        security_flags = []
        
        # Localhost
        for pattern in self.compiled_patterns['localhost']:
            if pattern.match(origin):
                return {
                    'valid': True,
                    'reason': 'Localhost development environment',
                    'category': 'localhost',
                    'risk_level': 'low',
                    'security_flags': []
                }
        
        # Production
        for pattern in self.compiled_patterns['production']:
            if pattern.match(origin):
                return {
                    'valid': True,
                    'reason': 'Production domain',
                    'category': 'production',
                    'risk_level': 'low',
                    'security_flags': []
                }
        
        # Security threats (check first)
        for pattern in self.compiled_patterns['security_threats']:
            if pattern.match(origin):
                security_flags.extend(['unauthorized_user', 'security_threat'])
                return {
                    'valid': False,
                    'reason': 'Unauthorized Vercel deployment',
                    'category': 'security_threat',
                    'risk_level': 'high',
                    'security_flags': security_flags
                }
        
        # Vercel preview
        for pattern in self.compiled_patterns['vercel_preview']:
            if pattern.match(origin):
                return {
                    'valid': True,
                    'reason': 'Authorized Vercel preview deployment',
                    'category': 'vercel_preview',
                    'risk_level': 'low',
                    'security_flags': []
                }
        
        # Unknown domain
        if 'vercel.app' in origin:
            security_flags.append('unknown_vercel_deployment')
            return {
                'valid': False,
                'reason': 'Unknown Vercel deployment pattern',
                'category': 'unknown_vercel',
                'risk_level': 'medium',
                'security_flags': security_flags
            }
        
        # External domain
        return {
            'valid': False,
            'reason': 'External domain not in allowlist',
            'category': 'external',
            'risk_level': 'medium',
            'security_flags': ['external_domain']
        }
    
    async def discover_vercel_deployments(self, count: int = None) -> List[str]:
        """Discover potential Vercel deployments using various strategies."""
        count = count or self.config['testing']['discovery_count']
        deployments = set()
        
        # Strategy 1: Generate common patterns
        logger.info(f"🔍 Generating {count} potential Vercel deployment URLs...")
        
        # Common ID patterns Vercel uses
        patterns = [
            # Short alphanumeric (8-10 chars)
            lambda: ''.join(secrets.choice(string.ascii_lowercase + string.digits) 
                          for _ in range(secrets.randbelow(3) + 8)),
            # Mixed case with numbers (9-12 chars)  
            lambda: ''.join(secrets.choice(string.ascii_lowercase + string.digits) 
                          for _ in range(secrets.randbelow(4) + 9)),
            # Longer IDs (12-15 chars)
            lambda: ''.join(secrets.choice(string.ascii_lowercase + string.digits) 
                          for _ in range(secrets.randbelow(4) + 12)),
        ]
        
        for _ in range(count):
            pattern = secrets.choice(patterns)
            deployment_id = pattern()
            url = f"https://insurance-navigator-{deployment_id}-andrew-quintanas-projects.vercel.app"
            deployments.add(url)
        
        # Strategy 2: Add known working patterns
        known_patterns = [
            'k2ui23iaj', 'abc123', 'test123', '1x3xrmwl5',
            'hrf0s88oh', 'q2ukn6eih', 'cylkkqsmn', 'gybzhfv6'
        ]
        
        for pattern in known_patterns:
            url = f"https://insurance-navigator-{pattern}-andrew-quintanas-projects.vercel.app"
            deployments.add(url)
        
        # Strategy 3: Add localhost variants
        localhost_urls = [
            'http://localhost:3000',
            'http://localhost:3001', 
            'http://127.0.0.1:3000',
            'https://localhost:3000'
        ]
        deployments.update(localhost_urls)
        
        # Strategy 4: Add production
        deployments.add('https://insurance-navigator.vercel.app')
        
        # Strategy 5: Add security test cases
        security_tests = [
            'https://insurance-navigator-hack-different-user.vercel.app',
            'https://insurance-navigator-test-malicious-user.vercel.app',
            'https://malicious-insurance-app.vercel.app'
        ]
        deployments.update(security_tests)
        
        return list(deployments)
    
    async def test_cors_endpoint_deep(self, origin: str) -> Dict[str, Any]:
        """Deep CORS testing with multiple scenarios."""
        start_time = time.time()
        
        result = {
            'origin': origin,
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'validation': {},
            'performance': {},
            'security': {},
            'overall': {}
        }
        
        # Validate origin
        validation = self.validate_origin_comprehensive(origin)
        result['validation'] = validation
        
        # Security analysis
        security_analysis = {
            'risk_level': validation.get('risk_level', 'unknown'),
            'security_flags': validation.get('security_flags', []),
            'category': validation.get('category', 'unknown'),
            'should_block': not validation.get('valid', False)
        }
        result['security'] = security_analysis
        
        if not self.session:
            connector = aiohttp.TCPConnector(ssl=False)
            timeout = aiohttp.ClientTimeout(total=self.config['testing']['timeout'])
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        # Test 1: Preflight (OPTIONS)
        try:
            headers = {
                'Origin': origin,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type, Authorization'
            }
            
            async with self.session.options(
                f"{self.backend_url}/upload-policy",
                headers=headers
            ) as response:
                cors_headers = {
                    k.lower().replace('_', '-'): v 
                    for k, v in response.headers.items() 
                    if k.lower().startswith('access-control')
                }
                
                result['tests']['preflight'] = {
                    'status': response.status,
                    'success': response.status == 200,
                    'cors_headers': cors_headers,
                    'expected_origin': origin in cors_headers.get('access-control-allow-origin', ''),
                    'has_credentials': cors_headers.get('access-control-allow-credentials') == 'true',
                    'allowed_methods': cors_headers.get('access-control-allow-methods', '').split(', '),
                    'allowed_headers': cors_headers.get('access-control-allow-headers', '').split(', ')
                }
                
        except Exception as e:
            result['tests']['preflight'] = {
                'status': 0,
                'success': False,
                'error': str(e),
                'cors_headers': {}
            }
        
        # Test 2: Actual request (GET /health)
        try:
            headers = {'Origin': origin}
            
            async with self.session.get(
                f"{self.backend_url}/health",
                headers=headers
            ) as response:
                cors_headers = {
                    k.lower().replace('_', '-'): v 
                    for k, v in response.headers.items() 
                    if k.lower().startswith('access-control')
                }
                
                result['tests']['health_check'] = {
                    'status': response.status,
                    'success': response.status == 200,
                    'cors_headers': cors_headers,
                    'response_time': f"{(time.time() - start_time) * 1000:.0f}ms"
                }
                
        except Exception as e:
            result['tests']['health_check'] = {
                'status': 0,
                'success': False,
                'error': str(e),
                'cors_headers': {}
            }
        
        # Test 3: Heavy endpoint (simulated upload)
        try:
            headers = {'Origin': origin}
            
            async with self.session.options(
                f"{self.backend_url}/upload-policy",
                headers=headers
            ) as response:
                result['tests']['upload_preflight'] = {
                    'status': response.status,
                    'success': response.status == 200,
                    'can_handle_heavy_requests': response.status != 502
                }
                
        except Exception as e:
            result['tests']['upload_preflight'] = {
                'status': 0,
                'success': False,
                'error': str(e)
            }
        
        # Performance analysis
        total_time = (time.time() - start_time) * 1000
        result['performance'] = {
            'total_time_ms': round(total_time, 2),
            'is_fast': total_time < self.config['monitoring']['performance_threshold'],
            'rating': 'fast' if total_time < 1000 else 'slow' if total_time > 3000 else 'medium'
        }
        
        # Overall assessment
        cors_working = (
            result['tests'].get('preflight', {}).get('success', False) and
            result['tests'].get('health_check', {}).get('success', False)
        )
        
        needs_attention = (
            not cors_working or
            validation.get('risk_level') == 'high' or
            total_time > self.config['monitoring']['performance_threshold']
        )
        
        result['overall'] = {
            'cors_working': cors_working,
            'pattern_valid': validation.get('valid', False),
            'risk_level': validation.get('risk_level', 'unknown'),
            'needs_attention': needs_attention,
            'recommendation': self._generate_recommendation(result)
        }
        
        return result
    
    def _generate_recommendation(self, test_result: Dict[str, Any]) -> str:
        """Generate specific recommendations based on test results."""
        validation = test_result.get('validation', {})
        tests = test_result.get('tests', {})
        performance = test_result.get('performance', {})
        
        if validation.get('risk_level') == 'high':
            return "🚨 BLOCK IMMEDIATELY - Security threat detected"
        
        if not tests.get('preflight', {}).get('success'):
            return "🔧 Fix CORS preflight configuration"
        
        if not tests.get('health_check', {}).get('success'):
            return "⚠️ Backend connectivity issues"
        
        if tests.get('upload_preflight', {}).get('status') == 502:
            return "🛠️ Server stability issues during heavy operations"
        
        if not performance.get('is_fast'):
            return "⚡ Performance optimization needed"
        
        if validation.get('valid'):
            return "✅ Working correctly"
        
        return "❓ Review needed"
    
    async def comprehensive_scan(self, discovery_count: int = None) -> Dict[str, Any]:
        """Run comprehensive CORS scan with discovery, testing, and analysis."""
        logger.info("🚀 Starting comprehensive CORS scan...")
        
        start_time = time.time()
        
        # Discover potential deployments
        deployments = await self.discover_vercel_deployments(discovery_count)
        logger.info(f"🔍 Testing {len(deployments)} potential deployments...")
        
        # Test in batches
        batch_size = self.config['testing']['batch_size']
        results = []
        
        for i in range(0, len(deployments), batch_size):
            batch = deployments[i:i + batch_size]
            logger.info(f"📦 Testing batch {i//batch_size + 1}/{(len(deployments)-1)//batch_size + 1}")
            
            # Test batch concurrently
            batch_tasks = [self.test_cors_endpoint_deep(url) for url in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for url, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Failed to test {url}: {result}")
                    results.append({
                        'origin': url,
                        'error': str(result),
                        'overall': {'cors_working': False, 'needs_attention': True}
                    })
                else:
                    results.append(result)
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        # Analyze results
        analysis = self._analyze_results(results)
        
        # Generate comprehensive report
        report = {
            'scan_metadata': {
                'timestamp': datetime.now().isoformat(),
                'backend_url': self.backend_url,
                'total_tested': len(deployments),
                'scan_duration': round(time.time() - start_time, 2),
                'batch_size': batch_size
            },
            'results': results,
            'analysis': analysis,
            'recommendations': self._generate_comprehensive_recommendations(analysis),
            'security_summary': self._generate_security_summary(results),
            'performance_summary': self._generate_performance_summary(results)
        }
        
        # Save report
        if self.config['notifications']['save_reports']:
            self._save_report(report)
        
        logger.info("✅ Comprehensive scan completed")
        return report
    
    def _analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze scan results for patterns and issues."""
        total = len(results)
        working = sum(1 for r in results if r.get('overall', {}).get('cors_working', False))
        failing = total - working
        
        high_risk = sum(1 for r in results if r.get('validation', {}).get('risk_level') == 'high')
        medium_risk = sum(1 for r in results if r.get('validation', {}).get('risk_level') == 'medium')
        
        slow_responses = sum(1 for r in results 
                           if r.get('performance', {}).get('total_time_ms', 0) > 2000)
        
        security_threats = [r for r in results 
                          if r.get('validation', {}).get('category') == 'security_threat']
        
        unknown_deployments = [r for r in results 
                             if r.get('validation', {}).get('category') == 'unknown_vercel']
        
        return {
            'total_tested': total,
            'working': working,
            'failing': failing,
            'success_rate': round((working / total) * 100, 1) if total > 0 else 0,
            'risk_distribution': {
                'high': high_risk,
                'medium': medium_risk,
                'low': total - high_risk - medium_risk
            },
            'performance': {
                'slow_responses': slow_responses,
                'performance_score': round(((total - slow_responses) / total) * 100, 1) if total > 0 else 0
            },
            'security': {
                'threats_detected': len(security_threats),
                'unknown_deployments': len(unknown_deployments),
                'threat_details': security_threats[:5]  # Top 5 threats
            }
        }
    
    def _generate_comprehensive_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate comprehensive recommendations based on analysis."""
        recommendations = []
        
        # Success rate recommendations
        if analysis['success_rate'] < 80:
            recommendations.append(
                f"🔧 Low success rate ({analysis['success_rate']}%) - Review CORS configuration"
            )
        
        # Security recommendations
        security = analysis['security']
        if security['threats_detected'] > 0:
            recommendations.append(
                f"🚨 {security['threats_detected']} security threats detected - Block immediately"
            )
        
        if security['unknown_deployments'] > 0:
            recommendations.append(
                f"❓ {security['unknown_deployments']} unknown deployments - Review patterns"
            )
        
        # Performance recommendations
        if analysis['performance']['performance_score'] < 80:
            recommendations.append(
                f"⚡ Performance issues detected - {analysis['performance']['slow_responses']} slow responses"
            )
        
        # General recommendations
        if analysis['failing'] > 5:
            recommendations.append(
                "📋 High failure count - Consider automated deployment discovery"
            )
        
        if not recommendations:
            recommendations.append("✅ All systems operating normally")
        
        return recommendations
    
    def _generate_security_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate security summary from results."""
        threats = []
        warnings = []
        
        for result in results:
            validation = result.get('validation', {})
            if validation.get('risk_level') == 'high':
                threats.append({
                    'origin': result.get('origin'),
                    'reason': validation.get('reason'),
                    'flags': validation.get('security_flags', [])
                })
            elif validation.get('risk_level') == 'medium':
                warnings.append({
                    'origin': result.get('origin'),
                    'reason': validation.get('reason'),
                    'category': validation.get('category')
                })
        
        return {
            'threat_level': 'high' if threats else 'medium' if warnings else 'low',
            'active_threats': len(threats),
            'warnings': len(warnings),
            'threat_details': threats[:3],  # Top 3 threats
            'warning_details': warnings[:3]  # Top 3 warnings
        }
    
    def _generate_performance_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate performance summary from results."""
        response_times = [
            r.get('performance', {}).get('total_time_ms', 0) 
            for r in results if 'performance' in r
        ]
        
        if not response_times:
            return {'status': 'no_data'}
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        fast_count = sum(1 for t in response_times if t < 1000)
        slow_count = sum(1 for t in response_times if t > 3000)
        
        return {
            'average_response_ms': round(avg_time, 2),
            'max_response_ms': round(max_time, 2),
            'min_response_ms': round(min_time, 2),
            'fast_responses': fast_count,
            'slow_responses': slow_count,
            'performance_grade': (
                'A' if avg_time < 1000 else
                'B' if avg_time < 2000 else
                'C' if avg_time < 3000 else 'D'
            )
        }
    
    def _save_report(self, report: Dict[str, Any]):
        """Save comprehensive report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cors_comprehensive_scan_{timestamp}.json"
        
        # Create reports directory
        reports_dir = Path("scripts/monitoring/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Report saved: {filepath}")
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()

async def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive CORS Scanner")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--count", type=int, default=30, help="Number of URLs to test")
    parser.add_argument("--backend", default="***REMOVED***", 
                       help="Backend URL to test against")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size for testing")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    scanner = ComprehensiveCORSScanner(args.config)
    scanner.backend_url = args.backend
    scanner.config['testing']['batch_size'] = args.batch_size
    
    try:
        report = await scanner.comprehensive_scan(args.count)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE CORS SCAN RESULTS")
        print("="*60)
        
        analysis = report['analysis']
        print(f"🎯 Total tested: {analysis['total_tested']}")
        print(f"✅ Working: {analysis['working']}")
        print(f"❌ Failing: {analysis['failing']}")
        print(f"📈 Success rate: {analysis['success_rate']}%")
        
        # Security summary
        security = report['security_summary']
        print(f"\n🔒 Security Status: {security['threat_level'].upper()}")
        if security['active_threats'] > 0:
            print(f"🚨 Active threats: {security['active_threats']}")
        if security['warnings'] > 0:
            print(f"⚠️ Warnings: {security['warnings']}")
        
        # Performance summary
        performance = report['performance_summary']
        if performance.get('status') != 'no_data':
            print(f"\n⚡ Performance Grade: {performance['performance_grade']}")
            print(f"⏱️ Avg response: {performance['average_response_ms']}ms")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 40)
        for rec in report['recommendations']:
            print(f"• {rec}")
        
    finally:
        await scanner.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 