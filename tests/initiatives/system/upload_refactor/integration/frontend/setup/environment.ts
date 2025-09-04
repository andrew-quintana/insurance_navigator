import { exec } from 'child_process';
import { promisify } from 'util';
import fetch from 'node-fetch';

const execAsync = promisify(exec);

export interface ServiceHealth {
  auth: boolean;
  api: boolean;
  frontend: boolean;
}

export class TestEnvironment {
  private services: string[] = ['mock-auth-service', 'mock-api-service', 'frontend-test'];
  private healthCheckUrls = {
    auth: 'http://localhost:3001/health',
    api: 'http://localhost:3002/health',
    frontend: 'http://localhost:3000/health'
  };

  /**
   * Start all mock services using Docker Compose
   */
  async startMockServices(): Promise<void> {
    console.log('🚀 Starting mock services...');
    
    try {
      const { stdout, stderr } = await execAsync('docker-compose -f docker-compose.mock.yml up -d', {
        cwd: __dirname
      });

      if (stderr) {
        console.warn('Docker Compose warnings:', stderr);
      }

      console.log('✅ Mock services started');
      console.log(stdout);
    } catch (error) {
      console.error('❌ Failed to start mock services:', error);
      throw error;
    }
  }

  /**
   * Stop all mock services
   */
  async stopMockServices(): Promise<void> {
    console.log('🛑 Stopping mock services...');
    
    try {
      const { stdout, stderr } = await execAsync('docker-compose -f docker-compose.mock.yml down -v', {
        cwd: __dirname
      });

      if (stderr) {
        console.warn('Docker Compose warnings:', stderr);
      }

      console.log('✅ Mock services stopped');
      console.log(stdout);
    } catch (error) {
      console.error('❌ Failed to stop mock services:', error);
      // Don't throw error during cleanup
    }
  }

  /**
   * Restart mock services
   */
  async restartMockServices(): Promise<void> {
    console.log('🔄 Restarting mock services...');
    
    try {
      await this.stopMockServices();
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait for cleanup
      await this.startMockServices();
      console.log('✅ Mock services restarted');
    } catch (error) {
      console.error('❌ Failed to restart mock services:', error);
      throw error;
    }
  }

  /**
   * Check health of all services
   */
  async checkServicesHealth(): Promise<ServiceHealth> {
    const health: ServiceHealth = {
      auth: false,
      api: false,
      frontend: false
    };

    try {
      // Check auth service
      try {
        const authResponse = await fetch(this.healthCheckUrls.auth, { timeout: 5000 });
        health.auth = authResponse.ok;
      } catch (error) {
        console.warn('Auth service health check failed:', error);
      }

      // Check API service
      try {
        const apiResponse = await fetch(this.healthCheckUrls.api, { timeout: 5000 });
        health.api = apiResponse.ok;
      } catch (error) {
        console.warn('API service health check failed:', error);
      }

      // Check frontend service
      try {
        const frontendResponse = await fetch(this.healthCheckUrls.frontend, { timeout: 5000 });
        health.frontend = frontendResponse.ok;
      } catch (error) {
        console.warn('Frontend service health check failed:', error);
      }

      return health;
    } catch (error) {
      console.error('Error checking services health:', error);
      return health;
    }
  }

  /**
   * Wait for all services to be healthy
   */
  async waitForServicesReady(maxAttempts: number = 60, delay: number = 2000): Promise<void> {
    console.log('⏳ Waiting for services to be healthy...');
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const health = await this.checkServicesHealth();
      
      if (health.auth && health.api && health.frontend) {
        console.log(`✅ All services healthy after ${attempt} attempts`);
        return;
      }
      
      console.log(`⏳ Services health check ${attempt}/${maxAttempts}:`, {
        auth: health.auth ? '✅' : '❌',
        api: health.api ? '✅' : '❌',
        frontend: health.frontend ? '✅' : '❌'
      });
      
      if (attempt >= maxAttempts) {
        throw new Error(`Services failed to become healthy after ${maxAttempts} attempts`);
      }
      
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  /**
   * Reset test data between test runs
   */
  async resetDatabase(): Promise<void> {
    console.log('🧹 Resetting test data...');
    
    try {
      // Clear auth service test data
      try {
        const authResponse = await fetch('http://localhost:3001/test/users', {
          method: 'DELETE'
        });
        if (authResponse.ok) {
          console.log('✅ Auth service test data cleared');
        }
      } catch (error) {
        console.warn('Failed to clear auth service test data:', error);
      }

      // Clear API service test data
      try {
        const apiResponse = await fetch('http://localhost:3002/test/clear', {
          method: 'DELETE'
        });
        if (apiResponse.ok) {
          console.log('✅ API service test data cleared');
        }
      } catch (error) {
        console.warn('Failed to clear API service test data:', error);
      }

      console.log('✅ Test data reset completed');
    } catch (error) {
      console.error('❌ Failed to reset test data:', error);
      throw error;
    }
  }

  /**
   * Seed test data for integration testing
   */
  async seedTestData(): Promise<void> {
    console.log('🌱 Seeding test data...');
    
    try {
      // This would create initial test data if needed
      // For now, we'll just log that seeding is complete
      console.log('✅ Test data seeding completed');
    } catch (error) {
      console.error('❌ Failed to seed test data:', error);
      throw error;
    }
  }

  /**
   * Get service logs for debugging
   */
  async getServiceLogs(serviceName?: string): Promise<string> {
    try {
      const command = serviceName 
        ? `docker-compose -f docker-compose.mock.yml logs ${serviceName}`
        : 'docker-compose -f docker-compose.mock.yml logs';
      
      const { stdout, stderr } = await execAsync(command, { cwd: __dirname });
      
      if (stderr) {
        console.warn('Service logs warnings:', stderr);
      }
      
      return stdout;
    } catch (error) {
      console.error('Failed to get service logs:', error);
      return 'Failed to retrieve logs';
    }
  }

  /**
   * Check if services are running
   */
  async areServicesRunning(): Promise<boolean> {
    try {
      const { stdout } = await execAsync('docker-compose -f docker-compose.mock.yml ps --format json', {
        cwd: __dirname
      });
      
      const services = JSON.parse(stdout);
      const runningServices = services.filter((service: any) => 
        service.State === 'running' || service.State === 'Up'
      );
      
      return runningServices.length >= this.services.length;
    } catch (error) {
      console.error('Failed to check if services are running:', error);
      return false;
    }
  }

  /**
   * Get service status information
   */
  async getServiceStatus(): Promise<any> {
    try {
      const { stdout } = await execAsync('docker-compose -f docker-compose.mock.yml ps --format json', {
        cwd: __dirname
      });
      
      const services = JSON.parse(stdout);
      return services.map((service: any) => ({
        name: service.Service,
        state: service.State,
        ports: service.Ports,
        status: service.Status
      }));
    } catch (error) {
      console.error('Failed to get service status:', error);
      return [];
    }
  }

  /**
   * Clean up all test resources
   */
  async cleanup(): Promise<void> {
    console.log('🧹 Cleaning up test environment...');
    
    try {
      await this.resetDatabase();
      await this.stopMockServices();
      console.log('✅ Test environment cleanup completed');
    } catch (error) {
      console.error('❌ Failed to cleanup test environment:', error);
      // Don't throw error during cleanup
    }
  }

  /**
   * Initialize test environment
   */
  async initialize(): Promise<void> {
    console.log('🚀 Initializing test environment...');
    
    try {
      await this.startMockServices();
      await this.waitForServicesReady();
      await this.seedTestData();
      console.log('✅ Test environment initialized successfully');
    } catch (error) {
      console.error('❌ Failed to initialize test environment:', error);
      throw error;
    }
  }

  /**
   * Get environment information
   */
  getEnvironmentInfo(): any {
    return {
      services: this.services,
      healthCheckUrls: this.healthCheckUrls,
      timestamp: new Date().toISOString(),
      nodeEnv: process.env.NODE_ENV || 'development'
    };
  }
}
