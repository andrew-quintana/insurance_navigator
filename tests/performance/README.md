# Frontend Performance Testing Infrastructure

This directory contains comprehensive performance testing for the Insurance Navigator frontend, covering authentication, upload components, chat interface, and cross-browser performance validation.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm 8+
- Frontend application running on `http://localhost:3000`
- Artillery.js installed globally

### Installation
```bash
# Install Artillery.js globally
npm install -g artillery

# Install local dependencies
npm install

# Verify installation
artillery --version
```

### Run All Performance Tests
```bash
npm run test:all
```

## 📊 Test Types

### 1. Authentication Load Testing
Tests authentication performance under normal and high load conditions.

```bash
# Run authentication load test
npm run test:auth

# Run authentication stress test
npm run test:stress
```

**Performance Targets:**
- Authentication time: < 1 second
- Session validation: < 500ms
- Error rate: < 1%

### 2. Cross-Browser Performance Testing
Validates performance across Chrome, Firefox, and Safari.

```bash
npm run test:cross-browser
```

**Test Coverage:**
- Chrome (Windows)
- Firefox (Windows)
- Safari (macOS)

### 3. Responsive Design Performance Testing
Tests performance across different viewport sizes.

```bash
npm run test:responsive
```

**Viewport Sizes:**
- Mobile: 375x667
- Tablet: 768x1024
- Desktop: 1920x1080

### 4. Comprehensive Load Testing
Full system performance validation with Artillery.js.

```bash
# Run complete load test suite
node run-auth-performance.js
```

## 🔧 Configuration

### Artillery Configuration Files

#### `artillery-auth.yml`
- **Phases**: Gradual ramp-up from 1 to 5 users/second
- **Duration**: 18 minutes total
- **Scenarios**: User registration, login, upload, chat
- **Targets**: 1000ms response time, <1% error rate

#### `artillery-stress-auth.yml`
- **Phases**: Stress testing up to 30 users/second
- **Duration**: 5 minutes total
- **Scenarios**: High-load authentication, memory leak testing
- **Targets**: 5000ms response time, <5% error rate

### Performance Thresholds

```javascript
const PERFORMANCE_TARGETS = {
  authenticationTime: 1000,     // < 1 second
  sessionValidation: 500,       // < 500ms
  tokenRefresh: 1000,          // < 1 second
  uploadInitiation: 2000,      // < 2 seconds
  chatResponseTime: 5000,      // < 5 seconds
  errorRate: 1,                // < 1%
  concurrentUsers: 10          // Support 10 concurrent users
};
```

## 📈 Metrics Collection

### Frontend Performance Metrics
The system collects comprehensive metrics including:

- **Authentication Metrics**: Login, registration, session validation
- **Upload Metrics**: File upload performance, memory usage
- **Chat Metrics**: Response times, agent performance
- **Core Web Vitals**: LCP, FID, CLS, TTFB, FCP
- **Memory Monitoring**: Usage patterns, leak detection
- **Network Performance**: Request timing, error rates

### Metrics Classes

#### `AuthMetricsCollector`
- Collects authentication-specific performance data
- Monitors memory usage during auth operations
- Tracks network request performance

#### `FrontendMetricsCollector`
- Comprehensive frontend performance monitoring
- Integrates with authentication metrics
- Collects Core Web Vitals

#### `BrowserPerformanceMonitor`
- Real-time browser performance monitoring
- Memory leak detection
- Slow operation identification

## 🧪 Test Scenarios

### Authentication Flow Testing
1. **User Registration**: Email validation, account creation
2. **User Login**: Credential validation, session creation
3. **Session Management**: Token refresh, validation
4. **Logout**: Session cleanup, redirect handling

### Upload Component Testing
1. **File Selection**: Drag-and-drop, file picker
2. **Upload Initiation**: Authentication headers, progress tracking
3. **Progress Monitoring**: Real-time updates, status synchronization
4. **Completion Handling**: Success notifications, error recovery

### Chat Interface Testing
1. **Message Sending**: Authentication, user context
2. **Agent Responses**: Response time, accuracy validation
3. **Conversation Management**: History, context preservation
4. **Real-time Features**: WebSocket connections, typing indicators

### Cross-Browser Validation
1. **Chrome**: File API, WebSocket stability
2. **Firefox**: Upload behavior, authentication persistence
3. **Safari**: macOS-specific features, session management

### Responsive Design Testing
1. **Mobile**: Touch interactions, mobile-optimized layouts
2. **Tablet**: Hybrid input methods, responsive navigation
3. **Desktop**: Advanced features, keyboard shortcuts

## 📊 Results Analysis

### Performance Reports
Test results are automatically analyzed and stored in the `results/` directory:

- **Response Time Analysis**: Average, P95, P99 percentiles
- **Error Rate Calculation**: 4xx and 5xx error percentages
- **Throughput Metrics**: Requests per second, concurrent users
- **Memory Usage**: Heap usage, leak detection
- **Cross-Browser Comparison**: Performance differences across browsers

### Baseline Metrics
The `baseline-metrics.json` file contains established performance baselines for:

- Authentication operations
- Upload performance
- Chat response times
- Cross-browser compatibility
- Responsive design performance

### Regression Detection
The system automatically detects performance regressions by comparing current results against baselines:

```javascript
// Example regression detection
if (current.authResponseTime > baseline.authResponseTime * 1.2) {
  throw new Error(`Performance regression: Auth response time increased by ${((current.authResponseTime / baseline.authResponseTime - 1) * 100).toFixed(1)}%`);
}
```

## 🚨 Error Handling

### Network Failures
- Automatic retry mechanisms
- Graceful degradation
- User-friendly error messages

### Performance Degradation
- Real-time monitoring alerts
- Automatic threshold checking
- Performance regression detection

### Memory Issues
- Memory leak detection
- Usage pattern monitoring
- Automatic cleanup recommendations

## 🔍 Debugging

### Performance Issues
```bash
# Check current performance metrics
node -e "const { FrontendMetricsCollector } = require('./ui/lib/performance/frontend-metrics'); const collector = new FrontendMetricsCollector(); console.log(collector.getPerformanceSummary());"

# Monitor memory usage
node -e "const { BrowserPerformanceMonitor } = require('./ui/lib/performance/browser-monitor'); const monitor = new BrowserPerformanceMonitor(); monitor.start(); console.log(monitor.getMemorySummary());"
```

### Load Test Issues
```bash
# Run with verbose output
artillery run artillery-auth.yml --verbose

# Generate HTML report
artillery run artillery-auth.yml --output results.json
artillery report results.json
```

## 📋 Test Execution

### Manual Testing
```bash
# Run specific test types
npm run test:auth          # Authentication only
npm run test:stress        # Stress testing only
npm run test:cross-browser # Cross-browser only
npm run test:responsive    # Responsive design only
```

### Automated Testing
```bash
# Run complete test suite
npm run test:all

# Clean results
npm run clean

# Generate reports
npm run report
```

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
- name: Performance Tests
  run: |
    cd performance
    npm install
    npm run test:all
```

## 📚 API Reference

### Performance Metrics Classes

#### `AuthMetricsCollector`
```typescript
class AuthMetricsCollector {
  async collectLoginMetrics(email: string, password: string): Promise<AuthMetrics>
  async collectRegistrationMetrics(email: string, password: string): Promise<AuthMetrics>
  async collectSessionValidationMetrics(): Promise<AuthMetrics>
  async collectTokenRefreshMetrics(): Promise<AuthMetrics>
  async collectLogoutMetrics(): Promise<AuthMetrics>
  exportMetrics(): AuthMetrics[]
  getMetricsSummary(): MetricsSummary
}
```

#### `FrontendMetricsCollector`
```typescript
class FrontendMetricsCollector {
  async collectUploadMetrics(file: File): Promise<UploadMetrics>
  async collectChatMetrics(message: string): Promise<ChatMetrics>
  async collectDocumentStateMetrics(operation: string): Promise<DocumentStateMetrics>
  collectCoreWebVitals(): Promise<CoreWebVitals>
  exportAllMetrics(): AllMetrics
  getPerformanceSummary(): PerformanceSummary
}
```

#### `BrowserPerformanceMonitor`
```typescript
class BrowserPerformanceMonitor {
  start(): void
  stop(): void
  startOperation(operationName: string): void
  endOperation(operationName: string): number
  startMemoryMonitoring(operationName: string): MemoryInfo | null
  endMemoryMonitoring(operationName: string): MemoryChange | null
  getMetrics(): PerformanceMetrics
  exportMetrics(): string
}
```

## 🎯 Best Practices

### Performance Testing
1. **Baseline Establishment**: Always establish performance baselines before major changes
2. **Regular Monitoring**: Run performance tests regularly to detect regressions
3. **Realistic Scenarios**: Test with realistic user behavior patterns
4. **Cross-Browser Validation**: Ensure consistent performance across all target browsers

### Load Testing
1. **Gradual Ramp-up**: Start with low load and gradually increase
2. **Realistic Data**: Use realistic test data and user scenarios
3. **Monitoring**: Monitor system resources during load testing
4. **Recovery Testing**: Test system recovery after peak load

### Memory Management
1. **Baseline Monitoring**: Establish memory usage baselines
2. **Leak Detection**: Monitor for memory leaks during extended sessions
3. **Cleanup**: Ensure proper cleanup after operations
4. **Thresholds**: Set appropriate memory usage thresholds

## 🔮 Future Enhancements

### Planned Features
- **Real User Monitoring (RUM)**: Browser-based performance monitoring
- **Performance Budgets**: Automated performance budget enforcement
- **Advanced Analytics**: Machine learning-based performance analysis
- **Mobile Performance**: Native mobile app performance testing
- **Accessibility Performance**: Performance impact of accessibility features

### Integration Opportunities
- **CI/CD Pipeline**: Automated performance testing in deployment
- **Monitoring Dashboards**: Real-time performance visualization
- **Alert Systems**: Automated performance degradation alerts
- **Performance Reports**: Automated report generation and distribution

## 📞 Support

### Getting Help
- **Documentation**: Check this README and inline code comments
- **Issues**: Report issues in the project issue tracker
- **Performance Team**: Contact the performance testing team

### Contributing
1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for any changes
4. Ensure performance targets are maintained

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Maintainer**: Insurance Navigator Performance Team
