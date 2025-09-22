#!/usr/bin/env python3
"""
Production Database Connectivity Investigation

Focused investigation of the production database connectivity issue
with specific attention to the "Network is unreachable" error.

This script tests various connection patterns to identify the root cause
of the production database connectivity failure.
"""

import asyncio
import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import asyncpg
import ssl
import socket
import dns.resolver

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Result of a specific test."""
    test_name: str
    success: bool
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None
    details: Optional[Dict] = None

class ProductionDatabaseInvestigator:
    """Focused investigation of production database connectivity."""
    
    def __init__(self):
        self.production_config = {
            'host': 'db.znvwzkdblknkkztqyfnu.supabase.co',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': 'beqhar-qincyg-Syxxi8',
            'connection_string': 'postgresql://postgres:beqhar-qincyg-Syxxi8@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres'
        }
        self.results: List[TestResult] = []
    
    async def test_dns_resolution(self) -> TestResult:
        """Test DNS resolution for the production database host."""
        test_name = "DNS Resolution"
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Testing DNS resolution for {self.production_config['host']}")
            
            # Test A record resolution
            result = dns.resolver.resolve(self.production_config['host'], 'A')
            ips = [str(ip) for ip in result]
            
            duration = (time.time() - start_time) * 1000
            
            return TestResult(
                test_name=test_name,
                success=True,
                duration_ms=duration,
                details={'resolved_ips': ips}
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                success=False,
                error_message=str(e),
                duration_ms=duration
            )
    
    async def test_port_connectivity(self) -> TestResult:
        """Test basic port connectivity to the production database."""
        test_name = "Port Connectivity"
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Testing port connectivity to {self.production_config['host']}:{self.production_config['port']}")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((self.production_config['host'], self.production_config['port']))
            sock.close()
            
            duration = (time.time() - start_time) * 1000
            
            return TestResult(
                test_name=test_name,
                success=result == 0,
                error_message=f"Connection failed with error code: {result}" if result != 0 else None,
                duration_ms=duration,
                details={'error_code': result}
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                success=False,
                error_message=str(e),
                duration_ms=duration
            )
    
    async def test_ssl_handshake(self) -> TestResult:
        """Test SSL handshake with the production database."""
        test_name = "SSL Handshake"
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Testing SSL handshake with {self.production_config['host']}:{self.production_config['port']}")
            
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Create socket and wrap with SSL
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.production_config['host'], self.production_config['port']))
            
            ssl_sock = context.wrap_socket(sock, server_hostname=self.production_config['host'])
            
            # Get SSL information
            ssl_info = {
                'protocol': ssl_sock.version(),
                'cipher': ssl_sock.cipher(),
                'certificate': ssl_sock.getpeercert()
            }
            
            ssl_sock.close()
            duration = (time.time() - start_time) * 1000
            
            return TestResult(
                test_name=test_name,
                success=True,
                duration_ms=duration,
                details=ssl_info
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                success=False,
                error_message=str(e),
                duration_ms=duration
            )
    
    async def test_database_connection_ssl_modes(self) -> List[TestResult]:
        """Test database connection with different SSL modes."""
        results = []
        ssl_modes = ['disable', 'prefer', 'require', 'verify-ca', 'verify-full']
        
        for ssl_mode in ssl_modes:
            test_name = f"Database Connection (SSL: {ssl_mode})"
            start_time = time.time()
            
            try:
                logger.info(f"🔍 Testing database connection with SSL mode: {ssl_mode}")
                
                conn = await asyncpg.connect(
                    host=self.production_config['host'],
                    port=self.production_config['port'],
                    database=self.production_config['database'],
                    user=self.production_config['user'],
                    password=self.production_config['password'],
                    ssl=ssl_mode,
                    command_timeout=30
                )
                
                # Test basic query
                version = await conn.fetchval("SELECT version()")
                await conn.close()
                
                duration = (time.time() - start_time) * 1000
                
                results.append(TestResult(
                    test_name=test_name,
                    success=True,
                    duration_ms=duration,
                    details={'ssl_mode': ssl_mode, 'postgres_version': version}
                ))
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                results.append(TestResult(
                    test_name=test_name,
                    success=False,
                    error_message=str(e),
                    duration_ms=duration,
                    details={'ssl_mode': ssl_mode}
                ))
        
        return results
    
    async def test_connection_string_formats(self) -> List[TestResult]:
        """Test different connection string formats."""
        results = []
        
        connection_strings = [
            # Basic format
            f"postgresql://{self.production_config['user']}:{self.production_config['password']}@{self.production_config['host']}:{self.production_config['port']}/{self.production_config['database']}",
            
            # With SSL mode
            f"postgresql://{self.production_config['user']}:{self.production_config['password']}@{self.production_config['host']}:{self.production_config['port']}/{self.production_config['database']}?sslmode=require",
            
            # With SSL mode and timeout
            f"postgresql://{self.production_config['user']}:{self.production_config['password']}@{self.production_config['host']}:{self.production_config['port']}/{self.production_config['database']}?sslmode=require&connect_timeout=30",
            
            # Alternative SSL parameter
            f"postgresql://{self.production_config['user']}:{self.production_config['password']}@{self.production_config['host']}:{self.production_config['port']}/{self.production_config['database']}?ssl=require",
            
            # With additional parameters
            f"postgresql://{self.production_config['user']}:{self.production_config['password']}@{self.production_config['host']}:{self.production_config['port']}/{self.production_config['database']}?sslmode=require&connect_timeout=30&command_timeout=30",
        ]
        
        for i, conn_str in enumerate(connection_strings, 1):
            test_name = f"Connection String Format {i}"
            start_time = time.time()
            
            try:
                logger.info(f"🔍 Testing connection string format {i}")
                
                conn = await asyncpg.connect(conn_str, command_timeout=30)
                version = await conn.fetchval("SELECT version()")
                await conn.close()
                
                duration = (time.time() - start_time) * 1000
                
                results.append(TestResult(
                    test_name=test_name,
                    success=True,
                    duration_ms=duration,
                    details={'connection_string': conn_str, 'postgres_version': version}
                ))
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                results.append(TestResult(
                    test_name=test_name,
                    success=False,
                    error_message=str(e),
                    duration_ms=duration,
                    details={'connection_string': conn_str}
                ))
        
        return results
    
    async def test_network_routing(self) -> TestResult:
        """Test network routing to the production database."""
        test_name = "Network Routing"
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Testing network routing to {self.production_config['host']}")
            
            # Test with different timeout values
            timeouts = [5, 10, 30, 60]
            results = {}
            
            for timeout in timeouts:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((self.production_config['host'], self.production_config['port']))
                    sock.close()
                    results[f'timeout_{timeout}s'] = result
                except Exception as e:
                    results[f'timeout_{timeout}s'] = str(e)
            
            duration = (time.time() - start_time) * 1000
            
            return TestResult(
                test_name=test_name,
                success=any(r == 0 for r in results.values() if isinstance(r, int)),
                error_message="All timeout tests failed" if not any(r == 0 for r in results.values() if isinstance(r, int)) else None,
                duration_ms=duration,
                details=results
            )
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                test_name=test_name,
                success=False,
                error_message=str(e),
                duration_ms=duration
            )
    
    async def run_investigation(self) -> Dict[str, Any]:
        """Run comprehensive production database investigation."""
        logger.info("🚨 PRODUCTION DATABASE CONNECTIVITY INVESTIGATION")
        logger.info("=" * 80)
        logger.info(f"Target: {self.production_config['host']}:{self.production_config['port']}")
        logger.info(f"Database: {self.production_config['database']}")
        logger.info("=" * 80)
        
        # Run all tests
        tests = [
            self.test_dns_resolution(),
            self.test_port_connectivity(),
            self.test_ssl_handshake(),
            self.test_network_routing(),
        ]
        
        # Run basic connectivity tests
        for test in tests:
            result = await test
            self.results.append(result)
        
        # Run database connection tests
        db_ssl_results = await self.test_database_connection_ssl_modes()
        self.results.extend(db_ssl_results)
        
        # Run connection string tests
        conn_str_results = await self.test_connection_string_formats()
        self.results.extend(conn_str_results)
        
        # Generate summary
        summary = self._generate_summary()
        
        return {
            'timestamp': time.time(),
            'target_config': self.production_config,
            'test_results': [asdict(r) for r in self.results],
            'summary': summary,
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate investigation summary."""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - successful_tests
        
        # Categorize failures
        failure_categories = {}
        for result in self.results:
            if not result.success and result.error_message:
                error_type = result.error_message.split(':')[0] if ':' in result.error_message else result.error_message
                failure_categories[error_type] = failure_categories.get(error_type, 0) + 1
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'failure_categories': failure_categories
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Analyze successful patterns
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        if not successful_results:
            recommendations.append("🚨 CRITICAL: No successful database connections found")
            recommendations.append("🔍 Check network connectivity and firewall rules")
            recommendations.append("🔍 Verify Supabase database is accessible")
        else:
            # Find working SSL modes
            ssl_successes = [r for r in successful_results if 'SSL' in r.test_name]
            if ssl_successes:
                ssl_modes = [r.details.get('ssl_mode') for r in ssl_successes if r.details and 'ssl_mode' in r.details]
                if ssl_modes:
                    recommendations.append(f"✅ Use SSL mode: {ssl_modes[0]}")
            
            # Find working connection strings
            conn_str_successes = [r for r in successful_results if 'Connection String' in r.test_name]
            if conn_str_successes:
                recommendations.append("✅ Use working connection string format")
        
        # Analyze failure patterns
        if failed_results:
            network_failures = [r for r in failed_results if 'Network is unreachable' in str(r.error_message)]
            if network_failures:
                recommendations.append("🔍 Network connectivity issue - check DNS and routing")
            
            ssl_failures = [r for r in failed_results if 'SSL' in str(r.error_message) or 'ssl' in str(r.error_message).lower()]
            if ssl_failures:
                recommendations.append("🔍 SSL/TLS configuration issue - check certificates")
            
            timeout_failures = [r for r in failed_results if 'timeout' in str(r.error_message).lower()]
            if timeout_failures:
                recommendations.append("🔍 Connection timeout - check network latency and firewall")
        
        return recommendations
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save investigation results to file."""
        if filename is None:
            timestamp = int(time.time())
            filename = f"production_database_investigation_{timestamp}.json"
        
        filepath = Path(filename)
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📁 Investigation results saved to: {filepath}")
        return filepath

async def main():
    """Main investigation function."""
    investigator = ProductionDatabaseInvestigator()
    
    try:
        results = await investigator.run_investigation()
        
        # Save results
        output_file = investigator.save_results(results)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 PRODUCTION DATABASE INVESTIGATION SUMMARY")
        print("=" * 80)
        
        summary = results['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['failure_categories']:
            print("\n🚨 FAILURE CATEGORIES:")
            for category, count in summary['failure_categories'].items():
                print(f"  - {category}: {count} failures")
        
        print("\n📋 RECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"{i}. {rec}")
        
        print(f"\n📁 Detailed results saved to: {output_file}")
        
        return summary['success_rate'] > 0
        
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
