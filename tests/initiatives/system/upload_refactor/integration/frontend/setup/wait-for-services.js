#!/usr/bin/env node

const { FullIntegrationEnvironment } = require('./full-environment');

async function waitForServices() {
  console.log('⏳ Waiting for all services to be ready...');
  
  const environment = new FullIntegrationEnvironment();
  
  try {
    // Wait for all services to be healthy
    const maxWaitTime = 5 * 60 * 1000; // 5 minutes
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWaitTime) {
      const isHealthy = await environment.isHealthy();
      
      if (isHealthy) {
        console.log('✅ All services are healthy and ready');
        process.exit(0);
      }
      
      console.log('⏳ Services not ready yet, waiting...');
      await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
    }
    
    console.error('❌ Timeout waiting for services to be ready');
    process.exit(1);
    
  } catch (error) {
    console.error('❌ Error waiting for services:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  waitForServices();
}

module.exports = { waitForServices };
