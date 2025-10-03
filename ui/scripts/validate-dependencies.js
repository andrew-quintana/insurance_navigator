#!/usr/bin/env node

/**
 * Dependency Validation Script
 * Prevents dependency conflicts by validating compatibility before deployment
 * Based on lessons learned from FM032, FM033, FM034 failure modes
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔍 Running dependency validation...\n');

// Check for dependency conflicts
function checkDependencyConflicts() {
  console.log('📦 Checking for dependency conflicts...');
  
  try {
    // Run npm ls to check for conflicts
    const result = execSync('npm ls --depth=0', { 
      encoding: 'utf8',
      stdio: 'pipe'
    });
    
    if (result.includes('UNMET PEER DEPENDENCY')) {
      console.error('❌ UNMET PEER DEPENDENCIES FOUND:');
      console.error(result);
      process.exit(1);
    }
    
    console.log('✅ No dependency conflicts found');
  } catch (error) {
    console.error('❌ Dependency conflict check failed:', error.message);
    process.exit(1);
  }
}

// Check for security vulnerabilities
function checkSecurityVulnerabilities() {
  console.log('🔒 Checking for security vulnerabilities...');
  
  try {
    const result = execSync('npm audit --audit-level=high', { 
      encoding: 'utf8',
      stdio: 'pipe'
    });
    
    if (result.includes('found 0 vulnerabilities')) {
      console.log('✅ No high-severity vulnerabilities found');
    } else {
      console.warn('⚠️  Security vulnerabilities found:');
      console.warn(result);
      console.log('💡 Run "npm audit fix" to address vulnerabilities');
    }
  } catch (error) {
    console.error('❌ Security check failed:', error.message);
    process.exit(1);
  }
}

// Validate React version compatibility
function validateReactCompatibility() {
  console.log('⚛️  Validating React version compatibility...');
  
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  const reactVersion = packageJson.dependencies?.react;
  const testingLibraryVersion = packageJson.devDependencies?.['@testing-library/react'];
  
  if (!reactVersion || !testingLibraryVersion) {
    console.error('❌ Missing React or @testing-library/react dependency');
    process.exit(1);
  }
  
  // Check if React version is compatible with testing library
  const reactMajor = parseInt(reactVersion.replace(/[^0-9]/g, ''));
  const testingLibraryMajor = parseInt(testingLibraryVersion.replace(/[^0-9]/g, ''));
  
  if (reactMajor >= 19 && testingLibraryMajor < 16) {
    console.error('❌ React 19 requires @testing-library/react >= 16.0.0');
    console.error(`   Current: React ${reactVersion}, @testing-library/react ${testingLibraryVersion}`);
    process.exit(1);
  }
  
  console.log(`✅ React ${reactVersion} compatible with @testing-library/react ${testingLibraryVersion}`);
}

// Validate environment variables
function validateEnvironmentVariables() {
  console.log('🌍 Validating environment variables...');
  
  const requiredEnvVars = [
    'NEXT_PUBLIC_SUPABASE_URL',
    'NEXT_PUBLIC_SUPABASE_ANON_KEY',
    'NEXT_PUBLIC_API_BASE_URL'
  ];
  
  const envFiles = ['.env.local', '.env.production', '.env.development'];
  let foundEnvFile = false;
  
  for (const envFile of envFiles) {
    if (fs.existsSync(envFile)) {
      foundEnvFile = true;
      const envContent = fs.readFileSync(envFile, 'utf8');
      
      for (const envVar of requiredEnvVars) {
        if (!envContent.includes(envVar)) {
          console.warn(`⚠️  Missing ${envVar} in ${envFile}`);
        }
      }
    }
  }
  
  if (!foundEnvFile) {
    console.warn('⚠️  No environment files found');
  } else {
    console.log('✅ Environment variables validated');
  }
}

// Main validation function
function main() {
  try {
    checkDependencyConflicts();
    checkSecurityVulnerabilities();
    validateReactCompatibility();
    validateEnvironmentVariables();
    
    console.log('\n🎉 All dependency validations passed!');
    console.log('✅ Ready for deployment');
  } catch (error) {
    console.error('\n❌ Dependency validation failed:', error.message);
    process.exit(1);
  }
}

// Run validation
main();
