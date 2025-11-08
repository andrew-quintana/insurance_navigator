const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class AuthPerformanceRunner {
  constructor() {
    this.resultsDir = path.join(__dirname, 'results');
    this.ensureResultsDir();
  }

  ensureResultsDir() {
    if (!fs.existsSync(this.resultsDir)) {
      fs.mkdirSync(this.resultsDir, { recursive: true });
    }
  }

  async runAuthLoadTest() {
    console.log('🚀 Starting authentication load test...');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(this.resultsDir, `auth-load-${timestamp}.json`);
    
    try {
      execSync(`artillery run artillery-auth.yml --output ${outputFile}`, {
        cwd: __dirname,
        stdio: 'inherit'
      });
      
      console.log('✅ Authentication load test completed');
      return this.analyzeResults(outputFile);
    } catch (error) {
      console.error('❌ Authentication load test failed:', error.message);
      throw error;
    }
  }

  async runAuthStressTest() {
    console.log('🔥 Starting authentication stress test...');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(this.resultsDir, `auth-stress-${timestamp}.json`);
    
    try {
      execSync(`artillery run artillery-stress-auth.yml --output ${outputFile}`, {
        cwd: __dirname,
        stdio: 'inherit'
      });
      
      console.log('✅ Authentication stress test completed');
      return this.analyzeResults(outputFile);
    } catch (error) {
      console.error('❌ Authentication stress test failed:', error.message);
      throw error;
    }
  }

  async runCrossBrowserPerformanceTest() {
    console.log('🌐 Starting cross-browser performance test...');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(this.resultsDir, `cross-browser-${timestamp}.json`);
    
    try {
      // Test with different user agents
      const userAgents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
      ];

      const results = [];
      for (const userAgent of userAgents) {
        console.log(`Testing with User-Agent: ${userAgent.substring(0, 50)}...`);
        
        const browserOutputFile = path.join(this.resultsDir, `browser-${userAgents.indexOf(userAgent)}-${timestamp}.json`);
        
        // Create a temporary config for this browser
        const tempConfig = this.createBrowserSpecificConfig(userAgent);
        const tempConfigFile = path.join(__dirname, 'temp-browser-config.yml');
        fs.writeFileSync(tempConfigFile, tempConfig);
        
        try {
          execSync(`artillery run ${tempConfigFile} --output ${browserOutputFile}`, {
            cwd: __dirname,
            stdio: 'inherit'
          });
          
          const browserResults = this.analyzeResults(browserOutputFile);
          results.push({ userAgent, results: browserResults });
          
        } finally {
          // Clean up temp file
          if (fs.existsSync(tempConfigFile)) {
            fs.unlinkSync(tempConfigFile);
          }
        }
      }
      
      // Save combined results
      const combinedResults = {
        timestamp: new Date().toISOString(),
        browserResults: results,
        summary: this.analyzeCrossBrowserResults(results)
      };
      
      fs.writeFileSync(outputFile, JSON.stringify(combinedResults, null, 2));
      console.log('✅ Cross-browser performance test completed');
      
      return combinedResults;
    } catch (error) {
      console.error('❌ Cross-browser performance test failed:', error.message);
      throw error;
    }
  }

  async runResponsiveDesignPerformanceTest() {
    console.log('📱 Starting responsive design performance test...');
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(this.resultsDir, `responsive-design-${timestamp}.json`);
    
    try {
      // Test different viewport sizes
      const viewports = [
        { name: 'mobile', width: 375, height: 667 },
        { name: 'tablet', width: 768, height: 1024 },
        { name: 'desktop', width: 1920, height: 1080 }
      ];

      const results = [];
      for (const viewport of viewports) {
        console.log(`Testing viewport: ${viewport.name} (${viewport.width}x${viewport.height})`);
        
        const viewportOutputFile = path.join(this.resultsDir, `viewport-${viewport.name}-${timestamp}.json`);
        
        // Create a temporary config for this viewport
        const tempConfig = this.createViewportSpecificConfig(viewport);
        const tempConfigFile = path.join(__dirname, 'temp-viewport-config.yml');
        fs.writeFileSync(tempConfigFile, tempConfig);
        
        try {
          execSync(`artillery run ${tempConfigFile} --output ${viewportOutputFile}`, {
            cwd: __dirname,
            stdio: 'inherit'
          });
          
          const viewportResults = this.analyzeResults(viewportOutputFile);
          results.push({ viewport, results: viewportResults });
          
        } finally {
          // Clean up temp file
          if (fs.existsSync(tempConfigFile)) {
            fs.unlinkSync(tempConfigFile);
          }
        }
      }
      
      // Save combined results
      const combinedResults = {
        timestamp: new Date().toISOString(),
        viewportResults: results,
        summary: this.analyzeResponsiveResults(results)
      };
      
      fs.writeFileSync(outputFile, JSON.stringify(combinedResults, null, 2));
      console.log('✅ Responsive design performance test completed');
      
      return combinedResults;
    } catch (error) {
      console.error('❌ Responsive design performance test failed:', error.message);
      throw error;
    }
  }

  analyzeResults(outputFile) {
    if (!fs.existsSync(outputFile)) {
      console.warn(`⚠️ Results file not found: ${outputFile}`);
      return null;
    }

    const results = JSON.parse(fs.readFileSync(outputFile, 'utf8'));
    
    const analysis = {
      summary: {
        totalRequests: results.aggregate?.counters?.['http.requests'] || 0,
        successfulRequests: results.aggregate?.counters?.['http.responses'] || 0,
        errorRate: this.calculateErrorRate(results.aggregate),
        averageResponseTime: results.aggregate?.summaries?.['http.response_time']?.mean || 0,
        p95ResponseTime: results.aggregate?.summaries?.['http.response_time']?.p95 || 0,
        p99ResponseTime: results.aggregate?.summaries?.['http.response_time']?.p99 || 0
      },
      authMetrics: {
        loginResponseTime: results.aggregate?.summaries?.['http.response_time']?.mean || 0,
        registrationResponseTime: results.aggregate?.summaries?.['http.response_time']?.mean || 0,
        sessionValidationTime: results.aggregate?.summaries?.['http.response_time']?.mean || 0
      },
      thresholds: this.checkPerformanceThresholds(results.aggregate),
      timestamp: new Date().toISOString()
    };

    console.log('\n📊 Performance Analysis:');
    console.log(`Total Requests: ${analysis.summary.totalRequests}`);
    console.log(`Success Rate: ${(100 - analysis.summary.errorRate).toFixed(2)}%`);
    console.log(`Average Response Time: ${analysis.summary.averageResponseTime.toFixed(2)}ms`);
    console.log(`95th Percentile: ${analysis.summary.p95ResponseTime.toFixed(2)}ms`);
    
    // Check if we meet performance targets
    const performanceTargets = {
      authenticationTime: 1000,    // < 1 second
      sessionValidation: 500,      // < 500ms  
      errorRate: 1                 // < 1%
    };

    console.log('\n🎯 Performance Targets:');
    console.log(`Authentication Time: ${analysis.authMetrics.loginResponseTime.toFixed(2)}ms (target: <${performanceTargets.authenticationTime}ms) ${analysis.authMetrics.loginResponseTime < performanceTargets.authenticationTime ? '✅' : '❌'}`);
    console.log(`Session Validation: ${analysis.authMetrics.sessionValidationTime.toFixed(2)}ms (target: <${performanceTargets.sessionValidation}ms) ${analysis.authMetrics.sessionValidationTime < performanceTargets.sessionValidation ? '✅' : '❌'}`);
    console.log(`Error Rate: ${analysis.summary.errorRate.toFixed(2)}% (target: <${performanceTargets.errorRate}%) ${analysis.summary.errorRate < performanceTargets.errorRate ? '✅' : '❌'}`);

    return analysis;
  }

  analyzeCrossBrowserResults(browserResults) {
    const summary = {
      totalBrowsers: browserResults.length,
      averageResponseTime: 0,
      bestPerformingBrowser: null,
      worstPerformingBrowser: null,
      browserComparison: []
    };

    let totalResponseTime = 0;
    let bestTime = Infinity;
    let worstTime = 0;

    browserResults.forEach(({ userAgent, results }) => {
      const responseTime = results?.summary?.averageResponseTime || 0;
      totalResponseTime += responseTime;
      
      const browserName = this.extractBrowserName(userAgent);
      
      if (responseTime < bestTime) {
        bestTime = responseTime;
        summary.bestPerformingBrowser = { browser: browserName, time: responseTime };
      }
      
      if (responseTime > worstTime) {
        worstTime = responseTime;
        summary.worstPerformingBrowser = { browser: browserName, time: responseTime };
      }
      
      summary.browserComparison.push({
        browser: browserName,
        responseTime,
        errorRate: results?.summary?.errorRate || 0
      });
    });

    summary.averageResponseTime = totalResponseTime / browserResults.length;
    
    return summary;
  }

  analyzeResponsiveResults(viewportResults) {
    const summary = {
      totalViewports: viewportResults.length,
      averageResponseTime: 0,
      bestPerformingViewport: null,
      worstPerformingViewport: null,
      viewportComparison: []
    };

    let totalResponseTime = 0;
    let bestTime = Infinity;
    let worstTime = 0;

    viewportResults.forEach(({ viewport, results }) => {
      const responseTime = results?.summary?.averageResponseTime || 0;
      totalResponseTime += responseTime;
      
      if (responseTime < bestTime) {
        bestTime = responseTime;
        summary.bestPerformingViewport = { viewport: viewport.name, time: responseTime };
      }
      
      if (responseTime > worstTime) {
        worstTime = responseTime;
        summary.worstPerformingViewport = { viewport: viewport.name, time: responseTime };
      }
      
      summary.viewportComparison.push({
        viewport: viewport.name,
        dimensions: `${viewport.width}x${viewport.height}`,
        responseTime,
        errorRate: results?.summary?.errorRate || 0
      });
    });

    summary.averageResponseTime = totalResponseTime / viewportResults.length;
    
    return summary;
  }

  calculateErrorRate(aggregate) {
    if (!aggregate) return 0;
    
    const totalRequests = aggregate.counters?.['http.requests'] || 0;
    const errors = (aggregate.counters?.['http.codes.4xx'] || 0) + (aggregate.counters?.['http.codes.5xx'] || 0);
    return totalRequests > 0 ? (errors / totalRequests) * 100 : 0;
  }

  checkPerformanceThresholds(aggregate) {
    if (!aggregate) return { responseTimeOk: false, errorRateOk: false, p95Ok: false };
    
    const avgResponseTime = aggregate.summaries?.['http.response_time']?.mean || 0;
    const errorRate = this.calculateErrorRate(aggregate);
    
    return {
      responseTimeOk: avgResponseTime < 1000,  // < 1 second for auth
      errorRateOk: errorRate < 1,              // < 1% error rate
      p95Ok: (aggregate.summaries?.['http.response_time']?.p95 || 0) < 2000  // < 2 seconds p95
    };
  }

  createBrowserSpecificConfig(userAgent) {
    return `config:
  target: http://localhost:3000
  phases:
    - duration: 60
      arrivalRate: 2
      name: "Browser test"
  
  defaultHeaders:
    "User-Agent": "${userAgent}"

scenarios:
  - name: "Browser-specific test"
    weight: 100
    flow:
      - get:
          url: "/"
          expect:
            - statusCode: 200
      - think: 1
      - post:
          url: "/api/auth/login"
          json:
            email: "browser-test@example.com"
            password: "BrowserTest123!"
          expect:
            - statusCode: [200, 401]`;
  }

  createViewportSpecificConfig(viewport) {
    return `config:
  target: http://localhost:3000
  phases:
    - duration: 60
      arrivalRate: 2
      name: "Viewport test"
  
  defaultHeaders:
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    "Accept-Language": "en-US,en;q=0.5"
    "Accept-Encoding": "gzip, deflate"
    "DNT": "1"
    "Connection": "keep-alive"
    "Upgrade-Insecure-Requests": "1"
    "X-Viewport-Width": "${viewport.width}"
    "X-Viewport-Height": "${viewport.height}"

scenarios:
  - name: "Viewport-specific test"
    weight: 100
    flow:
      - get:
          url: "/"
          expect:
            - statusCode: 200
      - think: 1
      - post:
          url: "/api/auth/login"
          json:
            email: "viewport-test@example.com"
            password: "ViewportTest123!"
          expect:
            - statusCode: [200, 401]`;
  }

  extractBrowserName(userAgent) {
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari')) return 'Safari';
    if (userAgent.includes('Edge')) return 'Edge';
    return 'Unknown';
  }

  // Generate performance report
  generateReport() {
    const resultsFiles = fs.readdirSync(this.resultsDir)
      .filter(file => file.endsWith('.json'))
      .sort()
      .reverse();

    if (resultsFiles.length === 0) {
      console.log('📋 No performance test results found');
      return;
    }

    console.log('\n📋 Performance Test Results Summary:');
    console.log('=====================================');
    
    resultsFiles.slice(0, 5).forEach(file => {
      const filePath = path.join(this.resultsDir, file);
      try {
        const results = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        const timestamp = results.timestamp || 'Unknown';
        const testType = file.split('-')[0];
        
        console.log(`\n${testType.toUpperCase()} Test - ${timestamp}`);
        if (results.summary) {
          console.log(`  Total Requests: ${results.summary.totalRequests}`);
          console.log(`  Success Rate: ${(100 - (results.summary.errorRate || 0)).toFixed(2)}%`);
          console.log(`  Avg Response Time: ${(results.summary.averageResponseTime || 0).toFixed(2)}ms`);
        }
      } catch (error) {
        console.log(`  Error reading ${file}: ${error.message}`);
      }
    });
  }
}

// Run performance tests
async function main() {
  const runner = new AuthPerformanceRunner();
  
  try {
    console.log('🚀 Starting comprehensive frontend performance testing...\n');
    
    // Run all performance tests
    await runner.runAuthLoadTest();
    console.log('\n' + '='.repeat(50) + '\n');
    
    await runner.runAuthStressTest();
    console.log('\n' + '='.repeat(50) + '\n');
    
    await runner.runCrossBrowserPerformanceTest();
    console.log('\n' + '='.repeat(50) + '\n');
    
    await runner.runResponsiveDesignPerformanceTest();
    console.log('\n' + '='.repeat(50) + '\n');
    
    // Generate final report
    runner.generateReport();
    
    console.log('\n✅ All performance tests completed successfully!');
    
  } catch (error) {
    console.error('\n❌ Performance tests failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = AuthPerformanceRunner;
