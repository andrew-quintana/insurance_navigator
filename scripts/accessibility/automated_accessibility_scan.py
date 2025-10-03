#!/usr/bin/env python3
"""
Automated Accessibility Scanner

This script performs automated accessibility scanning of the deployed frontend,
checking for WCAG 2.1 AA compliance and accessibility issues.
"""

import asyncio
import aiohttp
import json
import sys
import os
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedAccessibilityScanner:
    """Automated accessibility scanner for web applications"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.session = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "scans": [],
            "summary": {
                "total_issues": 0,
                "critical_issues": 0,
                "warning_issues": 0,
                "info_issues": 0,
                "overall_score": 0.0
            }
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scan_frontend_accessibility(self) -> Dict[str, Any]:
        """Perform comprehensive accessibility scan of the frontend"""
        logger.info("Starting automated accessibility scan")
        
        if not self.config.get('vercel_url'):
            raise ValueError("Frontend URL not configured")
        
        try:
            # Get the frontend HTML
            async with self.session.get(self.config['vercel_url']) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch frontend: HTTP {response.status}")
                
                html_content = await response.text()
            
            # Perform various accessibility scans
            scans = [
                await self._scan_color_contrast(html_content),
                await self._scan_keyboard_navigation(html_content),
                await self._scan_semantic_markup(html_content),
                await self._scan_form_accessibility(html_content),
                await self._scan_aria_support(html_content),
                await self._scan_image_accessibility(html_content),
                await self._scan_heading_structure(html_content),
                await self._scan_link_accessibility(html_content)
            ]
            
            # Compile results
            self.results["scans"] = scans
            self._calculate_summary()
            
            return self.results
            
        except Exception as e:
            logger.error(f"Accessibility scan failed: {e}")
            raise
    
    async def _scan_color_contrast(self, html_content: str) -> Dict[str, Any]:
        """Scan for color contrast issues"""
        logger.info("Scanning color contrast...")
        
        issues = []
        recommendations = []
        
        # Check for CSS color definitions
        color_patterns = [
            r'color:\s*([^;]+)',
            r'background-color:\s*([^;]+)',
            r'background:\s*([^;]+)'
        ]
        
        colors_found = 0
        for pattern in color_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            colors_found += len(matches)
        
        if colors_found == 0:
            issues.append("No color definitions found - may indicate missing CSS")
            recommendations.append("Ensure CSS is properly loaded with color definitions")
        
        # Check for high contrast theme support
        if 'high-contrast' not in html_content.lower() and 'contrast' not in html_content.lower():
            issues.append("No high contrast theme support detected")
            recommendations.append("Implement high contrast theme for better accessibility")
        
        # Check for color-only information
        color_only_patterns = [
            r'color:\s*red',
            r'color:\s*green',
            r'color:\s*blue'
        ]
        
        for pattern in color_only_patterns:
            if re.search(pattern, html_content, re.IGNORECASE):
                issues.append("Color-only information detected")
                recommendations.append("Use additional indicators beyond color for important information")
        
        return {
            "scan_type": "color_contrast",
            "issues": issues,
            "recommendations": recommendations,
            "severity": "warning" if issues else "info"
        }
    
    async def _scan_keyboard_navigation(self, html_content: str) -> Dict[str, Any]:
        """Scan for keyboard navigation support"""
        logger.info("Scanning keyboard navigation...")
        
        issues = []
        recommendations = []
        
        # Check for focusable elements
        focusable_elements = re.findall(r'<(?:a|button|input|select|textarea)', html_content, re.IGNORECASE)
        
        if len(focusable_elements) == 0:
            issues.append("No focusable elements found")
            recommendations.append("Add interactive elements that can be focused with keyboard")
        else:
            # Check for tabindex usage
            tabindex_matches = re.findall(r'tabindex\s*=\s*["\']?(\d+)["\']?', html_content, re.IGNORECASE)
            positive_tabindex = [t for t in tabindex_matches if int(t) > 0]
            
            if positive_tabindex:
                issues.append(f"Found {len(positive_tabindex)} elements with positive tabindex")
                recommendations.append("Avoid positive tabindex values as they can disrupt natural tab order")
            
            # Check for skip links
            skip_links = re.findall(r'href\s*=\s*["\'][^"\']*#', html_content, re.IGNORECASE)
            if len(skip_links) == 0:
                issues.append("No skip links found")
                recommendations.append("Implement skip links for keyboard users to bypass navigation")
        
        return {
            "scan_type": "keyboard_navigation",
            "issues": issues,
            "recommendations": recommendations,
            "severity": "warning" if issues else "info"
        }
    
    async def _scan_semantic_markup(self, html_content: str) -> Dict[str, Any]:
        """Scan for semantic markup"""
        logger.info("Scanning semantic markup...")
        
        issues = []
        recommendations = []
        
        # Check for semantic HTML5 elements
        semantic_elements = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer']
        found_semantic = []
        
        for element in semantic_elements:
            if f'<{element}' in html_content.lower():
                found_semantic.append(element)
        
        if len(found_semantic) < 3:
            issues.append(f"Only {len(found_semantic)} semantic HTML5 elements found")
            recommendations.append("Use more semantic HTML5 elements for better structure")
        
        # Check for heading structure
        headings = re.findall(r'<h([1-6])', html_content, re.IGNORECASE)
        if len(headings) == 0:
            issues.append("No heading elements found")
            recommendations.append("Implement proper heading structure for content hierarchy")
        else:
            # Check heading hierarchy
            heading_levels = [int(h) for h in headings]
            if max(heading_levels) > 3:
                issues.append("Heading levels go beyond h3 - may indicate poor structure")
                recommendations.append("Limit heading levels to h1-h3 for better structure")
        
        return {
            "scan_type": "semantic_markup",
            "issues": issues,
            "recommendations": recommendations,
            "severity": "warning" if issues else "info"
        }
    
    async def _scan_form_accessibility(self, html_content: str) -> Dict[str, Any]:
        """Scan for form accessibility"""
        logger.info("Scanning form accessibility...")
        
        issues = []
        recommendations = []
        
        # Check for forms
        forms = re.findall(r'<form[^>]*>', html_content, re.IGNORECASE)
        
        if len(forms) == 0:
            # No forms to check
            return {
                "scan_type": "form_accessibility",
                "issues": [],
                "recommendations": [],
                "severity": "info"
            }
        
        # Check for form labels
        inputs = re.findall(r'<input[^>]*>', html_content, re.IGNORECASE)
        labels = re.findall(r'<label[^>]*>', html_content, re.IGNORECASE)
        
        if len(inputs) > len(labels):
            issues.append(f"Found {len(inputs)} inputs but only {len(labels)} labels")
            recommendations.append("Add labels to all form inputs for better accessibility")
        
        # Check for fieldset and legend
        fieldsets = re.findall(r'<fieldset[^>]*>', html_content, re.IGNORECASE)
        legends = re.findall(r'<legend[^>]*>', html_content, re.IGNORECASE)
        
        if len(fieldsets) > 0 and len(legends) < len(fieldsets):
            issues.append("Fieldsets without legends found")
            recommendations.append("Add legends to all fieldsets for better grouping")
        
        # Check for error handling
        error_indicators = re.findall(r'(?:error|invalid|required)', html_content, re.IGNORECASE)
        if len(error_indicators) == 0 and len(inputs) > 0:
            issues.append("No error handling indicators found")
            recommendations.append("Implement accessible error handling for form validation")
        
        return {
            "scan_type": "form_accessibility",
            "issues": issues,
            "recommendations": recommendations,
            "severity": "warning" if issues else "info"
        }
    
    async def _scan_aria_support(self, html_content: str) -> Dict[str, Any]:
        """Scan for ARIA support"""
        logger.info("Scanning ARIA support...")
        
        issues = []
        recommendations = []
        
        # Check for ARIA attributes
        aria_attributes = [
            'aria-label', 'aria-labelledby', 'aria-describedby',
            'aria-expanded', 'aria-hidden', 'aria-live', 'aria-required'
        ]
        
        found_aria = []
        for attr in aria_attributes:
            if attr in html_content.lower():
                found_aria.append(attr)
        
        if len(found_aria) == 0:
            issues.append("No ARIA attributes found")
            recommendations.append("Add ARIA attributes to improve screen reader support")
        elif len(found_aria) < 3:
            issues.append(f"Limited ARIA support - only {len(found_aria)} attributes found")
            recommendations.append("Expand ARIA usage for better accessibility")
        
        # Check for ARIA roles
        roles = re.findall(r'role\s*=\s*["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        if len(roles) == 0:
            issues.append("No ARIA roles found")
            recommendations.append("Add ARIA roles to improve semantic structure")
        
        return {
            "scan_type": "aria_support",
            "issues": issues,
            "recommendations": recommendations,
            "severity": "warning" if issues else "info"
        }
    
    async def _scan_image_accessibility(self, html_content: str) -> Dict[str, Any]:
        """Scan for image accessibility"""
        logger.info("Scanning image accessibility...")
        
        issues = []
        recommendations = []
        
        # Find all images
        images = re.findall(r'<img[^>]*>', html_content, re.IGNORECASE)
        
        if len(images) == 0:
            # No images to check
            return {
                "scan_type": "image_accessibility",
                "issues": [],
                "recommendations": [],
                "severity": "info"
            }
        
        # Check for alt text
        images_without_alt = 0
        for img in images:
            if 'alt=' not in img.lower() and 'aria-label=' not in img.lower():
                images_without_alt += 1
        
        if images_without_alt > 0:
            issues.append(f"{images_without_alt} images without alt text found")
            recommendations.append("Add alt text to all images for screen reader accessibility")
        
        # Check for decorative images
        decorative_images = re.findall(r'alt\s*=\s*["\']?["\']', html_content, re.IGNORECASE)
        if len(decorative_images) > 0:
            recommendations.append("Consider using aria-hidden for purely decorative images")
        
        return {
            "scan_type": "image_accessibility",
            "issues": issues,
            "recommendations": recommendations,
            "severity": "warning" if issues else "info"
        }
    
    async def _scan_heading_structure(self, html_content: str) -> Dict[str, Any]:
        """Scan for heading structure"""
        logger.info("Scanning heading structure...")
        
        issues = []
        recommendations = []
        
        # Extract heading levels
        headings = re.findall(r'<h([1-6])[^>]*>', html_content, re.IGNORECASE)
        
        if len(headings) == 0:
            issues.append("No heading elements found")
            recommendations.append("Implement proper heading structure for content hierarchy")
            return {
                "scan_type": "heading_structure",
                "issues": issues,
                "recommendations": recommendations,
                "severity": "warning"
            }
        
        # Check for multiple h1 elements
        h1_count = headings.count('1')
        if h1_count > 1:
            issues.append(f"Found {h1_count} h1 elements - should have only one")
            recommendations.append("Use only one h1 element per page for proper document structure")
        
        # Check heading hierarchy
        heading_levels = [int(h) for h in headings]
        for i in range(1, len(heading_levels)):
            if heading_levels[i] > heading_levels[i-1] + 1:
                issues.append("Heading hierarchy skips levels")
                recommendations.append("Maintain proper heading hierarchy (h1 > h2 > h3, etc.)")
                break
        
        return {
            "scan_type": "heading_structure",
            "issues": issues,
            "recommendations": recommendations,
            "severity": "warning" if issues else "info"
        }
    
    async def _scan_link_accessibility(self, html_content: str) -> Dict[str, Any]:
        """Scan for link accessibility"""
        logger.info("Scanning link accessibility...")
        
        issues = []
        recommendations = []
        
        # Find all links
        links = re.findall(r'<a[^>]*>([^<]*)</a>', html_content, re.IGNORECASE)
        
        if len(links) == 0:
            # No links to check
            return {
                "scan_type": "link_accessibility",
                "issues": [],
                "recommendations": [],
                "severity": "info"
            }
        
        # Check for descriptive link text
        non_descriptive_links = 0
        for link_text in links:
            link_text = link_text.strip()
            if len(link_text) < 3 or link_text.lower() in ['click here', 'read more', 'here', 'more']:
                non_descriptive_links += 1
        
        if non_descriptive_links > 0:
            issues.append(f"{non_descriptive_links} links with non-descriptive text found")
            recommendations.append("Use descriptive link text that explains the destination")
        
        # Check for links without href
        links_without_href = re.findall(r'<a[^>]*(?!href)[^>]*>', html_content, re.IGNORECASE)
        if len(links_without_href) > 0:
            issues.append(f"{len(links_without_href)} links without href attribute found")
            recommendations.append("Add href attributes to all links or use buttons for actions")
        
        return {
            "scan_type": "link_accessibility",
            "issues": issues,
            "recommendations": recommendations,
            "severity": "warning" if issues else "info"
        }
    
    def _calculate_summary(self):
        """Calculate summary statistics"""
        total_issues = 0
        critical_issues = 0
        warning_issues = 0
        info_issues = 0
        
        for scan in self.results["scans"]:
            issue_count = len(scan["issues"])
            total_issues += issue_count
            
            if scan["severity"] == "critical":
                critical_issues += issue_count
            elif scan["severity"] == "warning":
                warning_issues += issue_count
            else:
                info_issues += issue_count
        
        # Calculate overall score (higher is better)
        if total_issues == 0:
            overall_score = 1.0
        else:
            # Penalize critical issues more heavily
            score_penalty = (critical_issues * 0.1) + (warning_issues * 0.05) + (info_issues * 0.02)
            overall_score = max(0.0, 1.0 - score_penalty)
        
        self.results["summary"] = {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "info_issues": info_issues,
            "overall_score": overall_score
        }
    
    def generate_report(self) -> str:
        """Generate human-readable accessibility report"""
        report = []
        report.append("🔍 Automated Accessibility Scan Report")
        report.append("=" * 50)
        report.append(f"Timestamp: {self.results['timestamp']}")
        report.append(f"Overall Score: {self.results['summary']['overall_score']:.2f}")
        report.append("")
        
        # Summary
        summary = self.results['summary']
        report.append("📊 Summary:")
        report.append(f"  Total Issues: {summary['total_issues']}")
        report.append(f"  Critical: {summary['critical_issues']}")
        report.append(f"  Warnings: {summary['warning_issues']}")
        report.append(f"  Info: {summary['info_issues']}")
        report.append("")
        
        # Detailed results
        report.append("📋 Detailed Results:")
        for scan in self.results['scans']:
            report.append(f"\n{scan['scan_type'].replace('_', ' ').title()}:")
            report.append(f"  Severity: {scan['severity']}")
            
            if scan['issues']:
                report.append("  Issues:")
                for issue in scan['issues']:
                    report.append(f"    • {issue}")
            
            if scan['recommendations']:
                report.append("  Recommendations:")
                for rec in scan['recommendations']:
                    report.append(f"    • {rec}")
        
        return "\n".join(report)

async def main():
    """Main function to run accessibility scan"""
    config = {
        "vercel_url": os.getenv("VERCEL_URL", "https://insurance-navigator.vercel.app"),
        "api_url": os.getenv("API_URL", "https://insurance-navigator-api.onrender.com"),
        "supabase_url": os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
    }
    
    try:
        async with AutomatedAccessibilityScanner(config) as scanner:
            results = await scanner.scan_frontend_accessibility()
            
            # Print report
            report = scanner.generate_report()
            print(report)
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"accessibility_scan_{timestamp}.json"
            filepath = Path(__file__).parent / filename
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📁 Results saved to: {filepath}")
            
            # Exit with appropriate code
            if results['summary']['overall_score'] >= 0.8:
                print("\n✅ Accessibility scan completed successfully!")
                sys.exit(0)
            else:
                print("\n⚠️ Accessibility issues found!")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Accessibility scan failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
