export interface PerformanceEntry {
  name: string;
  entryType: string;
  startTime: number;
  duration: number;
}

export interface MemoryInfo {
  usedJSHeapSize: number;
  totalJSHeapSize: number;
  jsHeapSizeLimit: number;
}

export interface PerformanceMetrics {
  navigationMetrics: PerformanceEntry[];
  resourceMetrics: PerformanceEntry[];
  paintMetrics: PerformanceEntry[];
  measureMetrics: PerformanceEntry[];
  memoryUsage: MemoryInfo | null;
  slowOperations: Array<{ name: string; duration: number; threshold: number }>;
  memoryLeaks: Array<{ operation: string; increase: number; threshold: number }>;
}

export class BrowserPerformanceMonitor {
  private observer: PerformanceObserver | null = null;
  private metrics: PerformanceEntry[] = [];
  private memoryBaseline: MemoryInfo | null = null;
  private operationStartTimes: Map<string, number> = new Map();
  private slowOperationThreshold = 1000; // 1 second
  private memoryLeakThreshold = 10 * 1024 * 1024; // 10MB

  start() {
    if ('PerformanceObserver' in window) {
      this.observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.metrics.push(entry as PerformanceEntry);
          this.analyzeEntry(entry as PerformanceEntry);
        }
      });

      // Monitor different performance metrics
      try {
        this.observer.observe({ entryTypes: ['navigation', 'resource', 'measure', 'paint'] });
        console.log('✅ Browser performance monitoring started');
      } catch (error) {
        console.warn('⚠️ Some performance metrics not available:', error);
        // Try to observe available entry types
        this.observeAvailableMetrics();
      }
    } else {
      console.warn('⚠️ PerformanceObserver not supported in this browser');
    }

    // Set memory baseline
    this.setMemoryBaseline();
  }

  stop() {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
      console.log('🛑 Browser performance monitoring stopped');
    }
  }

  // Start monitoring a specific operation
  startOperation(operationName: string): void {
    this.operationStartTimes.set(operationName, performance.now());
    console.log(`🚀 Started monitoring operation: ${operationName}`);
  }

  // End monitoring a specific operation
  endOperation(operationName: string): number {
    const startTime = this.operationStartTimes.get(operationName);
    if (startTime) {
      const duration = performance.now() - startTime;
      this.operationStartTimes.delete(operationName);
      
      // Check if operation was slow
      if (duration > this.slowOperationThreshold) {
        console.warn(`🐌 Slow operation detected: ${operationName} took ${duration.toFixed(2)}ms (threshold: ${this.slowOperationThreshold}ms)`);
      }
      
      console.log(`✅ Operation completed: ${operationName} in ${duration.toFixed(2)}ms`);
      return duration;
    }
    return 0;
  }

  // Monitor memory usage for specific operations
  startMemoryMonitoring(operationName: string): MemoryInfo | null {
    const memoryInfo = this.getMemoryInfo();
    if (memoryInfo) {
      this.operationStartTimes.set(`memory-${operationName}`, memoryInfo.usedJSHeapSize);
      console.log(`🧠 Started memory monitoring for: ${operationName} (current: ${this.formatBytes(memoryInfo.usedJSHeapSize)})`);
    }
    return memoryInfo;
  }

  endMemoryMonitoring(operationName: string): { increase: number; percentage: number } | null {
    const startMemory = this.operationStartTimes.get(`memory-${operationName}`);
    if (startMemory) {
      const currentMemory = this.getMemoryInfo();
      if (currentMemory) {
        const increase = currentMemory.usedJSHeapSize - startMemory;
        const percentage = (increase / startMemory) * 100;
        
        this.operationStartTimes.delete(`memory-${operationName}`);
        
        // Check for potential memory leaks
        if (increase > this.memoryLeakThreshold) {
          console.warn(`🚨 Potential memory leak detected in ${operationName}: ${this.formatBytes(increase)} increase`);
        }
        
        console.log(`🧠 Memory monitoring completed for ${operationName}: ${this.formatBytes(increase)} (${percentage.toFixed(2)}%)`);
        return { increase, percentage };
      }
    }
    return null;
  }

  // Monitor authentication operations specifically
  startAuthMonitoring(operation: string): void {
    this.startOperation(`auth-${operation}`);
    this.startMemoryMonitoring(`auth-${operation}`);
  }

  endAuthMonitoring(operation: string): { duration: number; memoryChange: { increase: number; percentage: number } | null } {
    const duration = this.endOperation(`auth-${operation}`);
    const memoryChange = this.endMemoryMonitoring(`auth-${operation}`);
    
    return { duration, memoryChange };
  }

  // Monitor upload operations
  startUploadMonitoring(fileName: string, fileSize: number): void {
    this.startOperation(`upload-${fileName}`);
    this.startMemoryMonitoring(`upload-${fileName}`);
    console.log(`📤 Started upload monitoring: ${fileName} (${this.formatBytes(fileSize)})`);
  }

  endUploadMonitoring(fileName: string): { duration: number; memoryChange: { increase: number; percentage: number } | null } {
    const duration = this.endOperation(`upload-${fileName}`);
    const memoryChange = this.endMemoryMonitoring(`upload-${fileName}`);
    
    console.log(`📤 Upload monitoring completed: ${fileName}`);
    return { duration, memoryChange };
  }

  // Monitor chat operations
  startChatMonitoring(messageLength: number): void {
    this.startOperation(`chat-${Date.now()}`);
    this.startMemoryMonitoring(`chat-${Date.now()}`);
    console.log(`💬 Started chat monitoring: message length ${messageLength}`);
  }

  endChatMonitoring(operationId: string): { duration: number; memoryChange: { increase: number; percentage: number } | null } {
    const duration = this.endOperation(`chat-${operationId}`);
    const memoryChange = this.endMemoryMonitoring(`chat-${operationId}`);
    
    console.log(`💬 Chat monitoring completed`);
    return { duration, memoryChange };
  }

  // Get current performance metrics
  getMetrics(): PerformanceMetrics {
    const slowOperations = this.metrics
      .filter(entry => entry.duration > this.slowOperationThreshold)
      .map(entry => ({
        name: entry.name,
        duration: entry.duration,
        threshold: this.slowOperationThreshold
      }));

    const memoryLeaks = this.detectMemoryLeaks();

    return {
      navigationMetrics: this.metrics.filter(m => m.entryType === 'navigation'),
      resourceMetrics: this.metrics.filter(m => m.entryType === 'resource'),
      paintMetrics: this.metrics.filter(m => m.entryType === 'paint'),
      measureMetrics: this.metrics.filter(m => m.entryType === 'measure'),
      memoryUsage: this.getMemoryInfo(),
      slowOperations,
      memoryLeaks
    };
  }

  // Export metrics for analysis
  exportMetrics(): string {
    return JSON.stringify(this.getMetrics(), null, 2);
  }

  // Clear collected metrics
  clearMetrics(): void {
    this.metrics = [];
    this.operationStartTimes.clear();
    console.log('🧹 Performance metrics cleared');
  }

  // Set performance thresholds
  setThresholds(slowOperationThreshold: number, memoryLeakThreshold: number): void {
    this.slowOperationThreshold = slowOperationThreshold;
    this.memoryLeakThreshold = memoryLeakThreshold;
    console.log(`⚙️ Thresholds updated: slow operations > ${slowOperationThreshold}ms, memory leaks > ${this.formatBytes(memoryLeakThreshold)}`);
  }

  // Get memory usage summary
  getMemorySummary(): { current: MemoryInfo | null; baseline: MemoryInfo | null; change: { used: number; percentage: number } | null } {
    const current = this.getMemoryInfo();
    const baseline = this.memoryBaseline;
    
    if (current && baseline) {
      const usedChange = current.usedJSHeapSize - baseline.usedJSHeapSize;
      const percentageChange = (usedChange / baseline.usedJSHeapSize) * 100;
      
      return {
        current,
        baseline,
        change: {
          used: usedChange,
          percentage: percentageChange
        }
      };
    }
    
    return { current, baseline, change: null };
  }

  // Private methods
  private analyzeEntry(entry: PerformanceEntry) {
    // Log slow operations
    if (entry.duration > this.slowOperationThreshold) {
      console.warn(`🐌 Slow operation detected: ${entry.name} took ${entry.duration.toFixed(2)}ms`);
    }

    // Monitor memory usage
    const memory = this.getMemoryInfo();
    if (memory) {
      if (memory.usedJSHeapSize > 50 * 1024 * 1024) { // 50MB
        console.warn(`⚠️ High memory usage: ${this.formatBytes(memory.usedJSHeapSize)}`);
      }
    }
  }

  private observeAvailableMetrics(): void {
    const availableTypes: string[] = [];
    
    // Check which entry types are available
    ['navigation', 'resource', 'measure', 'paint'].forEach(type => {
      try {
        const testObserver = new PerformanceObserver(() => {});
        testObserver.observe({ entryTypes: [type] });
        availableTypes.push(type);
        testObserver.disconnect();
      } catch (error) {
        console.log(`Entry type '${type}' not available`);
      }
    });

    if (availableTypes.length > 0) {
      console.log(`📊 Available performance metrics: ${availableTypes.join(', ')}`);
      this.observer?.observe({ entryTypes: availableTypes as any });
    }
  }

  private setMemoryBaseline(): void {
    this.memoryBaseline = this.getMemoryInfo();
    if (this.memoryBaseline) {
      console.log(`📊 Memory baseline set: ${this.formatBytes(this.memoryBaseline.usedJSHeapSize)}`);
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

  private detectMemoryLeaks(): Array<{ operation: string; increase: number; threshold: number }> {
    const leaks: Array<{ operation: string; increase: number; threshold: number }> = [];
    
    if (this.memoryBaseline) {
      const current = this.getMemoryInfo();
      if (current) {
        const increase = current.usedJSHeapSize - this.memoryBaseline.usedJSHeapSize;
        if (increase > this.memoryLeakThreshold) {
          leaks.push({
            operation: 'overall',
            increase,
            threshold: this.memoryLeakThreshold
          });
        }
      }
    }
    
    return leaks;
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}
