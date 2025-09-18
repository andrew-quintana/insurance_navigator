#!/usr/bin/env node

/**
 * Render Service Status Checker
 * 
 * This script checks the current status of Render services and provides
 * accurate information about their state, including recent logs and errors.
 */

const { execSync } = require('child_process');

function runCommand(command) {
  try {
    const output = execSync(command, { encoding: 'utf8', timeout: 30000 });
    return { success: true, output: output.trim() };
  } catch (error) {
    return { 
      success: false, 
      error: error.message,
      output: error.stdout ? error.stdout.trim() : '',
      stderr: error.stderr ? error.stderr.trim() : ''
    };
  }
}

function parseServiceStatus(serviceData) {
  try {
    const service = JSON.parse(serviceData);
    return {
      id: service.id,
      name: service.name,
      type: service.type,
      status: service.suspended === 'not_suspended' ? 'running' : 'suspended',
      url: service.serviceDetails?.url || 'N/A',
      lastUpdated: service.updatedAt,
      environment: service.environmentId
    };
  } catch (error) {
    return { error: 'Failed to parse service data', raw: serviceData };
  }
}

async function checkRenderServices() {
  console.log('🔍 Checking Render Service Status...\n');

  // Get list of services
  console.log('📋 Fetching service list...');
  const servicesResult = runCommand('render services list -o json');
  
  if (!servicesResult.success) {
    console.error('❌ Failed to fetch services:', servicesResult.error);
    return;
  }

  let services;
  try {
    services = JSON.parse(servicesResult.output);
  } catch (error) {
    console.error('❌ Failed to parse services JSON:', error.message);
    console.log('Raw output:', servicesResult.output);
    return;
  }

  console.log(`✅ Found ${services.length} services\n`);

  // Check each service
  for (const serviceData of services) {
    const service = serviceData.service;
    const project = serviceData.project;
    const environment = serviceData.environment;

    console.log(`🔧 Service: ${service.name}`);
    console.log(`   ID: ${service.id}`);
    console.log(`   Type: ${service.type}`);
    console.log(`   Status: ${service.suspended === 'not_suspended' ? '✅ Running' : '❌ Suspended'}`);
    console.log(`   URL: ${service.serviceDetails?.url || 'N/A'}`);
    console.log(`   Last Updated: ${service.updatedAt}`);
    console.log(`   Environment: ${environment.name}`);
    console.log(`   Project: ${project.name}`);

    // Get recent logs for this service
    console.log(`\n📝 Recent logs for ${service.name}:`);
    const logsResult = runCommand(`render logs --resources ${service.id} --tail 10 -o json`);
    
    if (logsResult.success) {
      try {
        const logs = JSON.parse(logsResult.output);
        if (Array.isArray(logs) && logs.length > 0) {
          console.log('   Recent log entries:');
          logs.slice(-5).forEach(log => {
            const timestamp = new Date(log.timestamp).toLocaleString();
            const level = log.labels?.find(l => l.name === 'level')?.value || 'info';
            const message = log.message || 'No message';
            console.log(`   [${timestamp}] [${level.toUpperCase()}] ${message}`);
          });
        } else {
          console.log('   No recent logs found');
        }
      } catch (error) {
        console.log('   Failed to parse logs:', error.message);
      }
    } else {
      console.log('   Failed to fetch logs:', logsResult.error);
    }

    console.log('\n' + '─'.repeat(80) + '\n');
  }

  // Summary
  console.log('📊 Summary:');
  const runningServices = services.filter(s => s.service.suspended === 'not_suspended');
  const suspendedServices = services.filter(s => s.service.suspended !== 'not_suspended');
  
  console.log(`   ✅ Running: ${runningServices.length}`);
  console.log(`   ❌ Suspended: ${suspendedServices.length}`);
  console.log(`   📊 Total: ${services.length}`);
}

// Run the check
checkRenderServices().catch(error => {
  console.error('❌ Script failed:', error.message);
  process.exit(1);
});
