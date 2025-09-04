#!/usr/bin/env python3
"""
Docker Build Performance Tester
Tests different Docker configurations and measures build times
"""

import subprocess
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import argparse

class DockerBuildTester:
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.results = []
        
    def test_dockerfile(self, dockerfile: str, tag: str, context: str = ".") -> Dict[str, Any]:
        """Test a specific Dockerfile and measure build time"""
        print(f"🔨 Testing {dockerfile}...")
        
        start_time = time.time()
        
        try:
            # Build the Docker image
            cmd = [
                "docker", "build",
                "-f", dockerfile,
                "-t", tag,
                context
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            build_time = time.time() - start_time
            
            if result.returncode == 0:
                # Get image size
                size_cmd = ["docker", "images", tag, "--format", "{{.Size}}"]
                size_result = subprocess.run(size_cmd, capture_output=True, text=True)
                image_size = size_result.stdout.strip() if size_result.returncode == 0 else "Unknown"
                
                return {
                    "dockerfile": dockerfile,
                    "tag": tag,
                    "context": context,
                    "build_time": build_time,
                    "success": True,
                    "image_size": image_size,
                    "error": None
                }
            else:
                return {
                    "dockerfile": dockerfile,
                    "tag": tag,
                    "context": context,
                    "build_time": build_time,
                    "success": False,
                    "image_size": None,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "dockerfile": dockerfile,
                "tag": tag,
                "context": context,
                "build_time": time.time() - start_time,
                "success": False,
                "image_size": None,
                "error": "Build timeout (30 minutes)"
            }
        except Exception as e:
            return {
                "dockerfile": dockerfile,
                "tag": tag,
                "context": context,
                "build_time": time.time() - start_time,
                "success": False,
                "image_size": None,
                "error": str(e)
            }
    
    def run_comparison_tests(self) -> List[Dict[str, Any]]:
        """Run tests on different Docker configurations"""
        test_configs = [
            {
                "dockerfile": "Dockerfile",
                "tag": "insurance-navigator:current",
                "context": "."
            },
            {
                "dockerfile": "Dockerfile.dev-fast",
                "tag": "insurance-navigator:dev-fast",
                "context": "."
            },
            {
                "dockerfile": "Dockerfile.prod-optimized",
                "tag": "insurance-navigator:prod-optimized",
                "context": "."
            }
        ]
        
        results = []
        for config in test_configs:
            if os.path.exists(config["dockerfile"]):
                result = self.test_dockerfile(**config)
                results.append(result)
            else:
                print(f"⚠️  {config['dockerfile']} not found, skipping...")
        
        return results
    
    def cleanup_images(self, tags: List[str]):
        """Clean up test images"""
        for tag in tags:
            try:
                subprocess.run(["docker", "rmi", tag], capture_output=True)
                print(f"🗑️  Cleaned up {tag}")
            except:
                pass
    
    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate a performance comparison report"""
        successful_results = [r for r in results if r["success"]]
        
        if not successful_results:
            return "❌ No successful builds to compare"
        
        # Sort by build time
        successful_results.sort(key=lambda x: x["build_time"])
        
        report = []
        report.append("📊 Docker Build Performance Report")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Best performer
        best = successful_results[0]
        report.append(f"🏆 Fastest Build: {best['dockerfile']}")
        report.append(f"   Time: {best['build_time']:.2f} seconds")
        report.append(f"   Size: {best['image_size']}")
        report.append("")
        
        # All results
        report.append("📈 All Results:")
        for i, result in enumerate(successful_results, 1):
            status = "✅" if result["success"] else "❌"
            report.append(f"  {i}. {status} {result['dockerfile']}")
            report.append(f"     Time: {result['build_time']:.2f}s")
            report.append(f"     Size: {result['image_size']}")
            if result["error"]:
                report.append(f"     Error: {result['error'][:100]}...")
            report.append("")
        
        # Performance comparison
        if len(successful_results) > 1:
            slowest = successful_results[-1]
            improvement = ((slowest["build_time"] - best["build_time"]) / slowest["build_time"]) * 100
            report.append(f"⚡ Performance Improvement: {improvement:.1f}% faster than slowest")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Test Docker build performance")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test images after testing")
    parser.add_argument("--output", help="Output file for results (JSON)")
    args = parser.parse_args()
    
    tester = DockerBuildTester()
    
    print("🚀 Starting Docker Build Performance Tests")
    print("=" * 50)
    
    # Run tests
    results = tester.run_comparison_tests()
    
    # Generate report
    report = tester.generate_report(results)
    print(report)
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": results,
                "report": report
            }, f, indent=2)
        print(f"\n💾 Results saved to {args.output}")
    
    # Cleanup
    if args.cleanup:
        tags = [r["tag"] for r in results if r["success"]]
        tester.cleanup_images(tags)

if __name__ == "__main__":
    main()
