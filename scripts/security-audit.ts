#!/usr/bin/env node

/**
 * Security Audit Script for Environment Configuration
 * 
 * This script performs comprehensive security auditing of environment
 * variables and configuration to ensure production security standards.
 */

import { readFileSync, existsSync, readdirSync } from 'fs';
import { join } from 'path';

interface SecurityAuditOptions {
  environment?: 'development' | 'production';
  strict?: boolean;
  verbose?: boolean;
  outputFile?: string;
  dryRun?: boolean;
}

interface SecurityIssue {
  level: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  description: string;
  recommendation: string;
  file?: string;
  line?: number;
}

interface SecurityAuditResult {
  totalIssues: number;
  criticalIssues: number;
  highIssues: number;
  mediumIssues: number;
  lowIssues: number;
  issues: SecurityIssue[];
  passed: boolean;
}

class SecurityAuditor {
  private options: SecurityAuditOptions;
  private issues: SecurityIssue[] = [];

  constructor(options: SecurityAuditOptions = {}) {
    this.options = {
      environment: options.environment || 'production',
      strict: options.strict || false,
      verbose: options.verbose || false,
      ...options
    };
  }

  /**
   * Performs comprehensive security audit
   */
  async audit(): Promise<SecurityAuditResult> {
    console.log(`🔒 Performing security audit for ${this.options.environment} environment...\n`);

    try {
      // Perform various security checks
      await this.auditEnvironmentFiles();
      await this.auditSecretsManagement();
      await this.auditConfigurationSecurity();
      await this.auditDependencies();
      await this.auditFilePermissions();

      const result = this.generateAuditResult();
      this.printResults(result);

      if (this.options.outputFile) {
        this.writeAuditReport(result);
      }

      return result;
    } catch (error) {
      console.error('❌ Security audit failed:', error);
      throw error;
    }
  }

  /**
   * Audits environment files for security issues
   */
  private async auditEnvironmentFiles(): Promise<void> {
    const envFiles = ['.env.development', '.env.production', '.env.local', '.env'];
    
    for (const file of envFiles) {
      if (existsSync(file)) {
        const content = readFileSync(file, 'utf8');
        const lines = content.split('\n');

        lines.forEach((line, index) => {
          const trimmed = line.trim();
          
          // Check for hardcoded secrets
          if (this.containsHardcodedSecret(trimmed)) {
            this.addIssue('critical', 'Hardcoded Secrets', 
              `Hardcoded secret detected in ${file}`, 
              'Remove hardcoded secrets and use environment variables',
              file, index + 1);
          }

          // Check for development secrets in production files
          if (file.includes('production') && this.containsDevelopmentSecret(trimmed)) {
            this.addIssue('critical', 'Development Secrets in Production',
              `Development secret found in production file: ${trimmed}`,
              'Replace with production-appropriate secrets',
              file, index + 1);
          }

          // Check for weak secrets
          if (this.isWeakSecret(trimmed)) {
            this.addIssue('high', 'Weak Secrets',
              `Weak secret detected: ${trimmed.split('=')[0]}`,
              'Use strong, randomly generated secrets',
              file, index + 1);
          }

          // Check for exposed sensitive data
          if (this.isExposedSensitiveData(trimmed)) {
            this.addIssue('medium', 'Exposed Sensitive Data',
              `Sensitive data may be exposed: ${trimmed.split('=')[0]}`,
              'Ensure sensitive data is properly protected',
              file, index + 1);
          }
        });
      }
    }
  }

  /**
   * Audits secrets management practices
   */
  private async auditSecretsManagement(): Promise<void> {
    const requiredSecrets = [
      'JWT_SECRET_KEY',
      'ENCRYPTION_KEY',
      'SUPABASE_SERVICE_ROLE_KEY',
      'OPENAI_API_KEY',
      'ANTHROPIC_API_KEY'
    ];

    for (const secret of requiredSecrets) {
      const value = process.env[secret];
      
      if (!value) {
        this.addIssue('critical', 'Missing Secrets',
          `Required secret not set: ${secret}`,
          'Set the required secret in environment configuration');
      } else {
        // Check secret strength
        if (secret.includes('SECRET') || secret.includes('KEY')) {
          if (value.length < 32) {
            this.addIssue('high', 'Weak Secrets',
              `Secret too short: ${secret} (${value.length} characters)`,
              'Use secrets with at least 32 characters');
          }

          if (this.isCommonSecret(value)) {
            this.addIssue('critical', 'Common Secrets',
              `Common/weak secret detected: ${secret}`,
              'Use cryptographically strong, unique secrets');
          }
        }
      }
    }
  }

  /**
   * Audits configuration security settings
   */
  private async auditConfigurationSecurity(): Promise<void> {
    // Check for security bypass in production
    if (this.options.environment === 'production') {
      const bypassEnabled = process.env.SECURITY_BYPASS === 'true' || 
                           process.env.BYPASS_ENABLED === 'true';
      
      if (bypassEnabled) {
        this.addIssue('critical', 'Security Bypass',
          'Security bypass is enabled in production',
          'Disable security bypass for production environment');
      }
    }

    // Check CORS configuration
    const corsOrigins = process.env.CORS_ORIGINS;
    if (corsOrigins && corsOrigins.includes('*')) {
      this.addIssue('high', 'Overly Permissive CORS',
        'CORS is configured to allow all origins (*)',
        'Restrict CORS to specific trusted domains');
    }

    // Check debug mode in production
    if (this.options.environment === 'production') {
      const debugMode = process.env.DEBUG === 'true' || 
                       process.env.NODE_ENV === 'development';
      
      if (debugMode) {
        this.addIssue('medium', 'Debug Mode in Production',
          'Debug mode is enabled in production',
          'Disable debug mode for production environment');
      }
    }
  }

  /**
   * Audits dependencies for known vulnerabilities
   */
  private async auditDependencies(): Promise<void> {
    const packageFiles = ['package.json', 'package-lock.json'];
    
    for (const file of packageFiles) {
      if (existsSync(file)) {
        try {
          const content = JSON.parse(readFileSync(file, 'utf8'));
          
          // Check for known vulnerable packages
          if (content.dependencies) {
            const vulnerablePackages = this.checkVulnerablePackages(content.dependencies);
            vulnerablePackages.forEach(pkg => {
              this.addIssue('medium', 'Vulnerable Dependencies',
                `Potentially vulnerable package: ${pkg}`,
                'Update to latest secure version or find alternative');
            });
          }
        } catch (error) {
          this.addIssue('low', 'Configuration Error',
            `Could not parse ${file}: ${error}`,
            'Fix JSON syntax errors');
        }
      }
    }
  }

  /**
   * Audits file permissions and access
   */
  private async auditFilePermissions(): Promise<void> {
    const sensitiveFiles = [
      '.env.production',
      '.env.local',
      'config/google_credentials.json',
      'config/environments/production.ts'
    ];

    for (const file of sensitiveFiles) {
      if (existsSync(file)) {
        // Check if file is readable by others (basic check)
        try {
          const stats = require('fs').statSync(file);
          const mode = stats.mode & parseInt('777', 8);
          
          if (mode & 0o004) { // Others can read
            this.addIssue('high', 'File Permissions',
              `Sensitive file is readable by others: ${file}`,
              'Restrict file permissions to owner only');
          }
        } catch (error) {
          // Ignore permission check errors
        }
      }
    }
  }

  /**
   * Checks if a line contains hardcoded secrets
   */
  private containsHardcodedSecret(line: string): boolean {
    const secretPatterns = [
      /sk-[a-zA-Z0-9]{48}/, // OpenAI API key
      /sk-ant-[a-zA-Z0-9]{48}/, // Anthropic API key
      /llx-[a-zA-Z0-9]{48}/, // LlamaCloud API key
      /eyJ[A-Za-z0-9+/=]+/, // JWT tokens
      /password\s*=\s*[^=\s]+/, // Password assignments
      /secret\s*=\s*[^=\s]+/ // Secret assignments
    ];

    return secretPatterns.some(pattern => pattern.test(line));
  }

  /**
   * Checks if a line contains development secrets
   */
  private containsDevelopmentSecret(line: string): boolean {
    const devPatterns = [
      'dev-jwt-secret-not-for-production',
      'dev-encryption-key-not-for-production',
      'localhost',
      '127.0.0.1',
      'test-',
      'demo-'
    ];

    return devPatterns.some(pattern => line.includes(pattern));
  }

  /**
   * Checks if a secret is weak
   */
  private isWeakSecret(line: string): boolean {
    const [key, value] = line.split('=');
    
    if (!value) return false;

    // Check for common weak values
    const weakValues = ['password', '123456', 'admin', 'secret', 'test'];
    if (weakValues.includes(value.toLowerCase())) {
      return true;
    }

    // Check for short values
    if (value.length < 8) {
      return true;
    }

    return false;
  }

  /**
   * Checks if sensitive data is exposed
   */
  private isExposedSensitiveData(line: string): boolean {
    const sensitiveKeys = ['password', 'secret', 'key', 'token', 'auth'];
    const [key] = line.split('=');
    
    return sensitiveKeys.some(sensitive => 
      key.toLowerCase().includes(sensitive) && 
      !key.startsWith('#')
    );
  }

  /**
   * Checks for common/weak secrets
   */
  private isCommonSecret(value: string): boolean {
    const commonSecrets = [
      'password',
      '123456',
      'admin',
      'secret',
      'test',
      'changeme',
      'default'
    ];

    return commonSecrets.includes(value.toLowerCase());
  }

  /**
   * Checks for vulnerable packages
   */
  private checkVulnerablePackages(dependencies: Record<string, string>): string[] {
    // This is a simplified check - in production, use tools like npm audit
    const knownVulnerable = [
      'lodash@4.17.0',
      'moment@2.29.0'
    ];

    return Object.entries(dependencies)
      .filter(([name, version]) => 
        knownVulnerable.some(vuln => vuln.startsWith(name))
      )
      .map(([name]) => name);
  }

  /**
   * Adds a security issue
   */
  private addIssue(
    level: SecurityIssue['level'],
    category: string,
    description: string,
    recommendation: string,
    file?: string,
    line?: number
  ): void {
    this.issues.push({
      level,
      category,
      description,
      recommendation,
      file,
      line
    });
  }

  /**
   * Generates audit result
   */
  private generateAuditResult(): SecurityAuditResult {
    const criticalIssues = this.issues.filter(i => i.level === 'critical').length;
    const highIssues = this.issues.filter(i => i.level === 'high').length;
    const mediumIssues = this.issues.filter(i => i.level === 'medium').length;
    const lowIssues = this.issues.filter(i => i.level === 'low').length;

    return {
      totalIssues: this.issues.length,
      criticalIssues,
      highIssues,
      mediumIssues,
      lowIssues,
      issues: this.issues,
      passed: criticalIssues === 0 && (this.options.strict ? highIssues === 0 : true)
    };
  }

  /**
   * Prints audit results
   */
  private printResults(result: SecurityAuditResult): void {
    console.log('🔒 Security Audit Results:\n');

    if (result.passed) {
      console.log('✅ Security audit passed!');
    } else {
      console.log('❌ Security audit failed!');
    }

    console.log(`\n📊 Summary:`);
    console.log(`  Total Issues: ${result.totalIssues}`);
    console.log(`  Critical: ${result.criticalIssues}`);
    console.log(`  High: ${result.highIssues}`);
    console.log(`  Medium: ${result.mediumIssues}`);
    console.log(`  Low: ${result.lowIssues}`);

    if (result.issues.length > 0) {
      console.log('\n🚨 Issues Found:');
      
      const groupedIssues = result.issues.reduce((acc, issue) => {
        if (!acc[issue.level]) acc[issue.level] = [];
        acc[issue.level].push(issue);
        return acc;
      }, {} as Record<string, SecurityIssue[]>);

      ['critical', 'high', 'medium', 'low'].forEach(level => {
        if (groupedIssues[level]) {
          console.log(`\n  ${level.toUpperCase()}:`);
          groupedIssues[level].forEach(issue => {
            console.log(`    • ${issue.description}`);
            console.log(`      Recommendation: ${issue.recommendation}`);
            if (issue.file) {
              console.log(`      File: ${issue.file}${issue.line ? `:${issue.line}` : ''}`);
            }
          });
        }
      });
    }

    if (this.options.verbose) {
      console.log('\n🔧 Audit Configuration:');
      console.log(`  Environment: ${this.options.environment}`);
      console.log(`  Strict Mode: ${this.options.strict ? 'enabled' : 'disabled'}`);
      console.log(`  Verbose: ${this.options.verbose ? 'enabled' : 'disabled'}`);
    }
  }

  /**
   * Writes audit report to file
   */
  private writeAuditReport(result: SecurityAuditResult): void {
    const report = {
      timestamp: new Date().toISOString(),
      environment: this.options.environment,
      result,
      options: this.options
    };

    const content = JSON.stringify(report, null, 2);
    
    if (this.options.dryRun) {
      console.log(`[DRY RUN] Would write audit report to ${this.options.outputFile}`);
    } else {
      require('fs').writeFileSync(this.options.outputFile!, content);
      console.log(`📄 Audit report written to ${this.options.outputFile}`);
    }
  }
}

/**
 * Main execution function
 */
async function main() {
  const args = process.argv.slice(2);
  const options: SecurityAuditOptions = {};

  // Parse command line arguments
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--environment':
      case '-e':
        options.environment = args[++i] as 'development' | 'production';
        break;
      case '--strict':
      case '-s':
        options.strict = true;
        break;
      case '--verbose':
      case '-v':
        options.verbose = true;
        break;
      case '--output':
      case '-o':
        options.outputFile = args[++i];
        break;
      case '--help':
      case '-h':
        console.log(`
Security Audit Tool

Usage: npm run security:audit [options]

Options:
  -e, --environment <env>  Target environment (development|production)
  -s, --strict            Enable strict mode (fail on high issues)
  -v, --verbose           Enable verbose output
  -o, --output <file>     Output audit report to file
  -h, --help              Show this help message

Examples:
  npm run security:audit
  npm run security:audit -- --environment production --strict
  npm run security:audit -- --output security-report.json
        `);
        process.exit(0);
        break;
    }
  }

  const auditor = new SecurityAuditor(options);
  const result = await auditor.audit();

  process.exit(result.passed ? 0 : 1);
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Security audit failed:', error);
    process.exit(1);
  });
}

export { SecurityAuditor };
