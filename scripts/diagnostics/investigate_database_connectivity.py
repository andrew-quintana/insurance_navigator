#!/usr/bin/env python3
"""
Comprehensive Database Connectivity Investigation Script

This script systematically tests database connectivity patterns across different
environments and configurations to identify working patterns and failure modes.

Usage:
    python investigate_database_connectivity.py [--environment production|staging|development]
"""

import asyncio
import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
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
class ConnectionTestResult:
    """Result of a database connection test."""
    test_name: str
    success: bool
    error_message: Optional[str] = None
    connection_time_ms: Optional[float] = None
    ssl_info: Optional[Dict] = None
    network_info: Optional[Dict] = None

@dataclass
class DatabaseConfig:
    """Database configuration for testing."""
    name: str
    host: str
    port: int
    database: str
    user: str
    password: str
    ssl_mode: str
    connection_string: str

class DatabaseConnectivityInvestigator:
    """Comprehensive database connectivity investigation tool."""
    
    def __init__(self):
        self.results: List[ConnectionTestResult] = []
        self.configs: Dict[str, DatabaseConfig] = {}
        self.setup_test_configurations()
    
    def setup_test_configurations(self):
        """Set up test configurations for different environments."""
        
        # Production Configuration
        self.configs['production'] = DatabaseConfig(
            name="Production",
            host=os.getenv("DB_HOST", "db.your-project.supabase.co"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "***REDACTED***"),
            ssl_mode="require",
            connection_string=os.getenv("DATABASE_URL", "postgresql://***REDACTED***@db.your-project.supabase.co:5432/postgres")
        )
        
        # Staging Configuration
        self.configs['staging'] = DatabaseConfig(
            name="Staging",
            host=os.getenv("STAGING_DB_HOST", "db.dfgzeastcxnoqshgyotp.supabase.co"),
            port=int(os.getenv("STAGING_DB_PORT", "5432")),
            database=os.getenv("STAGING_DB_NAME", "postgres"),
            user=os.getenv("STAGING_DB_USER", "postgres"),
            password=os.getenv("STAGING_DB_PASSWORD", "***REDACTED***"),
            ssl_mode="require",
            connection_string=os.getenv("STAGING_DATABASE_URL", "postgresql://***REDACTED***@db.dfgzeastcxnoqshgyotp.supabase.co:5432/postgres")
        )
        
        # Development Configuration (local)
        self.configs['development'] = DatabaseConfig(
            name="Development",
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="postgres",
            ssl_mode="prefer",
            connection_string="postgresql://postgres:postgres@localhost:5432/postgres"
        )
    
    async def test_network_connectivity(self, config: DatabaseConfig) -> Dict[str, Any]:
        """Test basic network connectivity to the database host."""
        network_info = {}
        
        try:
            # Test DNS resolution
            logger.info(f"Testing DNS resolution for {config.host}")
            dns_result = dns.resolver.resolve(config.host, 'A')
            network_info['dns_resolution'] = {
                'success': True,
                'ips': [str(ip) for ip in dns_result]
            }
        except Exception as e:
            logger.warning(f"DNS resolution failed: {e}")
            network_info['dns_resolution'] = {
                'success': False,
                'error': str(e)
            }
        
        try:
            # Test port connectivity
            logger.info(f"Testing port connectivity to {config.host}:{config.port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((config.host, config.port))
            sock.close()
            
            network_info['port_connectivity'] = {
                'success': result == 0,
                'error_code': result
            }
        except Exception as e:
            logger.warning(f"Port connectivity test failed: {e}")
            network_info['port_connectivity'] = {
                'success': False,
                'error': str(e)
            }
        
        return network_info
    
    async def test_ssl_handshake(self, config: DatabaseConfig) -> Dict[str, Any]:
        """Test SSL handshake with the database server."""
        ssl_info = {}
        
        try:
            logger.info(f"Testing SSL handshake with {config.host}:{config.port}")
            
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Create socket and wrap with SSL
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((config.host, config.port))
            
            ssl_sock = context.wrap_socket(sock, server_hostname=config.host)
            
            ssl_info = {
                'success': True,
                'protocol': ssl_sock.version(),
                'cipher': ssl_sock.cipher(),
                'certificate': {
                    'subject': ssl_sock.getpeercert().get('subject', []),
                    'issuer': ssl_sock.getpeercert().get('issuer', []),
                    'version': ssl_sock.getpeercert().get('version', 0)
                }
            }
            
            ssl_sock.close()
            
        except Exception as e:
            logger.warning(f"SSL handshake failed: {e}")
            ssl_info = {
                'success': False,
                'error': str(e)
            }
        
        return ssl_info
    
    async def test_database_connection(self, config: DatabaseConfig, ssl_mode: str = None) -> ConnectionTestResult:
        """Test database connection with specific SSL mode."""
        test_name = f"{config.name}_ssl_{ssl_mode or config.ssl_mode}"
        start_time = time.time()
        
        try:
            logger.info(f"Testing database connection: {test_name}")
            
            # Prepare connection parameters
            conn_params = {
                'host': config.host,
                'port': config.port,
                'database': config.database,
                'user': config.user,
                'password': config.password,
                'command_timeout': 30
            }
            
            # Add SSL configuration
            if ssl_mode:
                conn_params['ssl'] = ssl_mode
            else:
                conn_params['ssl'] = config.ssl_mode
            
            # Test connection
            conn = await asyncpg.connect(**conn_params)
            
            # Test basic query
            result = await conn.fetchval("SELECT version()")
            await conn.close()
            
            connection_time = (time.time() - start_time) * 1000
            
            return ConnectionTestResult(
                test_name=test_name,
                success=True,
                connection_time_ms=connection_time,
                ssl_info={'mode': ssl_mode or config.ssl_mode},
                network_info=await self.test_network_connectivity(config)
            )
            
        except Exception as e:
            connection_time = (time.time() - start_time) * 1000
            return ConnectionTestResult(
                test_name=test_name,
                success=False,
                error_message=str(e),
                connection_time_ms=connection_time,
                ssl_info={'mode': ssl_mode or config.ssl_mode},
                network_info=await self.test_network_connectivity(config)
            )
    
    async def test_connection_string_formats(self, config: DatabaseConfig) -> List[ConnectionTestResult]:
        """Test different connection string formats."""
        results = []
        
        # Test different connection string formats
        connection_strings = [
            # Basic format
            f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}",
            
            # With SSL mode
            f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}?sslmode=require",
            
            # With SSL mode and other parameters
            f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}?sslmode=require&connect_timeout=30",
            
            # Alternative SSL parameter
            f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}?ssl=require",
        ]
        
        for i, conn_str in enumerate(connection_strings):
            test_name = f"{config.name}_conn_str_{i+1}"
            start_time = time.time()
            
            try:
                logger.info(f"Testing connection string format: {test_name}")
                
                conn = await asyncpg.connect(conn_str, command_timeout=30)
                result = await conn.fetchval("SELECT version()")
                await conn.close()
                
                connection_time = (time.time() - start_time) * 1000
                
                results.append(ConnectionTestResult(
                    test_name=test_name,
                    success=True,
                    connection_time_ms=connection_time,
                    ssl_info={'connection_string': conn_str}
                ))
                
            except Exception as e:
                connection_time = (time.time() - start_time) * 1000
                results.append(ConnectionTestResult(
                    test_name=test_name,
                    success=False,
                    error_message=str(e),
                    connection_time_ms=connection_time,
                    ssl_info={'connection_string': conn_str}
                ))
        
        return results
    
    async def test_ssl_modes(self, config: DatabaseConfig) -> List[ConnectionTestResult]:
        """Test different SSL modes."""
        results = []
        
        ssl_modes = ['disable', 'prefer', 'require', 'verify-ca', 'verify-full']
        
        for ssl_mode in ssl_modes:
            result = await self.test_database_connection(config, ssl_mode)
            results.append(result)
        
        return results
    
    async def run_comprehensive_investigation(self, environment: str = None) -> Dict[str, Any]:
        """Run comprehensive database connectivity investigation."""
        logger.info("🔍 Starting comprehensive database connectivity investigation")
        logger.info("=" * 80)
        
        investigation_results = {
            'timestamp': time.time(),
            'environment': environment,
            'configurations_tested': [],
            'test_results': [],
            'summary': {},
            'recommendations': []
        }
        
        # Test configurations
        configs_to_test = [self.configs[env] for env in self.configs.keys() 
                          if environment is None or env == environment]
        
        for config in configs_to_test:
            logger.info(f"\n🧪 Testing {config.name} Configuration")
            logger.info("-" * 50)
            
            config_results = {
                'config_name': config.name,
                'config_details': asdict(config),
                'tests': []
            }
            
            # Test 1: Basic connection with default SSL mode
            basic_result = await self.test_database_connection(config)
            config_results['tests'].append(asdict(basic_result))
            self.results.append(basic_result)
            
            # Test 2: Different SSL modes
            ssl_results = await self.test_ssl_modes(config)
            for result in ssl_results:
                config_results['tests'].append(asdict(result))
                self.results.append(result)
            
            # Test 3: Different connection string formats
            conn_str_results = await self.test_connection_string_formats(config)
            for result in conn_str_results:
                config_results['tests'].append(asdict(result))
                self.results.append(result)
            
            investigation_results['configurations_tested'].append(config_results)
        
        # Generate summary
        investigation_results['summary'] = self._generate_summary()
        investigation_results['recommendations'] = self._generate_recommendations()
        
        return investigation_results
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate investigation summary."""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r.success])
        failed_tests = total_tests - successful_tests
        
        # Group by configuration
        config_summaries = {}
        for result in self.results:
            config_name = result.test_name.split('_')[0]
            if config_name not in config_summaries:
                config_summaries[config_name] = {'total': 0, 'successful': 0, 'failed': 0}
            
            config_summaries[config_name]['total'] += 1
            if result.success:
                config_summaries[config_name]['successful'] += 1
            else:
                config_summaries[config_name]['failed'] += 1
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'config_summaries': config_summaries
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Analyze successful patterns
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        if successful_results:
            # Find common patterns in successful connections
            ssl_modes_used = [r.ssl_info.get('mode') for r in successful_results if r.ssl_info and 'mode' in r.ssl_info]
            if ssl_modes_used:
                most_common_ssl = max(set(ssl_modes_used), key=ssl_modes_used.count)
                recommendations.append(f"Use SSL mode '{most_common_ssl}' for reliable connections")
        
        if failed_results:
            # Analyze common failure patterns
            error_patterns = {}
            for result in failed_results:
                if result.error_message:
                    error_type = result.error_message.split(':')[0]
                    error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
            
            if error_patterns:
                most_common_error = max(error_patterns, key=error_patterns.get)
                recommendations.append(f"Address common error pattern: {most_common_error}")
        
        # Network connectivity recommendations
        network_issues = [r for r in failed_results if r.network_info and 
                         not r.network_info.get('dns_resolution', {}).get('success', True)]
        if network_issues:
            recommendations.append("Check DNS resolution and network connectivity")
        
        ssl_issues = [r for r in failed_results if 'SSL' in str(r.error_message) or 'ssl' in str(r.error_message).lower()]
        if ssl_issues:
            recommendations.append("Review SSL/TLS configuration and certificate handling")
        
        return recommendations
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save investigation results to file."""
        if filename is None:
            timestamp = int(time.time())
            filename = f"database_connectivity_investigation_{timestamp}.json"
        
        filepath = Path(filename)
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📁 Investigation results saved to: {filepath}")
        return filepath

async def main():
    """Main investigation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Connectivity Investigation')
    parser.add_argument('--environment', choices=['production', 'staging', 'development'], 
                       help='Specific environment to test')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    investigator = DatabaseConnectivityInvestigator()
    
    try:
        results = await investigator.run_comprehensive_investigation(args.environment)
        
        # Save results
        output_file = investigator.save_results(results, args.output)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 INVESTIGATION SUMMARY")
        print("=" * 80)
        
        summary = results['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        print("\n📋 RECOMMENDATIONS")
        print("-" * 40)
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"{i}. {rec}")
        
        print(f"\n📁 Detailed results saved to: {output_file}")
        
        return results['summary']['success_rate'] > 0
        
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
