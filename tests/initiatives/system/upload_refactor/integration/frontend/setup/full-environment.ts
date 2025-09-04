import { exec } from 'child_process';
import { promisify } from 'util';
import fetch from 'node-fetch';

const execAsync = promisify(exec);

export interface ServiceHealth {
  name: string;
  url: string;
  healthy: boolean;
  lastCheck: Date;
}

export class FullIntegrationEnvironment {
  private services: string[] = ['postgres', 'supabase', 'api-server', 'enhanced-base-worker', 'frontend'];
  private healthCheckUrls = {
    frontend: 'http://localhost:3000/health',
    api: 'http://localhost:8000/health',
    supabase: 'http://localhost:54321/health',
    postgres: 'http://localhost:54322',
    mockLlamaParse: 'http://localhost:8001/health',
    mockOpenAI: 'http://localhost:8002/health',
    localStorage: 'http://localhost:5001/health'
  };

  private serviceHealth: Map<string, ServiceHealth> = new Map();

  async start(): Promise<void> {
    console.log('🚀 Starting full integration environment...');
    
    try {
      // Start all services
      await execAsync('docker-compose -f docker-compose.full.yml up -d', {
        cwd: __dirname
      });

      // Wait for services to be healthy
      await this.waitForServicesHealth();
      
      // Run database migrations
      await this.runMigrations();
      
      // Seed test data
      await this.seedTestData();
      
      console.log('✅ Full integration environment ready');
    } catch (error) {
      console.error('❌ Failed to start integration environment:', error);
      throw error;
    }
  }

  async stop(): Promise<void> {
    console.log('🛑 Stopping full integration environment...');
    
    try {
      await execAsync('docker-compose -f docker-compose.full.yml down -v', {
        cwd: __dirname
      });
      console.log('✅ Environment stopped');
    } catch (error) {
      console.error('❌ Failed to stop environment:', error);
    }
  }

  async restart(): Promise<void> {
    console.log('🔄 Restarting full integration environment...');
    await this.stop();
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
    await this.start();
  }

  private async waitForServicesHealth(): Promise<void> {
    console.log('⏳ Waiting for services to be healthy...');
    
    const maxAttempts = 60; // 5 minutes total
    const delay = 5000; // 5 seconds

    for (const [service, url] of Object.entries(this.healthCheckUrls)) {
      let attempts = 0;
      let healthy = false;
      
      console.log(`🔍 Checking ${service} at ${url}...`);
      
      while (attempts < maxAttempts && !healthy) {
        try {
          const response = await fetch(url, { 
            timeout: 3000,
            headers: {
              'User-Agent': 'FullIntegrationEnvironment/1.0'
            }
          });
          
          if (response.ok) {
            healthy = true;
            this.serviceHealth.set(service, {
              name: service,
              url,
              healthy: true,
              lastCheck: new Date()
            });
            console.log(`✅ ${service} is healthy`);
          } else {
            console.log(`⏳ ${service} not ready yet (status: ${response.status})`);
          }
        } catch (error) {
          // Service not ready yet
          console.log(`⏳ ${service} not ready yet (${error.message})`);
        }

        if (!healthy) {
          attempts++;
          if (attempts >= maxAttempts) {
            throw new Error(`Service ${service} failed to become healthy after ${maxAttempts} attempts`);
          }
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
  }

  private async runMigrations(): Promise<void> {
    console.log('🔄 Running database migrations...');
    
    try {
      // Wait a bit more for postgres to be fully ready
      await new Promise(resolve => setTimeout(resolve, 10000));
      
      // Run migrations through the API server
      await execAsync('docker-compose -f docker-compose.full.yml exec -T api-server python -m alembic upgrade head', {
        cwd: __dirname
      });
      console.log('✅ Migrations completed');
    } catch (error) {
      console.error('❌ Migration failed:', error);
      // Don't throw here as migrations might already be applied
      console.log('⚠️ Continuing without migrations (they may already be applied)');
    }
  }

  private async seedTestData(): Promise<void> {
    console.log('🌱 Seeding test data...');
    
    try {
      // Create test users
      await this.createTestUsers();
      
      // Create test documents
      await this.createTestDocuments();
      
      console.log('✅ Test data seeded');
    } catch (error) {
      console.error('❌ Failed to seed test data:', error);
      throw error;
    }
  }

  private async createTestUsers(): Promise<void> {
    const testUsers = [
      { email: 'integration-test-1@example.com', password: 'IntegrationTest123!' },
      { email: 'integration-test-2@example.com', password: 'IntegrationTest123!' },
      { email: 'performance-test@example.com', password: 'PerformanceTest123!' },
      { email: 'security-test@example.com', password: 'SecurityTest123!' },
      { email: 'accessibility-test@example.com', password: 'AccessibilityTest123!' }
    ];

    for (const user of testUsers) {
      try {
        const response = await fetch('http://localhost:54321/auth/v1/signup', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'
          },
          body: JSON.stringify(user)
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.warn(`Failed to create user ${user.email}: ${errorText}`);
        } else {
          console.log(`✅ Created test user: ${user.email}`);
        }
      } catch (error) {
        console.warn(`Error creating user ${user.email}:`, error.message);
      }
    }
  }

  private async createTestDocuments(): Promise<void> {
    // This would seed the database with test documents
    // for integration testing. For now, we'll create them during tests.
    console.log('📄 Test documents will be created during test execution');
  }

  async resetData(): Promise<void> {
    console.log('🧹 Resetting test data...');
    
    try {
      // Clean up test data between test runs
      await execAsync('docker-compose -f docker-compose.full.yml exec -T postgres psql -U postgres -d postgres -c "TRUNCATE upload_pipeline.documents CASCADE; TRUNCATE upload_pipeline.upload_jobs CASCADE;"', {
        cwd: __dirname
      });
      
      // Re-seed test data
      await this.seedTestData();
      console.log('✅ Data reset completed');
    } catch (error) {
      console.error('❌ Failed to reset data:', error);
      throw error;
    }
  }

  async getServiceHealth(): Promise<ServiceHealth[]> {
    const healthChecks = Array.from(this.serviceHealth.values());
    
    // Update health status
    for (const [service, url] of Object.entries(this.healthCheckUrls)) {
      try {
        const response = await fetch(url, { timeout: 2000 });
        const healthy = response.ok;
        
        this.serviceHealth.set(service, {
          name: service,
          url,
          healthy,
          lastCheck: new Date()
        });
      } catch (error) {
        this.serviceHealth.set(service, {
          name: service,
          url,
          healthy: false,
          lastCheck: new Date()
        });
      }
    }
    
    return Array.from(this.serviceHealth.values());
  }

  async waitForService(serviceName: string, timeoutMs: number = 30000): Promise<boolean> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeoutMs) {
      const health = await this.getServiceHealth();
      const service = health.find(s => s.name === serviceName);
      
      if (service && service.healthy) {
        return true;
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    return false;
  }

  async isHealthy(): Promise<boolean> {
    const health = await this.getServiceHealth();
    return health.every(service => service.healthy);
  }

  async getLogs(serviceName: string): Promise<string> {
    try {
      const { stdout } = await execAsync(`docker-compose -f docker-compose.full.yml logs ${serviceName}`, {
        cwd: __dirname
      });
      return stdout;
    } catch (error) {
      return `Failed to get logs for ${serviceName}: ${error.message}`;
    }
  }
}
