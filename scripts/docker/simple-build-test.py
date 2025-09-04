#!/usr/bin/env python3
"""
Simple Docker Build Performance Test
Measures build times for different Docker configurations
"""

import subprocess
import time
import json
from datetime import datetime

def test_build(dockerfile, tag, context="."):
    """Test a single Docker build and return timing info"""
    print(f"🔨 Testing {dockerfile}...")
    
    start_time = time.time()
    
    try:
        cmd = ["docker", "build", "-f", dockerfile, "-t", tag, context, "--no-cache"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        
        build_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {dockerfile} built successfully in {build_time:.2f} seconds")
            return {
                "dockerfile": dockerfile,
                "tag": tag,
                "build_time": build_time,
                "success": True,
                "error": None
            }
        else:
            print(f"❌ {dockerfile} failed: {result.stderr[:200]}...")
            return {
                "dockerfile": dockerfile,
                "tag": tag,
                "build_time": build_time,
                "success": False,
                "error": result.stderr
            }
    except subprocess.TimeoutExpired:
        print(f"⏰ {dockerfile} timed out after 30 minutes")
        return {
            "dockerfile": dockerfile,
            "tag": tag,
            "build_time": time.time() - start_time,
            "success": False,
            "error": "Build timeout"
        }
    except Exception as e:
        print(f"💥 {dockerfile} error: {str(e)}")
        return {
            "dockerfile": dockerfile,
            "tag": tag,
            "build_time": time.time() - start_time,
            "success": False,
            "error": str(e)
        }

def main():
    print("🚀 Docker Build Performance Test")
    print("=" * 40)
    
    # Test configurations
    tests = [
        {"dockerfile": "Dockerfile.dev-fast", "tag": "insurance-navigator:dev-fast"},
        {"dockerfile": "Dockerfile.prod-optimized", "tag": "insurance-navigator:prod-optimized"},
    ]
    
    results = []
    
    for test in tests:
        result = test_build(test["dockerfile"], test["tag"])
        results.append(result)
        print()
    
    # Generate report
    successful = [r for r in results if r["success"]]
    
    print("📊 RESULTS SUMMARY")
    print("=" * 40)
    
    if successful:
        successful.sort(key=lambda x: x["build_time"])
        
        print(f"✅ Successful builds: {len(successful)}/{len(results)}")
        print()
        
        for i, result in enumerate(successful, 1):
            print(f"{i}. {result['dockerfile']}")
            print(f"   Time: {result['build_time']:.2f} seconds")
            print()
        
        if len(successful) > 1:
            fastest = successful[0]
            slowest = successful[-1]
            improvement = ((slowest["build_time"] - fastest["build_time"]) / slowest["build_time"]) * 100
            print(f"⚡ Fastest: {fastest['dockerfile']} ({fastest['build_time']:.2f}s)")
            print(f"🐌 Slowest: {slowest['dockerfile']} ({slowest['build_time']:.2f}s)")
            print(f"📈 Improvement: {improvement:.1f}% faster")
    else:
        print("❌ No successful builds")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"build-test-results-{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "total_tests": len(results),
                "successful_tests": len(successful),
                "fastest_build": successful[0] if successful else None
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to {results_file}")

if __name__ == "__main__":
    main()
