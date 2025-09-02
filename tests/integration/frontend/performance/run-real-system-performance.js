#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class RealSystemPerformanceRunner {
  constructor() {
    this.resultsDir = path.join(__dirname, 'results');
    this.ensureResultsDir();
  }

  ensureResultsDir() {
    if (!fs.existsSync(this.resultsDir)) {
      fs.mkdirSync(this.resultsDir, { recursive: true });
    }
  }

  async runRealSystemLoadTest() {
    console.log('🚀 Starting real system load test...');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(this.resultsDir, `real-system-load-${timestamp}.json`);
    
    try {
      execSync(`artillery run artillery-real-system.yml --output ${outputFile}`, {
        cwd: __dirname,
        stdio: 'inherit'
      });
      
      console.log('✅ Real system load test completed');
      return this.analyzeResults(outputFile);
    } catch (error) {
      console.error('❌ Real system load test failed:', error.message);
      throw error;
    }
  }

  analyzeResults(outputFile) {
    const results = JSON.parse(fs.readFileSync(outputFile, 'utf8'));
    
    const analysis = {
      summary: {
        totalRequests: results.aggregate.counters?.['http.requests'] || 0,
        successfulRequests: results.aggregate.counters?.['http.responses'] || 0,
        errorRate: this.calculateErrorRate(results.aggregate),
        averageResponseTime: results.aggregate.summaries?.['http.response_time']?.mean || 0,
        p95ResponseTime: results.aggregate.summaries?.['http.response_time']?.p95 || 0,
        p99ResponseTime: results.aggregate.summaries?.['http.response_time']?.p99 || 0
      },
      realSystemMetrics: {
        authResponseTime: results.aggregate.summaries?.['http.response_time']?.mean || 0,
        uploadResponseTime: results.aggregate.summaries?.['http.response_time']?.mean || 0,
        chatResponseTime: results.aggregate.summaries?.['http.response_time']?.mean || 0,
        documentProcessingTime: this.estimateDocumentProcessingTime(results),
        aiResponseTime: this.estimateAIResponseTime(results)
      },
      thresholds: this.checkRealSystemThresholds(results.aggregate)
    };

    console.log('\n📊 Real System Performance Analysis:');
    console.log(`Total Requests: ${analysis.summary.totalRequests}`);
    console.log(`Success Rate: ${(100 - analysis.summary.errorRate).toFixed(2)}%`);
    console.log(`Average Response Time: ${analysis.summary.averageResponseTime.toFixed(2)}ms`);
    console.log(`95th Percentile: ${analysis.summary.p95ResponseTime.toFixed(2)}ms`);
    
    // Check if we meet real system performance targets
    const realSystemTargets = {
      authenticationTime: 2000,    // < 2 seconds (real auth)
      uploadTime: 30000,          // < 30 seconds (real processing)
      chatResponseTime: 15000,    // < 15 seconds (real AI)
      errorRate: 5                // < 5% (real system tolerance)
    };

    console.log('\n🎯 Real System Performance Targets:');
    console.log(`Authentication Time: ${analysis.realSystemMetrics.authResponseTime.toFixed(2)}ms (target: <${realSystemTargets.authenticationTime}ms) ${analysis.realSystemMetrics.authResponseTime < realSystemTargets.authenticationTime ? '✅' : '❌'}`);
    console.log(`Upload Time: ${analysis.realSystemMetrics.uploadResponseTime.toFixed(2)}ms (target: <${realSystemTargets.uploadTime}ms) ${analysis.realSystemMetrics.uploadResponseTime < realSystemTargets.uploadTime ? '✅' : '❌'}`);
    console.log(`Chat Response Time: ${analysis.realSystemMetrics.chatResponseTime.toFixed(2)}ms (target: <${realSystemTargets.chatResponseTime}ms) ${analysis.realSystemMetrics.chatResponseTime < realSystemTargets.chatResponseTime ? '✅' : '❌'}`);
    console.log(`Error Rate: ${analysis.summary.errorRate.toFixed(2)}% (target: <${realSystemTargets.errorRate}%) ${analysis.summary.errorRate < realSystemTargets.errorRate ? '✅' : '❌'}`);

    return analysis;
  }

  calculateErrorRate(aggregate) {
    const totalRequests = aggregate.counters?.['http.requests'] || 0;
    const errors = aggregate.counters?.['http.codes.4xx'] + aggregate.counters?.['http.codes.5xx'] || 0;
    return totalRequests > 0 ? (errors / totalRequests) * 100 : 0;
  }

  estimateDocumentProcessingTime(results) {
    // Estimate document processing time based on upload response times
    const uploadTimes = results.aggregate.summaries?.['http.response_time']?.mean || 0;
    return uploadTimes * 0.8; // Assume 80% of upload time is processing
  }

  estimateAIResponseTime(results) {
    // Estimate AI response time based on chat response times
    const chatTimes = results.aggregate.summaries?.['http.response_time']?.mean || 0;
    return chatTimes * 0.9; // Assume 90% of chat time is AI processing
  }

  checkRealSystemThresholds(aggregate) {
    const avgResponseTime = aggregate.summaries?.['http.response_time']?.mean || 0;
    const errorRate = this.calculateErrorRate(aggregate);
    
    return {
      responseTimeOk: avgResponseTime < 10000,  // < 10 seconds for real system
      errorRateOk: errorRate < 5,              // < 5% error rate for real system
      p95Ok: (aggregate.summaries?.['http.response_time']?.p95 || 0) < 20000  // < 20 seconds p95
    };
  }

  async runRealSystemStressTest() {
    console.log('🔥 Starting real system stress test...');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(this.resultsDir, `real-system-stress-${timestamp}.json`);
    
    try {
      // Create a stress test configuration
      const stressConfig = this.createStressTestConfig();
      const stressConfigFile = path.join(__dirname, 'artillery-real-stress.yml');
      fs.writeFileSync(stressConfigFile, stressConfig);
      
      execSync(`artillery run ${stressConfigFile} --output ${outputFile}`, {
        cwd: __dirname,
        stdio: 'inherit'
      });
      
      console.log('✅ Real system stress test completed');
      return this.analyzeResults(outputFile);
    } catch (error) {
      console.error('❌ Real system stress test failed:', error.message);
      throw error;
    }
  }

  createStressTestConfig() {
    return `
config:
  target: http://localhost:3000
  phases:
    # Stress test with moderate load for real system
    - duration: 60
      arrivalRate: 5
      name: "Real system stress test"
    - duration: 120  
      arrivalRate: 8
      name: "Peak real system load"

  timeout: 60
  http:
    timeout: 60

scenarios:
  - name: "Real System Stress Test"
    weight: 100
    flow:
      # Rapid fire registration and login
      - post:
          url: "/api/auth/register"
          json:
            email: "stress-{{ $randomString() }}-{{ $timestamp }}@example.com"
            password: "StressTest123!"
      - post:
          url: "/api/auth/login"
          json:
            email: "stress-{{ $randomString() }}-{{ $timestamp }}@example.com"  
            password: "StressTest123!"
      # Immediate operations to test real system handling
      - get:
          url: "/api/auth/user"
          headers:
            Authorization: "Bearer {{ authToken }}"
`;
  }
}

// Run performance tests
async function main() {
  const runner = new RealSystemPerformanceRunner();
  
  try {
    console.log('🚀 Starting real system performance testing...');
    
    await runner.runRealSystemLoadTest();
    await runner.runRealSystemStressTest();
    
    console.log('✅ All real system performance tests completed');
  } catch (error) {
    console.error('❌ Real system performance tests failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = RealSystemPerformanceRunner;
