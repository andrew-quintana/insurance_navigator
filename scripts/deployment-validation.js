#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

class DeploymentValidator {
  constructor() {
    this.validationResults = {
      unitTests: false,
      integrationTests: false,
      e2eTests: false,
      performanceTests: false,
      securityTests: false,
      accessibilityTests: false
    };
  }

  async validateDeploymentReadiness() {
    console.log('🔍 Validating deployment readiness...');
    
    try {
      // Check test results
      await this.checkUnitTestResults();
      await this.checkIntegrationTestResults();
      await this.checkE2ETestResults();
      await this.checkPerformanceResults();
      await this.checkSecurityResults();
      await this.checkAccessibilityResults();
      
      // Generate deployment report
      this.generateDeploymentReport();
      
      if (this.isReadyForDeployment()) {
        console.log('✅ System is ready for deployment');
        process.exit(0);
      } else {
        console.log('❌ System is not ready for deployment');
        process.exit(1);
      }
    } catch (error) {
      console.error('❌ Deployment validation failed:', error);
      process.exit(1);
    }
  }

  async checkUnitTestResults() {
    const coverageFile = path.join(__dirname, '../ui/coverage/coverage-summary.json');
    
    if (fs.existsSync(coverageFile)) {
      const coverage = JSON.parse(fs.readFileSync(coverageFile, 'utf8'));
      const totalCoverage = coverage.total.lines.pct;
      
      if (totalCoverage >= 85) {
        this.validationResults.unitTests = true;
        console.log(`✅ Unit tests: ${totalCoverage}% coverage (target: 85%)`);
      } else {
        console.log(`❌ Unit tests: ${totalCoverage}% coverage (target: 85%)`);
      }
    } else {
      console.log('❌ Unit test results not found');
    }
  }

  async checkIntegrationTestResults() {
    const integrationResultsDir = path.join(__dirname, '../tests/integration/frontend/results');
    
    if (fs.existsSync(integrationResultsDir)) {
      const files = fs.readdirSync(integrationResultsDir);
      const latestResult = files.sort().pop();
      
      if (latestResult) {
        const results = JSON.parse(fs.readFileSync(
          path.join(integrationResultsDir, latestResult), 
          'utf8'
        ));
        
        if (results.passRate >= 95) {
          this.validationResults.integrationTests = true;
          console.log(`✅ Integration tests: ${results.passRate}% pass rate (target: 95%)`);
        } else {
          console.log(`❌ Integration tests: ${results.passRate}% pass rate (target: 95%)`);
        }
      }
    } else {
      console.log('❌ Integration test results not found');
    }
  }

  async checkE2ETestResults() {
    const e2eResultsDir = path.join(__dirname, '../ui/e2e/test-results');
    
    if (fs.existsSync(e2eResultsDir)) {
      const files = fs.readdirSync(e2eResultsDir);
      const latestResult = files.sort().pop();
      
      if (latestResult) {
        const results = JSON.parse(fs.readFileSync(
          path.join(e2eResultsDir, latestResult), 
          'utf8'
        ));
        
        if (results.passRate >= 100) {
          this.validationResults.e2eTests = true;
          console.log(`✅ E2E tests: ${results.passRate}% pass rate (target: 100%)`);
        } else {
          console.log(`❌ E2E tests: ${results.passRate}% pass rate (target: 100%)`);
        }
      }
    } else {
      console.log('❌ E2E test results not found');
    }
  }

  async checkPerformanceResults() {
    const performanceDir = path.join(__dirname, '../performance/results');
    
    if (fs.existsSync(performanceDir)) {
      const files = fs.readdirSync(performanceDir);
      const latestResult = files.sort().pop();
      
      if (latestResult) {
        const results = JSON.parse(fs.readFileSync(
          path.join(performanceDir, latestResult), 
          'utf8'
        ));
        
        if (results.summary.errorRate < 1 && results.summary.averageResponseTime < 1000) {
          this.validationResults.performanceTests = true;
          console.log('✅ Performance tests: Targets met');
        } else {
          console.log(`❌ Performance tests: Error rate ${results.summary.errorRate}%, avg response ${results.summary.averageResponseTime}ms`);
        }
      }
    } else {
      console.log('❌ Performance test results not found');
    }
  }

  async checkSecurityResults() {
    const securityResultsDir = path.join(__dirname, '../tests/security/results');
    
    if (fs.existsSync(securityResultsDir)) {
      const files = fs.readdirSync(securityResultsDir);
      const latestResult = files.sort().pop();
      
      if (latestResult) {
        const results = JSON.parse(fs.readFileSync(
          path.join(securityResultsDir, latestResult), 
          'utf8'
        ));
        
        if (results.vulnerabilities === 0) {
          this.validationResults.securityTests = true;
          console.log('✅ Security tests: No vulnerabilities found');
        } else {
          console.log(`❌ Security tests: ${results.vulnerabilities} vulnerabilities found`);
        }
      }
    } else {
      console.log('❌ Security test results not found');
    }
  }

  async checkAccessibilityResults() {
    const accessibilityResultsDir = path.join(__dirname, '../tests/accessibility/results');
    
    if (fs.existsSync(accessibilityResultsDir)) {
      const files = fs.readdirSync(accessibilityResultsDir);
      const latestResult = files.sort().pop();
      
      if (latestResult) {
        const results = JSON.parse(fs.readFileSync(
          path.join(accessibilityResultsDir, latestResult), 
          'utf8'
        ));
        
        if (results.violations === 0) {
          this.validationResults.accessibilityTests = true;
          console.log('✅ Accessibility tests: No violations found');
        } else {
          console.log(`❌ Accessibility tests: ${results.violations} violations found`);
        }
      }
    } else {
      console.log('❌ Accessibility test results not found');
    }
  }

  isReadyForDeployment() {
    const requiredTests = ['unitTests', 'integrationTests', 'e2eTests', 'performanceTests'];
    return requiredTests.every(test => this.validationResults[test]);
  }

  generateDeploymentReport() {
    const report = {
      timestamp: new Date().toISOString(),
      validationResults: this.validationResults,
      readyForDeployment: this.isReadyForDeployment(),
      summary: {
        totalTests: Object.keys(this.validationResults).length,
        passedTests: Object.values(this.validationResults).filter(Boolean).length,
        failedTests: Object.values(this.validationResults).filter(Boolean => !Boolean).length
      }
    };
    
    fs.writeFileSync(
      path.join(__dirname, '../deployment-report.json'),
      JSON.stringify(report, null, 2)
    );
    
    console.log('📋 Deployment report generated');
    console.log(`📊 Summary: ${report.summary.passedTests}/${report.summary.totalTests} tests passed`);
  }
}

// Run validation
if (require.main === module) {
  const validator = new DeploymentValidator();
  validator.validateDeploymentReadiness();
}

module.exports = DeploymentValidator;
