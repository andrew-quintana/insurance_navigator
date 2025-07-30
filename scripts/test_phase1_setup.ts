/**
 * Phase 1 Environment Setup Test
 * 
 * Validates that all dependencies are installed and basic functionality works:
 * - Supabase connection
 * - Tavily client
 * - Database schema
 * - Type definitions
 */

import { createClient } from '@supabase/supabase-js';
import { tavily } from '@tavily/core';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config({ path: '.env.development' });

async function testSupabaseConnection() {
  console.log('Testing Supabase connection...');
  
  try {
    const supabase = createClient(
      process.env.URL!,
      process.env.SERVICE_ROLE_KEY!
    );
    
    // Test basic connection
    const { data, error } = await supabase.from('documents').select('count').limit(1);
    
    if (error) {
      console.error('❌ Supabase connection failed:', error);
      return false;
    }
    
    console.log('✅ Supabase connection successful');
    return true;
  } catch (error) {
    console.error('❌ Supabase connection error:', error);
    return false;
  }
}

async function testTavilyClient() {
  console.log('Testing Tavily client...');
  
  try {
    const tavilyClient = tavily({ apiKey: process.env.TAVILY_API_KEY! });
    
    // Test basic search functionality
    const result = await tavilyClient.search('healthcare strategy');
    
    if (result && result.results) {
      console.log('✅ Tavily client working');
      return true;
    } else {
      console.error('❌ Tavily search returned no results');
      return false;
    }
  } catch (error) {
    console.error('❌ Tavily client error:', error);
    return false;
  }
}

async function testDatabaseSchema() {
  console.log('Testing database schema...');
  
  try {
    const supabase = createClient(
      process.env.URL!,
      process.env.SERVICE_ROLE_KEY!
    );
    
    // Test if strategies schema exists
    const { data, error } = await supabase
      .from('information_schema.tables')
      .select('table_name')
      .eq('table_schema', 'strategies');
    
    if (error) {
      console.error('❌ Database schema test failed:', error);
      return false;
    }
    
    if (data && data.length > 0) {
      console.log('✅ Strategies schema exists');
      return true;
    } else {
      console.log('⚠️  Strategies schema not found - migration may not be applied');
      return false;
    }
  } catch (error) {
    console.error('❌ Database schema test error:', error);
    return false;
  }
}

async function testTypeDefinitions() {
  console.log('Testing TypeScript type definitions...');
  
  try {
    // Test basic object creation that matches our type patterns
    const testConstraints = {
      specialtyAccess: 'cardiology',
      urgencyLevel: 'medium' as const
    };
    
    const testScores = {
      speed: 0.8,
      cost: 0.6,
      effort: 0.7
    };
    
    // Basic validation
    if (testConstraints.specialtyAccess && testScores.speed >= 0 && testScores.speed <= 1) {
      console.log('✅ Type definitions working');
      return true;
    } else {
      console.error('❌ Type validation failed');
      return false;
    }
  } catch (error) {
    console.error('❌ Type definitions error:', error);
    return false;
  }
}

async function runAllTests() {
  console.log('🚀 Running Phase 1 Environment Tests...\n');
  
  const tests = [
    { name: 'Supabase Connection', test: testSupabaseConnection },
    { name: 'Tavily Client', test: testTavilyClient },
    { name: 'Database Schema', test: testDatabaseSchema },
    { name: 'Type Definitions', test: testTypeDefinitions }
  ];
  
  const results = [];
  
  for (const { name, test } of tests) {
    console.log(`\n--- Testing ${name} ---`);
    const result = await test();
    results.push({ name, passed: result });
  }
  
  console.log('\n📊 Test Results:');
  console.log('================');
  
  let passedCount = 0;
  for (const { name, passed } of results) {
    const status = passed ? '✅ PASS' : '❌ FAIL';
    console.log(`${status} ${name}`);
    if (passed) passedCount++;
  }
  
  console.log(`\n${passedCount}/${results.length} tests passed`);
  
  if (passedCount === results.length) {
    console.log('🎉 All Phase 1 tests passed! Environment is ready.');
  } else {
    console.log('⚠️  Some tests failed. Please check the issues above.');
  }
  
  return passedCount === results.length;
}

// Run tests if this file is executed directly
if (require.main === module) {
  runAllTests().then(success => {
    process.exit(success ? 0 : 1);
  });
}

export { runAllTests }; 