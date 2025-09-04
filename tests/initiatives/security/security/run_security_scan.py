"""Security scanning script using OWASP ZAP."""
import time
import sys
import json
from datetime import datetime
import subprocess
import requests
from zapv2 import ZAPv2
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityScanner:
    """Security scanner using OWASP ZAP."""

    def __init__(self, target_url, api_key=None):
        """Initialize the scanner."""
        self.target_url = target_url
        self.api_key = api_key or 'changeme'  # Default API key for ZAP
        self.zap = None
        self.context_id = 1
        self.context_name = 'insurance_navigator'

    def setup_zap(self):
        """Initialize ZAP connection."""
        try:
            # Connect to ZAP
            self.zap = ZAPv2(
                apikey=self.api_key,
                proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
            )
            
            # Wait for ZAP to be ready
            while True:
                try:
                    logger.info('Waiting for ZAP to be ready...')
                    status = self.zap.core.status
                    if status == '100':
                        break
                    time.sleep(2)
                except Exception:
                    time.sleep(2)
            
            logger.info('ZAP is ready')
            
        except Exception as e:
            logger.error(f'Failed to connect to ZAP: {str(e)}')
            sys.exit(1)

    def setup_context(self):
        """Set up the scanning context."""
        logger.info('Setting up context...')
        
        # Create new context
        self.zap.context.new_context(self.context_name)
        
        # Include target URL in context
        self.zap.context.include_in_context(
            self.context_name,
            f'^{self.target_url}.*$'
        )
        
        # Set up authentication
        self.zap.authentication.set_authentication_method(
            self.context_id,
            'jsonBasedAuthentication',
            '''{"loginUrl": "LOGIN_URL",
                "loginRequestData": "{'email':'%username%','password':'%password%'}"}'''
        )
        
        # Configure login indicators
        self.zap.authentication.set_logged_in_indicator(
            self.context_id,
            '\Q"token_type":"bearer"\E'
        )
        self.zap.authentication.set_logged_out_indicator(
            self.context_id,
            '\Q"error":"Unauthorized"\E'
        )

    def setup_users(self):
        """Set up test users for authenticated scanning."""
        logger.info('Setting up test users...')
        
        # Create test user
        user_id = self.zap.users.new_user(self.context_id, 'test_user')
        self.zap.users.set_authentication_credentials(
            self.context_id,
            user_id,
            '''{"username":"security_test@example.com",
                "password":"SecureTest123!"}'''
        )
        self.zap.users.set_user_enabled(self.context_id, user_id, True)
        
        # Create admin user
        admin_id = self.zap.users.new_user(self.context_id, 'test_admin')
        self.zap.users.set_authentication_credentials(
            self.context_id,
            admin_id,
            '''{"username":"security_admin@example.com",
                "password":"AdminTest123!"}'''
        )
        self.zap.users.set_user_enabled(self.context_id, admin_id, True)

    def run_spider(self):
        """Run the spider to discover endpoints."""
        logger.info('Starting spider scan...')
        
        # Run traditional spider
        scan_id = self.zap.spider.scan(self.target_url)
        
        # Wait for spider to complete
        while True:
            status = int(self.zap.spider.status(scan_id))
            logger.info(f'Spider progress: {status}%')
            if status >= 100:
                break
            time.sleep(5)
        
        logger.info('Spider scan completed')
        
        # Run AJAX Spider for JavaScript-heavy pages
        self.zap.ajaxSpider.scan(self.target_url)
        
        while self.zap.ajaxSpider.status == 'running':
            logger.info('Ajax Spider is running...')
            time.sleep(5)
        
        logger.info('Ajax Spider completed')

    def run_active_scan(self):
        """Run active security scan."""
        logger.info('Starting active scan...')
        
        # Configure scan policy
        scan_policy_name = 'Insurance Navigator Policy'
        self.zap.ascan.add_scan_policy(scan_policy_name)
        
        # Enable relevant scan rules
        rules = {
            # SQL Injection
            '40018': 'HIGH',  # SQL Injection
            '40019': 'HIGH',  # SQL Injection MySQL
            '40020': 'HIGH',  # SQL Injection PostgreSQL
            '40021': 'HIGH',  # SQL Injection Oracle
            '40022': 'HIGH',  # SQL Injection SQLServer
            
            # XSS
            '40012': 'HIGH',  # Reflected XSS
            '40014': 'HIGH',  # Persistent XSS
            '40016': 'HIGH',  # Persistent XSS Spider
            
            # Authentication
            '40013': 'HIGH',  # Session Fixation
            '40017': 'HIGH',  # CSRF
            
            # Information Disclosure
            '40023': 'MEDIUM',  # Path Traversal
            '40024': 'MEDIUM',  # Command Injection
            '40025': 'MEDIUM',  # LDAP Injection
            
            # Access Control
            '40026': 'HIGH',  # Cross Site Scripting (DOM Based)
            '40027': 'MEDIUM',  # SQL Injection (DOM Based)
            
            # Input Validation
            '40028': 'MEDIUM',  # Open Redirect
            '40029': 'MEDIUM',  # SSRF
        }
        
        for rule_id, strength in rules.items():
            self.zap.ascan.set_scanner_alert_threshold(
                rule_id,
                strength,
                scan_policy_name
            )
        
        # Start scan
        scan_id = self.zap.ascan.scan(
            self.target_url,
            scanpolicyname=scan_policy_name
        )
        
        # Wait for scan to complete
        while True:
            status = int(self.zap.ascan.status(scan_id))
            logger.info(f'Scan progress: {status}%')
            if status >= 100:
                break
            time.sleep(10)
        
        logger.info('Active scan completed')

    def generate_report(self):
        """Generate security report."""
        logger.info('Generating report...')
        
        # Get all alerts
        alerts = self.zap.core.alerts()
        
        # Organize alerts by risk level
        report = {
            'scan_date': datetime.now().isoformat(),
            'target_url': self.target_url,
            'risk_summary': {
                'high': 0,
                'medium': 0,
                'low': 0,
                'informational': 0
            },
            'alerts': {
                'high': [],
                'medium': [],
                'low': [],
                'informational': []
            }
        }
        
        for alert in alerts:
            risk = alert['risk'].lower()
            report['risk_summary'][risk] += 1
            report['alerts'][risk].append({
                'name': alert['name'],
                'description': alert['description'],
                'url': alert['url'],
                'param': alert['param'],
                'evidence': alert['evidence'],
                'solution': alert['solution'],
                'reference': alert['reference']
            })
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'security_scan_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f'Report saved to {report_file}')
        
        # Print summary
        logger.info('\nScan Summary:')
        logger.info('=' * 50)
        for risk, count in report['risk_summary'].items():
            logger.info(f'{risk.upper()} Risk Issues: {count}')

    def check_hipaa_compliance(self):
        """Check for HIPAA-specific security requirements."""
        logger.info('Checking HIPAA compliance...')
        
        hipaa_checks = {
            'encryption': {
                'description': 'Check for proper encryption in transit',
                'rules': ['10015', '10016', '10017'],  # SSL/TLS issues
                'required': True
            },
            'authentication': {
                'description': 'Verify authentication mechanisms',
                'rules': ['10012', '10013', '10014'],  # Auth related issues
                'required': True
            },
            'access_control': {
                'description': 'Check access control mechanisms',
                'rules': ['10020', '10021', '10022'],  # Access control issues
                'required': True
            },
            'audit_logging': {
                'description': 'Verify audit logging capabilities',
                'rules': ['10030', '10031', '10032'],  # Logging related issues
                'required': True
            }
        }
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {}
        }
        
        for check_name, check_info in hipaa_checks.items():
            alerts = []
            for rule in check_info['rules']:
                alerts.extend(self.zap.core.alerts(rule))
            
            passed = len(alerts) == 0
            results['checks'][check_name] = {
                'passed': passed,
                'required': check_info['required'],
                'description': check_info['description'],
                'alerts': [a['name'] for a in alerts]
            }
        
        # Save HIPAA compliance report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'hipaa_compliance_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f'HIPAA compliance report saved to {report_file}')
        
        # Print summary
        logger.info('\nHIPAA Compliance Summary:')
        logger.info('=' * 50)
        for check, result in results['checks'].items():
            status = 'PASSED' if result['passed'] else 'FAILED'
            required = '(Required)' if result['required'] else '(Optional)'
            logger.info(f'{check}: {status} {required}')

def main():
    """Main execution function."""
    # Parse command line arguments
    if len(sys.argv) < 2:
        print('Usage: python run_security_scan.py <target_url> [api_key]')
        sys.exit(1)
    
    target_url = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Initialize scanner
    scanner = SecurityScanner(target_url, api_key)
    
    try:
        # Run security scan
        scanner.setup_zap()
        scanner.setup_context()
        scanner.setup_users()
        scanner.run_spider()
        scanner.run_active_scan()
        scanner.generate_report()
        scanner.check_hipaa_compliance()
        
    except Exception as e:
        logger.error(f'Security scan failed: {str(e)}')
        sys.exit(1)
    
    logger.info('Security scan completed successfully')

if __name__ == '__main__':
    main() 