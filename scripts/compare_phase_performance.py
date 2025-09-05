#!/usr/bin/env python3
"""
Phase Performance Comparison Script
Phase 2: Cloud Deployment Testing
Compares cloud deployment performance against Phase 1 local Docker baselines
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class PerformanceMetrics:
    """Performance metrics for a service"""
    service: str
    environment: str
    response_time_avg: float
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    response_time_max: float
    success_rate: float
    error_rate: float
    timestamp: str
    test_duration: float
    sample_count: int

@dataclass
class ComparisonResult:
    """Result of performance comparison"""
    service: str
    metric: str
    phase1_value: float
    phase2_value: float
    difference: float
    difference_percent: float
    status: str  # 'improved', 'degraded', 'similar'
    threshold: float

class PerformanceComparator:
    """Compares performance between Phase 1 and Phase 2 deployments"""
    
    def __init__(self, phase1_baseline_file: str = None, phase2_config_file: str = None):
        self.phase1_baseline_file = phase1_baseline_file or "phase1_performance_baseline.json"
        self.phase2_config_file = phase2_config_file or "env.workflow-testing-cloud"
        self.phase1_baselines = self._load_phase1_baselines()
        self.phase2_services = self._load_phase2_services()
        
        # Performance thresholds
        self.thresholds = {
            'response_time_degradation': 0.10,  # 10% degradation acceptable
            'success_rate_degradation': 0.01,   # 1% success rate degradation acceptable
            'error_rate_increase': 0.01         # 1% error rate increase acceptable
        }
    
    def _load_phase1_baselines(self) -> Dict[str, PerformanceMetrics]:
        """Load Phase 1 performance baselines"""
        if os.path.exists(self.phase1_baseline_file):
            with open(self.phase1_baseline_file, 'r') as f:
                data = json.load(f)
                return {
                    service: PerformanceMetrics(**metrics)
                    for service, metrics in data.items()
                }
        else:
            print(f"Warning: Phase 1 baseline file not found: {self.phase1_baseline_file}")
            return {}
    
    def _load_phase2_services(self) -> Dict[str, str]:
        """Load Phase 2 service URLs"""
        services = {}
        
        # Default URLs
        api_url = os.getenv('RENDER_API_URL', 'https://insurance-navigator-api-workflow-testing.onrender.com')
        frontend_url = os.getenv('VERCEL_URL', 'https://insurance-navigator-frontend-workflow-testing.vercel.app')
        
        # Try to load from environment file
        if os.path.exists(self.phase2_config_file):
            with open(self.phase2_config_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        if key == 'RENDER_API_URL':
                            api_url = value
                        elif key == 'VERCEL_URL':
                            frontend_url = value
        
        services = {
            'api': api_url,
            'frontend': frontend_url
        }
        
        return services
    
    def _make_request(self, url: str, timeout: int = 30) -> Tuple[bool, float, Optional[str]]:
        """Make HTTP request and return success, response_time, error"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return True, response_time, None
            else:
                return False, response_time, f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, timeout, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, 0, "Connection error"
        except Exception as e:
            return False, 0, str(e)
    
    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """Calculate percentiles for response times"""
        if not values:
            return {}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            'p50': sorted_values[int(n * 0.5)],
            'p95': sorted_values[int(n * 0.95)],
            'p99': sorted_values[int(n * 0.99)]
        }
    
    def measure_service_performance(self, service_name: str, url: str, sample_count: int = 10) -> PerformanceMetrics:
        """Measure performance metrics for a service"""
        print(f"Measuring {service_name} performance...")
        
        response_times = []
        success_count = 0
        error_count = 0
        start_time = time.time()
        
        for i in range(sample_count):
            success, response_time, error = self._make_request(url)
            response_times.append(response_time)
            
            if success:
                success_count += 1
            else:
                error_count += 1
                if i < 3:  # Log first few errors
                    print(f"  Error {i+1}: {error}")
            
            # Small delay between requests
            time.sleep(0.1)
        
        test_duration = time.time() - start_time
        
        # Calculate metrics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            percentiles = self._calculate_percentiles(response_times)
        else:
            avg_response_time = 0
            max_response_time = 0
            percentiles = {'p50': 0, 'p95': 0, 'p99': 0}
        
        success_rate = success_count / sample_count
        error_rate = error_count / sample_count
        
        return PerformanceMetrics(
            service=service_name,
            environment='phase2_cloud',
            response_time_avg=avg_response_time,
            response_time_p50=percentiles.get('p50', 0),
            response_time_p95=percentiles.get('p95', 0),
            response_time_p99=percentiles.get('p99', 0),
            response_time_max=max_response_time,
            success_rate=success_rate,
            error_rate=error_rate,
            timestamp=datetime.now().isoformat(),
            test_duration=test_duration,
            sample_count=sample_count
        )
    
    def compare_metrics(self, phase1_metrics: PerformanceMetrics, phase2_metrics: PerformanceMetrics) -> List[ComparisonResult]:
        """Compare metrics between Phase 1 and Phase 2"""
        comparisons = []
        
        # Response time comparisons
        response_time_metrics = [
            ('response_time_avg', 'Average Response Time'),
            ('response_time_p50', 'P50 Response Time'),
            ('response_time_p95', 'P95 Response Time'),
            ('response_time_p99', 'P99 Response Time'),
            ('response_time_max', 'Max Response Time')
        ]
        
        for metric, description in response_time_metrics:
            phase1_value = getattr(phase1_metrics, metric)
            phase2_value = getattr(phase2_metrics, metric)
            
            if phase1_value > 0:
                difference = phase2_value - phase1_value
                difference_percent = (difference / phase1_value) * 100
                
                # Determine status
                if difference_percent <= self.thresholds['response_time_degradation'] * 100:
                    status = 'similar'
                elif difference_percent > 0:
                    status = 'degraded'
                else:
                    status = 'improved'
                
                comparisons.append(ComparisonResult(
                    service=phase1_metrics.service,
                    metric=description,
                    phase1_value=phase1_value,
                    phase2_value=phase2_value,
                    difference=difference,
                    difference_percent=difference_percent,
                    status=status,
                    threshold=self.thresholds['response_time_degradation'] * 100
                ))
        
        # Success rate comparison
        success_rate_diff = phase2_metrics.success_rate - phase1_metrics.success_rate
        success_rate_diff_percent = success_rate_diff * 100
        
        if success_rate_diff_percent >= -self.thresholds['success_rate_degradation'] * 100:
            success_status = 'similar'
        elif success_rate_diff_percent < 0:
            success_status = 'degraded'
        else:
            success_status = 'improved'
        
        comparisons.append(ComparisonResult(
            service=phase1_metrics.service,
            metric='Success Rate',
            phase1_value=phase1_metrics.success_rate,
            phase2_value=phase2_metrics.success_rate,
            difference=success_rate_diff,
            difference_percent=success_rate_diff_percent,
            status=success_status,
            threshold=self.thresholds['success_rate_degradation'] * 100
        ))
        
        # Error rate comparison
        error_rate_diff = phase2_metrics.error_rate - phase1_metrics.error_rate
        error_rate_diff_percent = error_rate_diff * 100
        
        if error_rate_diff_percent <= self.thresholds['error_rate_increase'] * 100:
            error_status = 'similar'
        elif error_rate_diff_percent > 0:
            error_status = 'degraded'
        else:
            error_status = 'improved'
        
        comparisons.append(ComparisonResult(
            service=phase1_metrics.service,
            metric='Error Rate',
            phase1_value=phase1_metrics.error_rate,
            phase2_value=phase2_metrics.error_rate,
            difference=error_rate_diff,
            difference_percent=error_rate_diff_percent,
            status=error_status,
            threshold=self.thresholds['error_rate_increase'] * 100
        ))
        
        return comparisons
    
    def run_comparison(self, sample_count: int = 10) -> Dict[str, List[ComparisonResult]]:
        """Run performance comparison between Phase 1 and Phase 2"""
        print("Starting Phase 2 vs Phase 1 performance comparison")
        print("=" * 60)
        
        results = {}
        
        for service_name, service_url in self.phase2_services.items():
            print(f"\nAnalyzing {service_name.upper()} service...")
            
            # Check if we have Phase 1 baseline for this service
            if service_name not in self.phase1_baselines:
                print(f"  Warning: No Phase 1 baseline found for {service_name}")
                continue
            
            # Measure Phase 2 performance
            phase2_metrics = self.measure_service_performance(service_name, service_url, sample_count)
            
            # Compare with Phase 1 baseline
            phase1_metrics = self.phase1_baselines[service_name]
            comparisons = self.compare_metrics(phase1_metrics, phase2_metrics)
            
            results[service_name] = comparisons
            
            # Print summary for this service
            print(f"  Phase 1 baseline: {phase1_metrics.response_time_avg:.2f}s avg, {phase1_metrics.success_rate:.1%} success")
            print(f"  Phase 2 current:  {phase2_metrics.response_time_avg:.2f}s avg, {phase2_metrics.success_rate:.1%} success")
        
        return results
    
    def print_comparison_results(self, results: Dict[str, List[ComparisonResult]], json_output: bool = False):
        """Print comparison results"""
        if json_output:
            # JSON output for programmatic use
            output = {
                'timestamp': datetime.now().isoformat(),
                'comparison_results': {}
            }
            
            for service, comparisons in results.items():
                output['comparison_results'][service] = [
                    asdict(comparison) for comparison in comparisons
                ]
            
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            print("\n" + "=" * 60)
            print("PERFORMANCE COMPARISON RESULTS")
            print("=" * 60)
            
            for service, comparisons in results.items():
                print(f"\n{service.upper()} SERVICE")
                print("-" * 40)
                
                for comparison in comparisons:
                    status_symbol = {
                        'improved': '📈',
                        'degraded': '📉',
                        'similar': '➡️'
                    }.get(comparison.status, '❓')
                    
                    print(f"{status_symbol} {comparison.metric}")
                    print(f"   Phase 1: {comparison.phase1_value:.3f}")
                    print(f"   Phase 2: {comparison.phase2_value:.3f}")
                    print(f"   Change:  {comparison.difference:+.3f} ({comparison.difference_percent:+.1f}%)")
                    print(f"   Status:  {comparison.status.upper()}")
                    print()
            
            # Overall summary
            print("=" * 60)
            print("OVERALL SUMMARY")
            print("=" * 60)
            
            total_comparisons = sum(len(comparisons) for comparisons in results.values())
            improved_count = sum(
                len([c for c in comparisons if c.status == 'improved'])
                for comparisons in results.values()
            )
            degraded_count = sum(
                len([c for c in comparisons if c.status == 'degraded'])
                for comparisons in results.values()
            )
            similar_count = sum(
                len([c for c in comparisons if c.status == 'similar'])
                for comparisons in results.values()
            )
            
            print(f"Total comparisons: {total_comparisons}")
            print(f"Improved: {improved_count}")
            print(f"Similar: {similar_count}")
            print(f"Degraded: {degraded_count}")
            
            if degraded_count == 0:
                print("\n🎉 All metrics maintained or improved in Phase 2!")
            elif degraded_count <= 2:
                print("\n⚠️  Some metrics degraded, but overall performance is acceptable.")
            else:
                print("\n❌ Multiple metrics degraded. Consider investigating performance issues.")
    
    def save_phase2_baseline(self, metrics: Dict[str, PerformanceMetrics]):
        """Save Phase 2 metrics as new baseline"""
        baseline_data = {
            service: asdict(metrics) for service, metrics in metrics.items()
        }
        
        filename = f"phase2_performance_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        print(f"Phase 2 baseline saved to: {filename}")

def main():
    parser = argparse.ArgumentParser(description='Compare Phase 2 cloud performance with Phase 1 baselines')
    parser.add_argument('--sample-count', type=int, default=10, help='Number of samples to collect per service')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--phase1-baseline', help='Path to Phase 1 baseline file')
    parser.add_argument('--phase2-config', help='Path to Phase 2 configuration file')
    parser.add_argument('--save-baseline', action='store_true', help='Save Phase 2 metrics as new baseline')
    
    args = parser.parse_args()
    
    # Load environment variables
    config_file = args.phase2_config or 'env.workflow-testing-cloud'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Run comparison
    comparator = PerformanceComparator(args.phase1_baseline, config_file)
    results = comparator.run_comparison(args.sample_count)
    
    # Print results
    comparator.print_comparison_results(results, args.json)
    
    # Save baseline if requested
    if args.save_baseline:
        # This would require collecting metrics first
        print("Note: Use --sample-count with --save-baseline to collect and save new baseline")

if __name__ == '__main__':
    main()
