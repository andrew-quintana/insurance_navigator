import { AuthMetricsCollector, AuthMetrics } from './auth-metrics';

export interface UploadMetrics {
  fileName: string;
  fileSize: number;
  uploadTime: number;
  memoryUsed: number;
  success: boolean;
  error?: string;
  timestamp: number;
  progressUpdates?: number;
  networkRequests?: number;
}

export interface ChatMetrics {
  messageLength: number;
  responseTime: number;
  responseLength?: number;
  success: boolean;
  error?: string;
  timestamp: number;
  memoryUsed?: number;
  agentType?: string;
}

export interface DocumentStateMetrics {
  operation: string;
  duration: number;
  success: boolean;
  documentCount?: number;
  memoryUsed?: number;
  timestamp: number;
  error?: string;
}

export interface CoreWebVitals {
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay  
  cls: number; // Cumulative Layout Shift
  ttfb: number; // Time to First Byte
  fcp: number; // First Contentful Paint
}

export interface FrontendPerformanceMetrics {
  authenticationTime: number;      // Login/registration response time
  sessionValidation: number;       // Token validation timing  
  uploadInitiation: number;        // Time to start upload (authenticated)
  uploadCompletion: number;        // End-to-end upload time (authenticated)
  chatResponseTime: number;        // Agent response latency (authenticated)
  memoryUsage: any;                // Browser memory consumption
  coreWebVitals: CoreWebVitals;    // LCP, FID, CLS metrics
  networkRequests: any[];          // API call performance
}

export class FrontendMetricsCollector {
  private authMetrics: AuthMetricsCollector;
  private metrics: {
    uploads: UploadMetrics[];
    chat: ChatMetrics[];
    documentState: DocumentStateMetrics[];
    coreWebVitals: CoreWebVitals[];
  };

  constructor() {
    this.authMetrics = new AuthMetricsCollector();
    this.metrics = {
      uploads: [],
      chat: [],
      documentState: [],
      coreWebVitals: []
    };
  }

  // Authentication metrics delegation
  async collectLoginMetrics(email: string, password: string): Promise<AuthMetrics> {
    return this.authMetrics.collectLoginMetrics(email, password);
  }

  async collectRegistrationMetrics(email: string, password: string): Promise<AuthMetrics> {
    return this.authMetrics.collectRegistrationMetrics(email, password);
  }

  async collectSessionValidationMetrics(): Promise<AuthMetrics> {
    return this.authMetrics.collectSessionValidationMetrics();
  }

  async collectTokenRefreshMetrics(): Promise<AuthMetrics> {
    return this.authMetrics.collectTokenRefreshMetrics();
  }

  async collectLogoutMetrics(): Promise<AuthMetrics> {
    return this.authMetrics.collectLogoutMetrics();
  }

  // Upload performance metrics
  async collectUploadMetrics(file: File, progressCallback?: (progress: number) => void): Promise<UploadMetrics> {
    const startTime = performance.now();
    const memoryBefore = this.getMemoryInfo();
    const networkBefore = this.getNetworkRequests();
    let progressUpdates = 0;
    
    try {
      // Monitor authenticated upload
      const result = await this.simulateUpload(file, progressCallback);
      
      const duration = performance.now() - startTime;
      const memoryAfter = this.getMemoryInfo();
      const networkAfter = this.getNetworkRequests();
      
      const metrics: UploadMetrics = {
        fileName: file.name,
        fileSize: file.size,
        uploadTime: duration,
        memoryUsed: memoryAfter ? memoryAfter.usedJSHeapSize - (memoryBefore?.usedJSHeapSize || 0) : 0,
        success: true,
        timestamp: Date.now(),
        progressUpdates,
        networkRequests: this.calculateNetworkDelta(networkBefore, networkAfter).length
      };

      this.metrics.uploads.push(metrics);
      return metrics;
    } catch (error) {
      const metrics: UploadMetrics = {
        fileName: file.name,
        fileSize: file.size,
        uploadTime: performance.now() - startTime,
        memoryUsed: 0,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now(),
        progressUpdates,
        networkRequests: this.calculateNetworkDelta(networkBefore, this.getNetworkRequests()).length
      };

      this.metrics.uploads.push(metrics);
      return metrics;
    }
  }

  // Chat performance metrics
  async collectChatMetrics(message: string, agentType: string = 'default'): Promise<ChatMetrics> {
    const startTime = performance.now();
    const memoryBefore = this.getMemoryInfo();
    
    try {
      const response = await this.simulateChatMessage(message, agentType);
      const duration = performance.now() - startTime;
      const memoryAfter = this.getMemoryInfo();
      
      const metrics: ChatMetrics = {
        messageLength: message.length,
        responseTime: duration,
        responseLength: response.text?.length || 0,
        success: true,
        timestamp: Date.now(),
        memoryUsed: memoryAfter ? memoryAfter.usedJSHeapSize - (memoryBefore?.usedJSHeapSize || 0) : 0,
        agentType
      };

      this.metrics.chat.push(metrics);
      return metrics;
    } catch (error) {
      const metrics: ChatMetrics = {
        messageLength: message.length,
        responseTime: performance.now() - startTime,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now(),
        agentType
      };

      this.metrics.chat.push(metrics);
      return metrics;
    }
  }

  // Document state management metrics
  async collectDocumentStateMetrics(operation: string, documentCount?: number): Promise<DocumentStateMetrics> {
    const startTime = performance.now();
    const memoryBefore = this.getMemoryInfo();
    
    try {
      await this.simulateDocumentStateOperation(operation);
      const duration = performance.now() - startTime;
      const memoryAfter = this.getMemoryInfo();
      
      const metrics: DocumentStateMetrics = {
        operation,
        duration,
        success: true,
        documentCount,
        memoryUsed: memoryAfter ? memoryAfter.usedJSHeapSize - (memoryBefore?.usedJSHeapSize || 0) : 0,
        timestamp: Date.now()
      };

      this.metrics.documentState.push(metrics);
      return metrics;
    } catch (error) {
      const metrics: DocumentStateMetrics = {
        operation,
        duration: performance.now() - startTime,
        success: false,
        documentCount,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      };

      this.metrics.documentState.push(metrics);
      return metrics;
    }
  }

  // Core Web Vitals collection
  collectCoreWebVitals(): Promise<CoreWebVitals> {
    return new Promise((resolve) => {
      // Use Performance Observer for real metrics when available
      if ('PerformanceObserver' in window) {
        this.observeCoreWebVitals(resolve);
      } else {
        // Fallback to basic metrics
        const vitals = this.getBasicCoreWebVitals();
        resolve(vitals);
      }
    });
  }

  // Performance monitoring for specific operations
  startPerformanceMark(name: string): void {
    if ('performance' in window && 'mark' in performance) {
      performance.mark(`${name}-start`);
    }
  }

  endPerformanceMark(name: string): number {
    if ('performance' in window && 'mark' in performance) {
      performance.mark(`${name}-end`);
      performance.measure(name, `${name}-start`, `${name}-end`);
      
      const measure = performance.getEntriesByName(name)[0];
      return measure ? measure.duration : 0;
    }
    return 0;
  }

  // Memory monitoring
  getCurrentMemoryUsage(): any {
    return this.getMemoryInfo();
  }

  // Network performance monitoring
  getCurrentNetworkPerformance(): any[] {
    return this.getNetworkRequests();
  }

  // Metrics export and analysis
  exportAllMetrics(): {
    auth: AuthMetrics[];
    uploads: UploadMetrics[];
    chat: ChatMetrics[];
    documentState: DocumentStateMetrics[];
    coreWebVitals: CoreWebVitals[];
  } {
    return {
      auth: this.authMetrics.exportMetrics(),
      uploads: [...this.metrics.uploads],
      chat: [...this.metrics.chat],
      documentState: [...this.metrics.documentState],
      coreWebVitals: [...this.metrics.coreWebVitals]
    };
  }

  getPerformanceSummary(): {
    auth: { total: number; successful: number; failed: number; averageDuration: number };
    uploads: { total: number; successful: number; failed: number; averageDuration: number };
    chat: { total: number; successful: number; failed: number; averageDuration: number };
    documentState: { total: number; successful: number; failed: number; averageDuration: number };
  } {
    return {
      auth: this.authMetrics.getMetricsSummary(),
      uploads: this.getMetricsSummary(this.metrics.uploads),
      chat: this.getMetricsSummary(this.metrics.chat),
      documentState: this.getMetricsSummary(this.metrics.documentState)
    };
  }

  clearAllMetrics(): void {
    this.authMetrics.clearMetrics();
    this.metrics.uploads = [];
    this.metrics.chat = [];
    this.metrics.documentState = [];
    this.metrics.coreWebVitals = [];
  }

  // Private helper methods
  private getMemoryInfo(): any {
    if ('memory' in performance) {
      return (performance as any).memory;
    }
    return null;
  }

  private getNetworkRequests(): any[] {
    try {
      return performance.getEntriesByType('resource') as any[];
    } catch (error) {
      return [];
    }
  }

  private calculateNetworkDelta(before: any[], after: any[]): any[] {
    if (before.length === 0) return after;
    return after.slice(before.length);
  }

  private getMetricsSummary(metrics: any[]): { total: number; successful: number; failed: number; averageDuration: number } {
    const total = metrics.length;
    const successful = metrics.filter(m => m.success).length;
    const failed = total - successful;
    const averageDuration = metrics.reduce((sum, m) => sum + m.duration, 0) / total || 0;

    return { total, successful, failed, averageDuration };
  }

  private observeCoreWebVitals(resolve: (vitals: CoreWebVitals) => void): void {
    const vitals: CoreWebVitals = {
      lcp: 0,
      fid: 0,
      cls: 0,
      ttfb: 0,
      fcp: 0
    };

    let metricsCollected = 0;
    const totalMetrics = 5;

    const checkComplete = () => {
      metricsCollected++;
      if (metricsCollected >= totalMetrics) {
        this.metrics.coreWebVitals.push(vitals);
        resolve(vitals);
      }
    };

    // LCP (Largest Contentful Paint)
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          vitals.lcp = lastEntry.startTime;
          checkComplete();
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      } catch (error) {
        console.warn('LCP observation failed:', error);
        checkComplete();
      }
    } else {
      checkComplete();
    }

    // FID (First Input Delay)
    try {
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const firstEntry = entries[0] as PerformanceEventTiming;
        vitals.fid = firstEntry.processingStart - firstEntry.startTime;
        checkComplete();
      });
      fidObserver.observe({ entryTypes: ['first-input'] });
    } catch (error) {
      console.warn('FID observation failed:', error);
      checkComplete();
    }

    // CLS (Cumulative Layout Shift)
    try {
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
          }
        }
        vitals.cls = clsValue;
        checkComplete();
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    } catch (error) {
      console.warn('CLS observation failed:', error);
      checkComplete();
    }

    // TTFB (Time to First Byte)
    try {
      const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (navigationEntry) {
        vitals.ttfb = navigationEntry.responseStart - navigationEntry.requestStart;
      }
      checkComplete();
    } catch (error) {
      console.warn('TTFB calculation failed:', error);
      checkComplete();
    }

    // FCP (First Contentful Paint)
    try {
      const fcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const firstEntry = entries[0];
        vitals.fcp = firstEntry.startTime;
        checkComplete();
      });
      fcpObserver.observe({ entryTypes: ['paint'] });
    } catch (error) {
      console.warn('FCP observation failed:', error);
      checkComplete();
    }
  }

  private getBasicCoreWebVitals(): CoreWebVitals {
    return {
      lcp: 0,
      fid: 0,
      cls: 0,
      ttfb: 0,
      fcp: 0
    };
  }

  // Simulation methods for testing
  private async simulateUpload(file: File, progressCallback?: (progress: number) => void): Promise<any> {
    const totalSteps = 10;
    for (let i = 0; i <= totalSteps; i++) {
      if (progressCallback) {
        progressCallback((i / totalSteps) * 100);
      }
      await new Promise(resolve => setTimeout(resolve, Math.random() * 200 + 100));
    }
    return { documentId: 'mock-doc-id', success: true };
  }

  private async simulateChatMessage(message: string, agentType: string): Promise<any> {
    // Simulate agent response time
    await new Promise(resolve => setTimeout(resolve, Math.random() * 2000 + 500));
    return { text: `Mock response to: ${message}`, agentType };
  }

  private async simulateDocumentStateOperation(operation: string): Promise<any> {
    // Simulate document state operation
    await new Promise(resolve => setTimeout(resolve, Math.random() * 500 + 100));
    return { success: true, operation };
  }
}
