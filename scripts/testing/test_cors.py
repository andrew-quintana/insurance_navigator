#!/usr/bin/env python3
"""
Enhanced CORS Testing and Validation System

Comprehensive testing for:
- Current Vercel deployment URLs
- Pattern-based validation
- Real-time CORS endpoint testing
- Future deployment prediction
- Error monitoring and alerting
"""

import asyncio
import aiohttp
import re
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CORSValidator:
    """Enhanced CORS validation and testing system."""
    
    def __init__(self):
        self.patterns = self._compile_patterns()
        self.test_results = []
        
    def _compile_patterns(self):
        """Compile all CORS patterns for validation."""
        return {
            'localhost': re.compile(r'^localhost(:\d+)?$'),
            'production': [
                'insurance-navigator.vercel.app',
                'insurance-navigator-api.onrender.com'
            ],
            'vercel_preview': re.compile(r'^insurance-navigator-[a-z0-9]+-andrew-quintanas-projects\.vercel\.app$'),
            'vercel_all': re.compile(r'^[a-z0-9-]+\.vercel\.app$'),
            'vercel_harmful': re.compile(r'^insurance-navigator-[a-z0-9]+-(?!andrew-quintanas-projects).*\.vercel\.app$'),
        }
    
    def validate_origin_comprehensive(self, origin: str) -> Dict[str, Any]:
        """Comprehensive origin validation with detailed results."""
        if not origin:
            return {"valid": False, "reason": "Empty origin", "pattern": None}
        
        try:
            parsed = urlparse(origin)
            domain = parsed.netloc.lower()
            
            # Check localhost
            if self.patterns['localhost'].match(domain):
                return {
                    "valid": True, 
                    "reason": "Localhost development", 
                    "pattern": "localhost",
                    "risk_level": "low"
                }
            
            # Check production domains
            if domain in self.patterns['production']:
                return {
                    "valid": True, 
                    "reason": "Production domain", 
                    "pattern": "production",
                    "risk_level": "low"
                }
            
            # Check for potential security issues (wrong user)
            if self.patterns['vercel_harmful'].match(domain):
                return {
                    "valid": False, 
                    "reason": "Vercel deployment for different user", 
                    "pattern": "vercel_harmful",
                    "risk_level": "high",
                    "security_issue": True
                }
            
            # Check Vercel preview pattern (specific project)
            if self.patterns['vercel_preview'].match(domain):
                return {
                    "valid": True, 
                    "reason": "Authorized Vercel preview deployment", 
                    "pattern": "vercel_preview",
                    "risk_level": "low"
                }
            
            # Check any Vercel deployment (broader - should be limited)
            if self.patterns['vercel_all'].match(domain):
                return {
                    "valid": True, 
                    "reason": "Generic Vercel deployment (review needed)", 
                    "pattern": "vercel_all",
                    "risk_level": "medium",
                    "review_needed": True
                }
            
        except Exception as e:
            return {
                "valid": False, 
                "reason": f"Parse error: {e}", 
                "pattern": None,
                "risk_level": "unknown"
            }
        
        return {
            "valid": False, 
            "reason": "No matching pattern", 
            "pattern": None,
            "risk_level": "medium"
        }
    
    def generate_potential_urls(self, count: int = 20) -> List[str]:
        """Generate potential future Vercel deployment URLs for testing."""
        import random
        import string
        
        urls = []
        
        # Generate random hashes similar to Vercel pattern
        for _ in range(count):
            hash_length = random.randint(8, 12)
            hash_chars = string.ascii_lowercase + string.digits
            random_hash = ''.join(random.choice(hash_chars) for _ in range(hash_length))
            
            url = f"https://insurance-navigator-{random_hash}-andrew-quintanas-projects.vercel.app"
            urls.append(url)
        
        return urls
    
    async def test_cors_endpoint_comprehensive(self, session: aiohttp.ClientSession, backend_url: str, origin: str) -> Dict[str, Any]:
        """Comprehensive CORS endpoint testing."""
        test_result = {
            "origin": origin,
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {}
        }
        
        # Test 1: OPTIONS preflight request
        try:
            headers = {
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
            
            async with session.options(f"{backend_url}/upload-policy", headers=headers, timeout=10) as response:
                test_result["tests"]["preflight"] = {
                    "status": response.status,
                    "success": response.status == 200,
                    "cors_headers": {
                        "access_control_allow_origin": response.headers.get("Access-Control-Allow-Origin"),
                        "access_control_allow_methods": response.headers.get("Access-Control-Allow-Methods"),
                        "access_control_allow_headers": response.headers.get("Access-Control-Allow-Headers"),
                        "access_control_allow_credentials": response.headers.get("Access-Control-Allow-Credentials"),
                        "access_control_max_age": response.headers.get("Access-Control-Max-Age"),
                    }
                }
        except Exception as e:
            test_result["tests"]["preflight"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test 2: Actual GET request to health endpoint
        try:
            headers = {"Origin": origin}
            async with session.get(f"{backend_url}/health", headers=headers, timeout=10) as response:
                test_result["tests"]["health_check"] = {
                    "status": response.status,
                    "success": response.status == 200,
                    "cors_headers": {
                        "access_control_allow_origin": response.headers.get("Access-Control-Allow-Origin"),
                    },
                    "response_time": response.headers.get("X-Processing-Time")
                }
        except Exception as e:
            test_result["tests"]["health_check"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test 3: Pattern validation
        validation_result = self.validate_origin_comprehensive(origin)
        test_result["validation"] = validation_result
        
        # Overall assessment
        preflight_success = test_result["tests"].get("preflight", {}).get("success", False)
        health_success = test_result["tests"].get("health_check", {}).get("success", False)
        pattern_valid = validation_result.get("valid", False)
        
        test_result["overall"] = {
            "cors_working": preflight_success and health_success,
            "pattern_valid": pattern_valid,
            "risk_level": validation_result.get("risk_level", "unknown"),
            "needs_attention": not (preflight_success and health_success and pattern_valid)
        }
        
        return test_result
    
    async def run_comprehensive_test_suite(self, backend_url: str = None) -> Dict[str, Any]:
        """Run comprehensive CORS test suite."""
        if not backend_url:
            backend_url = "***REMOVED***"
        
        logger.info(f"🧪 Starting comprehensive CORS test suite against {backend_url}")
        
        # Test URLs - known working and potential problem cases
        test_urls = [
            # Development
            "http://localhost:3000",
            "http://localhost:3001",
            
            # Production
            "https://insurance-navigator.vercel.app",
            
            # Known preview deployments
            "https://insurance-navigator-hrf0s88oh-andrew-quintanas-projects.vercel.app",
            "https://insurance-navigator-q2ukn6eih-andrew-quintanas-projects.vercel.app",
            "https://insurance-navigator-cylkkqsmn-andrew-quintanas-projects.vercel.app",
            "https://insurance-navigator-k2ui23iaj-andrew-quintanas-projects.vercel.app",  # The failing one
            
            # Generated potential URLs
            *self.generate_potential_urls(10),
            
            # Security test cases (should be blocked)
            "https://insurance-navigator-abc123-different-user.vercel.app",
            "https://malicious-site.vercel.app",
            "https://insurance-navigator-hack-andrew-quintanas-projects.vercel.app",
        ]
        
        results = {
            "test_suite": "comprehensive_cors_validation",
            "backend_url": backend_url,
            "timestamp": datetime.utcnow().isoformat(),
            "total_urls": len(test_urls),
            "results": [],
            "summary": {}
        }
        
        async with aiohttp.ClientSession() as session:
            # Test each URL
            for i, url in enumerate(test_urls):
                logger.info(f"📋 Testing {i+1}/{len(test_urls)}: {url}")
                
                try:
                    test_result = await self.test_cors_endpoint_comprehensive(session, backend_url, url)
                    results["results"].append(test_result)
                    
                    # Log result
                    overall = test_result["overall"]
                    status = "✅ PASS" if not overall["needs_attention"] else "❌ FAIL"
                    risk = overall["risk_level"].upper()
                    logger.info(f"   {status} - Risk: {risk} - CORS: {overall['cors_working']} - Pattern: {overall['pattern_valid']}")
                    
                except Exception as e:
                    logger.error(f"   ❌ ERROR testing {url}: {e}")
                    results["results"].append({
                        "origin": url,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        # Generate summary
        working_urls = [r for r in results["results"] if r.get("overall", {}).get("cors_working", False)]
        failing_urls = [r for r in results["results"] if r.get("overall", {}).get("needs_attention", True)]
        high_risk_urls = [r for r in results["results"] if r.get("validation", {}).get("risk_level") == "high"]
        
        results["summary"] = {
            "total_tested": len(results["results"]),
            "working_count": len(working_urls),
            "failing_count": len(failing_urls),
            "high_risk_count": len(high_risk_urls),
            "success_rate": f"{(len(working_urls) / len(results['results']) * 100):.1f}%",
            "recommendations": self._generate_recommendations(results["results"])
        }
        
        return results
    
    def _generate_recommendations(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        failing_urls = [r for r in test_results if r.get("overall", {}).get("needs_attention", True)]
        high_risk_urls = [r for r in test_results if r.get("validation", {}).get("risk_level") == "high"]
        
        if failing_urls:
            recommendations.append(f"🔧 {len(failing_urls)} URLs failed CORS tests - review configuration")
        
        if high_risk_urls:
            recommendations.append(f"🚨 {len(high_risk_urls)} high-risk URLs detected - potential security issue")
        
        pattern_issues = [r for r in test_results if not r.get("validation", {}).get("valid", True)]
        if pattern_issues:
            recommendations.append(f"📝 {len(pattern_issues)} URLs don't match expected patterns - update regex")
        
        # Check for 502 errors specifically
        server_errors = [r for r in test_results if r.get("tests", {}).get("health_check", {}).get("status") in [502, 503, 504]]
        if server_errors:
            recommendations.append(f"⚠️ {len(server_errors)} server errors detected - check backend stability")
        
        if not recommendations:
            recommendations.append("✅ All tests passed - CORS configuration is working correctly")
        
        return recommendations


async def main():
    """Run the comprehensive CORS test suite."""
    print("🚀 Enhanced CORS Testing and Validation System")
    print("=" * 60)
    
    validator = CORSValidator()
    
    # Run comprehensive test suite
    results = await validator.run_comprehensive_test_suite()
    
    # Print detailed results
    print(f"\n📊 TEST RESULTS SUMMARY")
    print(f"Backend: {results['backend_url']}")
    print(f"Total URLs tested: {results['summary']['total_tested']}")
    print(f"Working: {results['summary']['working_count']}")
    print(f"Failing: {results['summary']['failing_count']}")
    print(f"High risk: {results['summary']['high_risk_count']}")
    print(f"Success rate: {results['summary']['success_rate']}")
    
    print(f"\n🔍 DETAILED RESULTS")
    print("-" * 40)
    
    for result in results["results"]:
        origin = result["origin"]
        overall = result.get("overall", {})
        validation = result.get("validation", {})
        
        status_icon = "✅" if not overall.get("needs_attention", True) else "❌"
        risk_level = validation.get("risk_level", "unknown").upper()
        cors_working = overall.get("cors_working", False)
        pattern_valid = overall.get("pattern_valid", False)
        
        print(f"{status_icon} {origin}")
        print(f"   Risk: {risk_level} | CORS: {'✓' if cors_working else '✗'} | Pattern: {'✓' if pattern_valid else '✗'}")
        
        if validation.get("security_issue"):
            print(f"   🚨 SECURITY ISSUE: {validation.get('reason')}")
        elif validation.get("review_needed"):
            print(f"   ⚠️ REVIEW NEEDED: {validation.get('reason')}")
        
        # Show specific test failures
        tests = result.get("tests", {})
        if not tests.get("preflight", {}).get("success", True):
            print(f"   ❌ Preflight failed: {tests.get('preflight', {}).get('error', 'Unknown')}")
        if not tests.get("health_check", {}).get("success", True):
            print(f"   ❌ Health check failed: {tests.get('health_check', {}).get('error', 'Unknown')}")
        
        print()
    
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 25)
    for rec in results["summary"]["recommendations"]:
        print(f"• {rec}")
    
    # Save results to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"cors_test_results_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    
    return results


def test_cors_pattern_validation():
    """Test the pattern validation logic specifically."""
    
    def validate_cors_origin(origin: str) -> bool:
        """Replicate the original validation logic for comparison."""
        if not origin:
            return False
        
        try:
            from urllib.parse import urlparse
            import re
            
            parsed = urlparse(origin)
            domain = parsed.netloc.lower()
            
            # Allow localhost for development
            if domain.startswith('localhost:') or domain == 'localhost':
                return True
            
            # Allow production domains
            production_domains = [
                'insurance-navigator.vercel.app',
                'insurance-navigator-api.onrender.com'
            ]
            if domain in production_domains:
                return True
            
            # Allow Vercel preview deployments with pattern matching
            vercel_pattern = re.compile(
                r'^insurance-navigator-[a-z0-9]+-andrew-quintanas-projects\.vercel\.app$'
            )
            if vercel_pattern.match(domain):
                return True
            
            # Allow any Vercel deployment for this project
            if (domain.endswith('andrew-quintanas-projects.vercel.app') and 
                domain.startswith('insurance-navigator-')):
                return True
                
        except Exception:
            return False
        
        return False
    
    # Test cases
    test_urls = [
        # Should PASS
        ("http://localhost:3000", True),
        ("https://insurance-navigator.vercel.app", True),
        ("https://insurance-navigator-k2ui23iaj-andrew-quintanas-projects.vercel.app", True),  # The failing one
        ("https://insurance-navigator-abc123-andrew-quintanas-projects.vercel.app", True),
        
        # Should FAIL
        ("https://malicious-site.com", False),
        ("https://insurance-navigator-abc123-different-user.vercel.app", False),
        ("", False),
        ("invalid-url", False),
    ]
    
    print("🧪 Testing CORS Pattern Validation Logic")
    print("=" * 50)
    
    validator = CORSValidator()
    all_passed = True
    
    for url, expected in test_urls:
        original_result = validate_cors_origin(url)
        enhanced_result = validator.validate_origin_comprehensive(url)
        enhanced_valid = enhanced_result.get("valid", False)
        
        original_ok = original_result == expected
        enhanced_ok = enhanced_valid == expected
        
        status = "✅ PASS" if (original_ok and enhanced_ok) else "❌ FAIL"
        
        print(f"{status} {url}")
        print(f"   Expected: {expected} | Original: {original_result} | Enhanced: {enhanced_valid}")
        
        if enhanced_result.get("security_issue"):
            print(f"   🚨 Security Issue: {enhanced_result.get('reason')}")
        elif enhanced_result.get("review_needed"):
            print(f"   ⚠️ Review Needed: {enhanced_result.get('reason')}")
        
        if not (original_ok and enhanced_ok):
            all_passed = False
            print(f"   💡 Pattern: {enhanced_result.get('pattern')} | Risk: {enhanced_result.get('risk_level')}")
        
        print()
    
    print(f"📊 Overall: {'✅ All tests passed' if all_passed else '❌ Some tests failed'}")
    return all_passed


if __name__ == "__main__":
    print("🔧 Running pattern validation tests...")
    test_cors_pattern_validation()
    
    print("\n" + "="*60 + "\n")
    
    print("🌐 Running comprehensive CORS tests...")
    asyncio.run(main()) 