export interface MemoryInfo {
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
}

export interface NetworkRequest {
  name: string;
  entryType: string;
  startTime: number;
  duration: number;
  transferSize: number;
}

export interface AuthMetrics {
  operation: string;
  duration: number;
  success: boolean;
  memoryUsed?: number;
  networkRequests?: NetworkRequest[];
  error?: string;
  timestamp: number;
}

export interface AuthenticationMetrics {
  loginTime: number;           // Time to complete login
  registrationTime: number;    // Time to complete registration
  sessionValidation: number;   // Token validation timing
  tokenRefreshTime: number;    // Token refresh duration
  logoutTime: number;         // Time to complete logout
  memoryUsage: MemoryInfo;    // Browser memory during auth
  networkRequests: NetworkRequest[]; // Auth-related API calls
}

export class AuthMetricsCollector {
  private startTime: number = 0;
  private metrics: AuthMetrics[] = [];

  startMeasurement(operation: string): void {
    this.startTime = performance.now();
    console.log(`Starting ${operation} measurement`);
  }

  endMeasurement(operation: string): number {
    const duration = performance.now() - this.startTime;
    console.log(`${operation} completed in ${duration}ms`);
    return duration;
  }

  async collectLoginMetrics(email: string, password: string): Promise<AuthMetrics> {
    this.startMeasurement('login');
    
    const memoryBefore = this.getMemoryInfo();
    const networkBefore = this.getNetworkRequests();
    
    try {
      // This would integrate with your auth service
      // For now, we'll simulate the login process
      const result = await this.simulateLogin(email, password);
      
      const duration = this.endMeasurement('login');
      const memoryAfter = this.getMemoryInfo();
      const networkAfter = this.getNetworkRequests();
      
      const metrics: AuthMetrics = {
        operation: 'login',
        duration,
        success: true,
        memoryUsed: memoryAfter ? memoryAfter.usedJSHeapSize - (memoryBefore?.usedJSHeapSize || 0) : 0,
        networkRequests: this.calculateNetworkDelta(networkBefore, networkAfter),
        timestamp: Date.now()
      };

      this.metrics.push(metrics);
      return metrics;
    } catch (error) {
      const metrics: AuthMetrics = {
        operation: 'login',
        duration: this.endMeasurement('login'),
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };

      this.metrics.push(metrics);
      return metrics;
    }
  }

  async collectRegistrationMetrics(email: string, password: string): Promise<AuthMetrics> {
    this.startMeasurement('registration');
    
    const memoryBefore = this.getMemoryInfo();
    const networkBefore = this.getNetworkRequests();
    
    try {
      // Simulate registration process
      const result = await this.simulateRegistration(email, password);
      
      const duration = this.endMeasurement('registration');
      const memoryAfter = this.getMemoryInfo();
      const networkAfter = this.getNetworkRequests();
      
      const metrics: AuthMetrics = {
        operation: 'registration',
        duration,
        success: true,
        memoryUsed: memoryAfter ? memoryAfter.usedJSHeapSize - (memoryBefore?.usedJSHeapSize || 0) : 0,
        networkRequests: this.calculateNetworkDelta(networkBefore, networkAfter),
        timestamp: Date.now()
      };

      this.metrics.push(metrics);
      return metrics;
    } catch (error) {
      const metrics: AuthMetrics = {
        operation: 'registration',
        duration: this.endMeasurement('registration'),
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };

      this.metrics.push(metrics);
      return metrics;
    }
  }

  async collectSessionValidationMetrics(): Promise<AuthMetrics> {
    this.startMeasurement('session-validation');
    
    try {
      // Simulate session validation
      await this.simulateSessionValidation();
      const duration = this.endMeasurement('session-validation');
      
      const metrics: AuthMetrics = {
        operation: 'session-validation',
        duration,
        success: true,
        timestamp: Date.now()
      };

      this.metrics.push(metrics);
      return metrics;
    } catch (error) {
      const metrics: AuthMetrics = {
        operation: 'session-validation', 
        duration: this.endMeasurement('session-validation'),
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };

      this.metrics.push(metrics);
      return metrics;
    }
  }

  async collectTokenRefreshMetrics(): Promise<AuthMetrics> {
    this.startMeasurement('token-refresh');
    
    try {
      // Simulate token refresh
      await this.simulateTokenRefresh();
      const duration = this.endMeasurement('token-refresh');
      
      const metrics: AuthMetrics = {
        operation: 'token-refresh',
        duration,
        success: true,
        timestamp: Date.now()
      };

      this.metrics.push(metrics);
      return metrics;
    } catch (error) {
      const metrics: AuthMetrics = {
        operation: 'token-refresh',
        duration: this.endMeasurement('token-refresh'),
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };

      this.metrics.push(metrics);
      return metrics;
    }
  }

  async collectLogoutMetrics(): Promise<AuthMetrics> {
    this.startMeasurement('logout');
    
    try {
      // Simulate logout process
      await this.simulateLogout();
      const duration = this.endMeasurement('logout');
      
      const metrics: AuthMetrics = {
        operation: 'logout',
        duration,
        success: true,
        timestamp: Date.now()
      };

      this.metrics.push(metrics);
      return metrics;
    } catch (error) {
      const metrics: AuthMetrics = {
        operation: 'logout',
        duration: this.endMeasurement('logout'),
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };

      this.metrics.push(metrics);
      return metrics;
    }
  }

  private getMemoryInfo(): MemoryInfo | null {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit
      };
    }
    return null;
  }

  private getNetworkRequests(): NetworkRequest[] {
    try {
      // Collect network performance entries
      const entries = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
      return entries.map(entry => ({
        name: entry.name,
        entryType: entry.entryType,
        startTime: entry.startTime,
        duration: entry.duration,
        transferSize: entry.transferSize
      }));
    } catch (error) {
      console.warn('Could not collect network requests:', error);
      return [];
    }
  }

  private calculateNetworkDelta(before: NetworkRequest[], after: NetworkRequest[]): NetworkRequest[] {
    if (before.length === 0) return after;
    return after.slice(before.length);
  }

  // Simulation methods for testing
  private async simulateLogin(email: string, password: string): Promise<any> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, Math.random() * 500 + 100));
    return { user: { email }, session: { access_token: 'mock-token' } };
  }

  private async simulateRegistration(email: string, password: string): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, Math.random() * 800 + 200));
    return { user: { email }, session: { access_token: 'mock-token' } };
  }

  private async simulateSessionValidation(): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, Math.random() * 200 + 50));
    return { valid: true };
  }

  private async simulateTokenRefresh(): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, Math.random() * 300 + 100));
    return { access_token: 'new-mock-token' };
  }

  private async simulateLogout(): Promise<any> {
    await new Promise(resolve => setTimeout(resolve, Math.random() * 150 + 50));
    return { success: true };
  }

  exportMetrics(): AuthMetrics[] {
    return [...this.metrics];
  }

  clearMetrics(): void {
    this.metrics = [];
  }

  getMetricsSummary(): { total: number; successful: number; failed: number; averageDuration: number } {
    const total = this.metrics.length;
    const successful = this.metrics.filter(m => m.success).length;
    const failed = total - successful;
    const averageDuration = this.metrics.reduce((sum, m) => sum + m.duration, 0) / total || 0;

    return {
      total,
      successful,
      failed,
      averageDuration
    };
  }
}
