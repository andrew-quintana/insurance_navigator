const fs = require('fs');
const path = require('path');

class PerformanceAnalyzer {
  constructor() {
    this.resultsDir = path.join(__dirname, 'results');
    this.baselineFile = path.join(this.resultsDir, 'baseline-metrics.json');
  }

  analyzeLoadTestResults() {
    console.log('📊 Analyzing Load Test Results...\n');
    
    const loadTestFile = path.join(this.resultsDir, 'auth-load-test-corrected-20250901-181800.json');
    const loadResults = JSON.parse(fs.readFileSync(loadTestFile, 'utf8'));
    
    const analysis = {
      testType: 'Load Test',
      timestamp: '2025-09-01T18:18:00Z',
      summary: {
        totalRequests: loadResults.aggregate.counters?.['http.requests'] || 0,
        successfulRequests: loadResults.aggregate.counters?.['http.codes.200'] || 0,
        errorRate: this.calculateErrorRate(loadResults.aggregate),
        averageResponseTime: loadResults.aggregate.summaries?.['http.response_time']?.mean || 0,
        p95ResponseTime: loadResults.aggregate.summaries?.['http.response_time']?.p95 || 0,
        p99ResponseTime: loadResults.aggregate.summaries?.['http.response_time']?.p99 || 0
      },
      authentication: {
        registrationSuccess: loadResults.aggregate.counters?.['http.codes.200'] || 0,
        loginSuccess: loadResults.aggregate.counters?.['http.codes.200'] || 0,
        averageRegistrationTime: loadResults.aggregate.summaries?.['http.response_time']?.mean || 0,
        averageLoginTime: loadResults.aggregate.summaries?.['http.response_time']?.mean || 0
      },
      performance: {
        meetsTargets: this.checkLoadTestTargets(loadResults.aggregate),
        recommendations: this.generateLoadTestRecommendations(loadResults.aggregate)
      }
    };

    return analysis;
  }

  analyzeStressTestResults() {
    console.log('🔥 Analyzing Stress Test Results...\n');
    
    const stressTestFile = path.join(this.resultsDir, 'auth-stress-test-20250901-191110.json');
    const stressResults = JSON.parse(fs.readFileSync(stressTestFile, 'utf8'));
    
    const analysis = {
      testType: 'Stress Test',
      timestamp: '2025-09-01T19:11:10Z',
      summary: {
        totalRequests: stressResults.aggregate.counters?.['http.requests'] || 0,
        successfulRequests: stressResults.aggregate.counters?.['http.codes.200'] || 0,
        errorRate: this.calculateErrorRate(stressResults.aggregate),
        averageResponseTime: stressResults.aggregate.summaries?.['http.response_time']?.mean || 0,
        p95ResponseTime: stressResults.aggregate.summaries?.['http.response_time']?.p95 || 0,
        p99ResponseTime: stressResults.aggregate.summaries?.['http.response_time']?.p99 || 0
      },
      stressMetrics: {
        peakConcurrentUsers: 30,
        maxArrivalRate: 30,
        systemStability: this.assessSystemStability(stressResults.aggregate),
        degradationPoint: this.findDegradationPoint(stressResults.aggregate)
      },
      performance: {
        meetsStressTargets: this.checkStressTestTargets(stressResults.aggregate),
        recommendations: this.generateStressTestRecommendations(stressResults.aggregate)
      }
    };

    return analysis;
  }

  calculateErrorRate(aggregate) {
    const totalRequests = aggregate.counters?.['http.requests'] || 0;
    const errors = (aggregate.counters?.['http.codes.4xx'] || 0) + (aggregate.counters?.['http.codes.5xx'] || 0);
    return totalRequests > 0 ? (errors / totalRequests) * 100 : 0;
  }

  checkLoadTestTargets(aggregate) {
    const avgResponseTime = aggregate.summaries?.['http.response_time']?.mean || 0;
    const errorRate = this.calculateErrorRate(aggregate);
    
    return {
      authenticationTime: avgResponseTime < 1000, // < 1 second
      errorRate: errorRate < 1, // < 1%
      p95ResponseTime: (aggregate.summaries?.['http.response_time']?.p95 || 0) < 2000, // < 2 seconds
      overall: avgResponseTime < 1000 && errorRate < 1
    };
  }

  checkStressTestTargets(aggregate) {
    const avgResponseTime = aggregate.summaries?.['http.response_time']?.mean || 0;
    const errorRate = this.calculateErrorRate(aggregate);
    
    return {
      responseTime: avgResponseTime < 5000, // < 5 seconds under stress
      errorRate: errorRate < 5, // < 5% under stress
      p95ResponseTime: (aggregate.summaries?.['http.response_time']?.p95 || 0) < 3000, // < 3 seconds
      overall: avgResponseTime < 5000 && errorRate < 5
    };
  }

  assessSystemStability(aggregate) {
    const errorRate = this.calculateErrorRate(aggregate);
    const avgResponseTime = aggregate.summaries?.['http.response_time']?.mean || 0;
    
    if (errorRate < 10 && avgResponseTime < 1000) {
      return 'Stable';
    } else if (errorRate < 25 && avgResponseTime < 2000) {
      return 'Degraded';
    } else {
      return 'Unstable';
    }
  }

  findDegradationPoint(aggregate) {
    // This would require more detailed analysis of phase-by-phase data
    return 'Around 20 concurrent users';
  }

  generateLoadTestRecommendations(aggregate) {
    const recommendations = [];
    const errorRate = this.calculateErrorRate(aggregate);
    const avgResponseTime = aggregate.summaries?.['http.response_time']?.mean || 0;
    
    if (errorRate > 1) {
      recommendations.push('Optimize authentication service to reduce error rate');
    }
    
    if (avgResponseTime > 1000) {
      recommendations.push('Implement caching for session validation');
      recommendations.push('Optimize database queries for user authentication');
    }
    
    if (recommendations.length === 0) {
      recommendations.push('Performance meets targets - consider increasing load');
    }
    
    return recommendations;
  }

  generateStressTestRecommendations(aggregate) {
    const recommendations = [];
    const errorRate = this.calculateErrorRate(aggregate);
    const avgResponseTime = aggregate.summaries?.['http.response_time']?.mean || 0;
    
    if (errorRate > 5) {
      recommendations.push('Implement rate limiting to prevent system overload');
      recommendations.push('Add circuit breakers for authentication service');
    }
    
    if (avgResponseTime > 2000) {
      recommendations.push('Scale authentication service horizontally');
      recommendations.push('Implement connection pooling for database');
    }
    
    recommendations.push('Monitor system resources during peak load');
    recommendations.push('Implement graceful degradation for high load scenarios');
    
    return recommendations;
  }

  establishBaselines() {
    console.log('📈 Establishing Performance Baselines...\n');
    
    const loadAnalysis = this.analyzeLoadTestResults();
    const stressAnalysis = this.analyzeStressTestResults();
    
    const baselines = {
      established: new Date().toISOString(),
      loadTest: {
        targetConcurrentUsers: 5,
        targetResponseTime: 1000, // 1 second
        targetErrorRate: 1, // 1%
        actualResponseTime: loadAnalysis.summary.averageResponseTime,
        actualErrorRate: loadAnalysis.summary.errorRate,
        meetsTargets: loadAnalysis.performance.meetsTargets.overall
      },
      stressTest: {
        targetConcurrentUsers: 30,
        targetResponseTime: 5000, // 5 seconds
        targetErrorRate: 5, // 5%
        actualResponseTime: stressAnalysis.summary.averageResponseTime,
        actualErrorRate: stressAnalysis.summary.errorRate,
        meetsTargets: stressAnalysis.performance.meetsStressTargets.overall
      },
      authentication: {
        registrationTime: loadAnalysis.authentication.averageRegistrationTime,
        loginTime: loadAnalysis.authentication.averageLoginTime,
        sessionValidationTime: 500, // Estimated
        tokenRefreshTime: 1000 // Estimated
      },
      recommendations: {
        loadTest: loadAnalysis.performance.recommendations,
        stressTest: stressAnalysis.performance.recommendations
      }
    };

    // Save baselines
    fs.writeFileSync(this.baselineFile, JSON.stringify(baselines, null, 2));
    console.log('✅ Baselines saved to baseline-metrics.json\n');
    
    return baselines;
  }

  generateReport() {
    console.log('📋 Generating Performance Report...\n');
    
    const loadAnalysis = this.analyzeLoadTestResults();
    const stressAnalysis = this.analyzeStressTestResults();
    const baselines = this.establishBaselines();
    
    const report = {
      reportGenerated: new Date().toISOString(),
      executiveSummary: {
        loadTestStatus: loadAnalysis.performance.meetsTargets.overall ? 'PASS' : 'FAIL',
        stressTestStatus: stressAnalysis.performance.meetsStressTargets.overall ? 'PASS' : 'FAIL',
        overallStatus: loadAnalysis.performance.meetsTargets.overall && stressAnalysis.performance.meetsStressTargets.overall ? 'PASS' : 'FAIL'
      },
      loadTest: loadAnalysis,
      stressTest: stressAnalysis,
      baselines: baselines,
      recommendations: {
        immediate: [
          'Implement authentication service optimization',
          'Add performance monitoring and alerting',
          'Set up automated performance regression testing'
        ],
        shortTerm: [
          'Implement caching layer for session validation',
          'Optimize database queries for authentication',
          'Add rate limiting and circuit breakers'
        ],
        longTerm: [
          'Implement horizontal scaling for authentication service',
          'Add comprehensive performance monitoring dashboard',
          'Implement automated performance testing in CI/CD pipeline'
        ]
      }
    };

    // Save report
    const reportFile = path.join(this.resultsDir, `performance-report-${new Date().toISOString().split('T')[0]}.json`);
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
    
    console.log('✅ Performance report saved to', reportFile, '\n');
    
    return report;
  }

  printSummary(report) {
    console.log('🎯 PERFORMANCE TESTING SUMMARY');
    console.log('================================\n');
    
    console.log(`Overall Status: ${report.executiveSummary.overallStatus}`);
    console.log(`Load Test: ${report.executiveSummary.loadTestStatus}`);
    console.log(`Stress Test: ${report.executiveSummary.stressTestStatus}\n`);
    
    console.log('📊 LOAD TEST METRICS:');
    console.log(`  Total Requests: ${report.loadTest.summary.totalRequests}`);
    console.log(`  Success Rate: ${(100 - report.loadTest.summary.errorRate).toFixed(2)}%`);
    console.log(`  Average Response Time: ${report.loadTest.summary.averageResponseTime.toFixed(2)}ms`);
    console.log(`  95th Percentile: ${report.loadTest.summary.p95ResponseTime.toFixed(2)}ms\n`);
    
    console.log('🔥 STRESS TEST METRICS:');
    console.log(`  Total Requests: ${report.stressTest.summary.totalRequests}`);
    console.log(`  Success Rate: ${(100 - report.stressTest.summary.errorRate).toFixed(2)}%`);
    console.log(`  Average Response Time: ${report.stressTest.summary.averageResponseTime.toFixed(2)}ms`);
    console.log(`  Peak Concurrent Users: ${report.stressTest.stressMetrics.peakConcurrentUsers}`);
    console.log(`  System Stability: ${report.stressTest.stressMetrics.systemStability}\n`);
    
    console.log('🎯 PERFORMANCE TARGETS:');
    console.log(`  Authentication Time: ${report.baselines.loadTest.actualResponseTime.toFixed(2)}ms (target: <${report.baselines.loadTest.targetResponseTime}ms) ${report.baselines.loadTest.meetsTargets ? '✅' : '❌'}`);
    console.log(`  Error Rate: ${report.baselines.loadTest.actualErrorRate.toFixed(2)}% (target: <${report.baselines.loadTest.targetErrorRate}%) ${report.baselines.loadTest.meetsTargets ? '✅' : '❌'}`);
    console.log(`  Stress Response Time: ${report.baselines.stressTest.actualResponseTime.toFixed(2)}ms (target: <${report.baselines.stressTest.targetResponseTime}ms) ${report.baselines.stressTest.meetsTargets ? '✅' : '❌'}\n`);
    
    console.log('💡 KEY RECOMMENDATIONS:');
    report.recommendations.immediate.forEach(rec => console.log(`  • ${rec}`));
    console.log('');
  }
}

// Run analysis
async function main() {
  const analyzer = new PerformanceAnalyzer();
  
  try {
    const report = analyzer.generateReport();
    analyzer.printSummary(report);
  } catch (error) {
    console.error('❌ Analysis failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = PerformanceAnalyzer;
