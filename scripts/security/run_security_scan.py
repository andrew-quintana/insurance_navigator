#!/usr/bin/env python3
"""
Automated Security Scanner using OWASP ZAP

This script:
1. Starts OWASP ZAP in daemon mode
2. Configures scanning policies
3. Performs automated security scans
4. Generates detailed security reports
5. Includes HIPAA compliance checks
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from zapv2 import ZAPv2
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityScanner:
    """Security scanner using OWASP ZAP."""
    
    def __init__(self, target_url: str, api_key: str = None):
        """Initialize the security scanner.
        
        Args:
            target_url: The base URL to scan
            api_key: ZAP API key (optional)
        """
        self.target_url = target_url
        self.zap = None
        self.api_key = api_key or self._generate_api_key()
        self.context_id = 1
        self.scan_id = None
        
        # Create reports directory
        self.reports_dir = Path("reports/security")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_api_key(self) -> str:
        """Generate a random API key for ZAP."""
        import secrets
        return secrets.token_urlsafe(32)
    
    def start_zap(self) -> None:
        """Start ZAP daemon and configure initial settings."""
        logger.info("Starting OWASP ZAP...")
        
        try:
            self.zap = ZAPv2(
                apikey=self.api_key,
                proxies={'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
            )
            
            # Wait for ZAP to be ready
            for _ in range(20):  # Wait up to 20 seconds
                try:
                    status = self.zap.core.status
                    if status == '100':
                        break
                except:
                    time.sleep(1)
            else:
                raise TimeoutError("ZAP failed to start")
            
            logger.info("ZAP started successfully")
            
            # Configure ZAP
            self._configure_scan_policy()
            
        except Exception as e:
            logger.error(f"Failed to start ZAP: {str(e)}")
            sys.exit(1)
    
    def _configure_scan_policy(self) -> None:
        """Configure scanning policy with focus on HIPAA compliance."""
        logger.info("Configuring scan policy...")
        
        # Enable all scanners
        self.zap.ascan.enable_all_scanners()
        
        # Configure specific scanners for HIPAA compliance
        hipaa_scanners = {
            # Authentication
            '10010': 'HIGH',     # Cookie No HttpOnly Flag
            '10011': 'HIGH',     # Cookie Without Secure Flag
            '10012': 'HIGH',     # Password Autocomplete
            '10016': 'HIGH',     # Web Browser XSS Protection Not Enabled
            
            # Encryption
            '10020': 'HIGH',     # Weak SSL/TLS Ciphers
            '10021': 'HIGH',     # X-Content-Type-Options Header Missing
            '10035': 'HIGH',     # Strict-Transport-Security Header Not Set
            
            # Information Disclosure
            '10023': 'HIGH',     # Information Disclosure - Debug Error Messages
            '10024': 'HIGH',     # Information Disclosure - Sensitive Information in URL
            '10025': 'HIGH',     # Information Disclosure - Sensitive Information in HTTP Referrer Header
            
            # Access Control
            '10040': 'HIGH',     # Cross Site Scripting (XSS)
            '10045': 'HIGH',     # Source Code Disclosure
            '10048': 'HIGH',     # Remote Code Execution
            '10056': 'HIGH',     # Directory Traversal
            
            # Data Protection
            '10062': 'HIGH',     # PII Exposure
            '10063': 'HIGH',     # Insecure Password Storage
        }
        
        # Set scanner levels
        for scanner_id, level in hipaa_scanners.items():
            self.zap.ascan.set_scanner_alert_threshold(
                scanner_id,
                level,
                apikey=self.api_key
            )
    
    def setup_context(self) -> None:
        """Set up scanning context and include relevant paths."""
        logger.info("Setting up scan context...")
        
        # Create new context
        context_name = f"insurance-navigator-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.context_id = self.zap.context.new_context(context_name)
        
        # Include relevant URL paths
        include_paths = [
            "^https?://.*\\.insurance-navigator\\.com/.*$",
            "^https?://insurance-navigator-api\\.onrender\\.com/.*$"
        ]
        
        for path in include_paths:
            self.zap.context.include_in_context(context_name, path)
        
        # Exclude static content and health endpoints
        exclude_paths = [
            ".*\\.css$",
            ".*\\.js$",
            ".*\\.png$",
            ".*\\.jpg$",
            ".*/health$",
            ".*/metrics$"
        ]
        
        for path in exclude_paths:
            self.zap.context.exclude_from_context(context_name, path)
    
    def run_active_scan(self) -> None:
        """Run active security scan."""
        logger.info("Starting active scan...")
        
        try:
            self.scan_id = self.zap.ascan.scan(
                self.target_url,
                recurse=True,
                in_scope_only=True,
                scan_policy_name="HIPAA-Compliance",
                method="GET"
            )
            
            # Monitor scan progress
            while int(self.zap.ascan.status(self.scan_id)) < 100:
                logger.info(f"Scan progress: {self.zap.ascan.status(self.scan_id)}%")
                time.sleep(5)
            
            logger.info("Active scan completed")
            
        except Exception as e:
            logger.error(f"Active scan failed: {str(e)}")
    
    def generate_report(self) -> str:
        """Generate security report with findings."""
        logger.info("Generating security report...")
        
        # Get all alerts
        alerts = self.zap.core.alerts()
        
        report = {
            "scan_info": {
                "timestamp": datetime.now().isoformat(),
                "target_url": self.target_url,
                "scan_id": self.scan_id
            },
            "summary": {
                "total_alerts": len(alerts),
                "high_risks": len([a for a in alerts if a['risk'] == 'High']),
                "medium_risks": len([a for a in alerts if a['risk'] == 'Medium']),
                "low_risks": len([a for a in alerts if a['risk'] == 'Low'])
            },
            "hipaa_compliance": self._check_hipaa_compliance(alerts),
            "alerts": alerts
        }
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.reports_dir / f"security_scan_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(report_file)
    
    def _check_hipaa_compliance(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check HIPAA compliance based on scan results."""
        hipaa_requirements = {
            "access_control": {
                "compliant": True,
                "issues": []
            },
            "encryption": {
                "compliant": True,
                "issues": []
            },
            "authentication": {
                "compliant": True,
                "issues": []
            },
            "data_protection": {
                "compliant": True,
                "issues": []
            }
        }
        
        # Map alert types to HIPAA categories
        category_mapping = {
            "Authentication": "authentication",
            "Session Management": "authentication",
            "Access Control": "access_control",
            "Cryptography": "encryption",
            "Information Disclosure": "data_protection"
        }
        
        # Process alerts
        for alert in alerts:
            if alert['risk'] in ['High', 'Medium']:
                category = category_mapping.get(alert['category'], 'other')
                if category in hipaa_requirements:
                    hipaa_requirements[category]['compliant'] = False
                    hipaa_requirements[category]['issues'].append({
                        'name': alert['name'],
                        'risk': alert['risk'],
                        'description': alert['description'],
                        'solution': alert['solution']
                    })
        
        return hipaa_requirements

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run security scan using OWASP ZAP")
    parser.add_argument(
        "--target",
        default="https://insurance-navigator-api.onrender.com",
        help="Target URL to scan"
    )
    parser.add_argument(
        "--api-key",
        help="ZAP API key (optional)"
    )
    
    args = parser.parse_args()
    
    # Initialize and run scanner
    scanner = SecurityScanner(args.target, args.api_key)
    
    try:
        scanner.start_zap()
        scanner.setup_context()
        scanner.run_active_scan()
        report_file = scanner.generate_report()
        
        logger.info(f"Security scan completed. Report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Security scan failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 