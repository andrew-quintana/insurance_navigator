# Phase 3 Monitoring and Observability Setup
## Production Monitoring for Agent System with Upload Pipeline Integration

**Date**: January 7, 2025  
**Status**: 📋 **SETUP COMPLETE**  
**Phase**: 3 - Cloud Backend with Production RAG Integration + Upload Pipeline

---

## Executive Summary

This document outlines the comprehensive monitoring and observability setup for Phase 3, building on the **successful Phase 2 RAG system** (100% query processing success, 0.71 quality score) and integrating the **existing upload pipeline** to ensure production-ready monitoring for the complete agentic system with document-to-chat functionality.

### **Monitoring Objectives**
1. **System Health**: Monitor all services and infrastructure
2. **Performance Tracking**: Track response times and throughput
3. **Quality Assurance**: Monitor response quality and user satisfaction
4. **Security Monitoring**: Track security events and threats
5. **Business Metrics**: Monitor user activity and document processing

---

## Monitoring Architecture

### **1. Monitoring Stack**

#### **Metrics Collection**
- **Prometheus**: Time-series metrics collection
- **Grafana**: Metrics visualization and dashboards
- **AlertManager**: Alert routing and notification
- **Node Exporter**: Node-level metrics
- **cAdvisor**: Container metrics

#### **Logging**
- **Fluentd**: Log collection and forwarding
- **Elasticsearch**: Log storage and indexing
- **Kibana**: Log visualization and analysis
- **Logstash**: Log processing and transformation

#### **Tracing**
- **Jaeger**: Distributed tracing
- **OpenTelemetry**: Telemetry data collection
- **Zipkin**: Alternative tracing solution

#### **APM (Application Performance Monitoring)**
- **New Relic**: Application performance monitoring
- **DataDog**: Infrastructure and application monitoring
- **Sentry**: Error tracking and performance monitoring

---

## Metrics Collection

### **1. Application Metrics**

#### **Upload Pipeline Service Metrics**
```python
# metrics/upload_pipeline_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Request metrics
upload_requests_total = Counter(
    'upload_requests_total',
    'Total number of upload requests',
    ['method', 'endpoint', 'status']
)

upload_request_duration = Histogram(
    'upload_request_duration_seconds',
    'Upload request duration in seconds',
    ['method', 'endpoint']
)

# Document processing metrics
documents_processed_total = Counter(
    'documents_processed_total',
    'Total number of documents processed',
    ['status', 'file_type']
)

document_processing_duration = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration in seconds',
    ['stage']
)

# Job queue metrics
job_queue_size = Gauge(
    'job_queue_size',
    'Current size of job queue'
)

job_processing_duration = Histogram(
    'job_processing_duration_seconds',
    'Job processing duration in seconds',
    ['job_type', 'status']
)

# Error metrics
upload_errors_total = Counter(
    'upload_errors_total',
    'Total number of upload errors',
    ['error_type', 'stage']
)
```

#### **RAG Service Metrics**
```python
# metrics/rag_service_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Query metrics
rag_queries_total = Counter(
    'rag_queries_total',
    'Total number of RAG queries',
    ['user_id', 'query_type', 'status']
)

rag_query_duration = Histogram(
    'rag_query_duration_seconds',
    'RAG query duration in seconds',
    ['query_type']
)

# Retrieval metrics
chunks_retrieved_total = Counter(
    'chunks_retrieved_total',
    'Total number of chunks retrieved',
    ['user_id', 'document_id']
)

similarity_scores = Histogram(
    'similarity_scores',
    'Distribution of similarity scores',
    ['query_type']
)

# Embedding metrics
embeddings_generated_total = Counter(
    'embeddings_generated_total',
    'Total number of embeddings generated',
    ['model', 'status']
)

embedding_generation_duration = Histogram(
    'embedding_generation_duration_seconds',
    'Embedding generation duration in seconds',
    ['model']
)

# Quality metrics
response_quality_scores = Histogram(
    'response_quality_scores',
    'Distribution of response quality scores',
    ['user_id']
)
```

#### **Agent API Service Metrics**
```python
# metrics/agent_api_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Chat metrics
chat_requests_total = Counter(
    'chat_requests_total',
    'Total number of chat requests',
    ['user_id', 'language', 'status']
)

chat_response_duration = Histogram(
    'chat_response_duration_seconds',
    'Chat response duration in seconds',
    ['workflow_stage']
)

# Agent workflow metrics
workflow_executions_total = Counter(
    'workflow_executions_total',
    'Total number of workflow executions',
    ['workflow_type', 'status']
)

workflow_duration = Histogram(
    'workflow_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_type', 'stage']
)

# LLM metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total number of LLM requests',
    ['provider', 'model', 'status']
)

llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['provider', 'model']
)

# User session metrics
active_sessions = Gauge(
    'active_sessions',
    'Number of active user sessions'
)

session_duration = Histogram(
    'session_duration_seconds',
    'User session duration in seconds'
)
```

### **2. Infrastructure Metrics**

#### **Kubernetes Metrics**
```yaml
# monitoring/kubernetes-metrics.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    rule_files:
      - "alert_rules.yml"
    
    scrape_configs:
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)
          - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
            action: replace
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: $1:$2
            target_label: __address__
          - action: labelmap
            regex: __meta_kubernetes_pod_label_(.+)
          - source_labels: [__meta_kubernetes_namespace]
            action: replace
            target_label: kubernetes_namespace
          - source_labels: [__meta_kubernetes_pod_name]
            action: replace
            target_label: kubernetes_pod_name
```

#### **Database Metrics**
```python
# metrics/database_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Connection metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_connections_total = Counter(
    'db_connections_total',
    'Total number of database connections',
    ['status']
)

# Query metrics
db_queries_total = Counter(
    'db_queries_total',
    'Total number of database queries',
    ['query_type', 'status']
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

# Transaction metrics
db_transactions_total = Counter(
    'db_transactions_total',
    'Total number of database transactions',
    ['status']
)

db_transaction_duration = Histogram(
    'db_transaction_duration_seconds',
    'Database transaction duration in seconds'
)

# Storage metrics
db_storage_size = Gauge(
    'db_storage_size_bytes',
    'Database storage size in bytes'
)

db_index_usage = Gauge(
    'db_index_usage_ratio',
    'Database index usage ratio',
    ['table_name', 'index_name']
)
```

### **3. Business Metrics**

#### **User Activity Metrics**
```python
# metrics/business_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# User metrics
users_registered_total = Counter(
    'users_registered_total',
    'Total number of users registered',
    ['registration_method']
)

users_active_daily = Gauge(
    'users_active_daily',
    'Number of daily active users'
)

users_active_monthly = Gauge(
    'users_active_monthly',
    'Number of monthly active users'
)

# Document metrics
documents_uploaded_total = Counter(
    'documents_uploaded_total',
    'Total number of documents uploaded',
    ['user_id', 'file_type', 'status']
)

documents_processed_total = Counter(
    'documents_processed_total',
    'Total number of documents processed',
    ['user_id', 'processing_stage', 'status']
)

# Chat metrics
chat_sessions_total = Counter(
    'chat_sessions_total',
    'Total number of chat sessions',
    ['user_id', 'language']
)

messages_sent_total = Counter(
    'messages_sent_total',
    'Total number of messages sent',
    ['user_id', 'message_type']
)

# Quality metrics
response_quality_average = Gauge(
    'response_quality_average',
    'Average response quality score',
    ['user_id']
)

user_satisfaction_score = Gauge(
    'user_satisfaction_score',
    'User satisfaction score',
    ['user_id']
)
```

---

## Dashboards

### **1. System Health Dashboard**

#### **Overview Dashboard**
```json
{
  "dashboard": {
    "title": "System Health Overview",
    "panels": [
      {
        "title": "Service Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=~\"upload-pipeline|rag-service|agent-api\"}",
            "legendFormat": "{{job}}"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{job}} - {{method}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{job}} - 95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "{{job}} - 5xx errors"
          }
        ]
      }
    ]
  }
}
```

#### **Service-Specific Dashboards**

##### **Upload Pipeline Dashboard**
```json
{
  "dashboard": {
    "title": "Upload Pipeline Service",
    "panels": [
      {
        "title": "Upload Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(upload_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Document Processing",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(documents_processed_total[5m])",
            "legendFormat": "{{status}} - {{file_type}}"
          }
        ]
      },
      {
        "title": "Processing Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(document_processing_duration_seconds_bucket[5m]))",
            "legendFormat": "{{stage}} - 95th percentile"
          }
        ]
      },
      {
        "title": "Job Queue Size",
        "type": "graph",
        "targets": [
          {
            "expr": "job_queue_size",
            "legendFormat": "Queue Size"
          }
        ]
      }
    ]
  }
}
```

##### **RAG Service Dashboard**
```json
{
  "dashboard": {
    "title": "RAG Service",
    "panels": [
      {
        "title": "RAG Queries",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(rag_queries_total[5m])",
            "legendFormat": "{{query_type}} - {{status}}"
          }
        ]
      },
      {
        "title": "Query Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(rag_query_duration_seconds_bucket[5m]))",
            "legendFormat": "{{query_type}} - 95th percentile"
          }
        ]
      },
      {
        "title": "Chunks Retrieved",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(chunks_retrieved_total[5m])",
            "legendFormat": "{{user_id}} - {{document_id}}"
          }
        ]
      },
      {
        "title": "Response Quality",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, rate(response_quality_scores_bucket[5m]))",
            "legendFormat": "{{user_id}} - Median"
          }
        ]
      }
    ]
  }
}
```

##### **Agent API Dashboard**
```json
{
  "dashboard": {
    "title": "Agent API Service",
    "panels": [
      {
        "title": "Chat Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(chat_requests_total[5m])",
            "legendFormat": "{{language}} - {{status}}"
          }
        ]
      },
      {
        "title": "Response Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(chat_response_duration_seconds_bucket[5m]))",
            "legendFormat": "{{workflow_stage}} - 95th percentile"
          }
        ]
      },
      {
        "title": "Active Sessions",
        "type": "graph",
        "targets": [
          {
            "expr": "active_sessions",
            "legendFormat": "Active Sessions"
          }
        ]
      },
      {
        "title": "LLM Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(llm_requests_total[5m])",
            "legendFormat": "{{provider}} - {{model}}"
          }
        ]
      }
    ]
  }
}
```

### **2. Business Metrics Dashboard**

#### **User Activity Dashboard**
```json
{
  "dashboard": {
    "title": "User Activity",
    "panels": [
      {
        "title": "User Registrations",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(users_registered_total[1h])",
            "legendFormat": "{{registration_method}}"
          }
        ]
      },
      {
        "title": "Active Users",
        "type": "graph",
        "targets": [
          {
            "expr": "users_active_daily",
            "legendFormat": "Daily Active Users"
          },
          {
            "expr": "users_active_monthly",
            "legendFormat": "Monthly Active Users"
          }
        ]
      },
      {
        "title": "Document Uploads",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(documents_uploaded_total[1h])",
            "legendFormat": "{{file_type}} - {{status}}"
          }
        ]
      },
      {
        "title": "Chat Sessions",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(chat_sessions_total[1h])",
            "legendFormat": "{{language}}"
          }
        ]
      }
    ]
  }
}
```

#### **Quality Metrics Dashboard**
```json
{
  "dashboard": {
    "title": "Quality Metrics",
    "panels": [
      {
        "title": "Response Quality",
        "type": "graph",
        "targets": [
          {
            "expr": "response_quality_average",
            "legendFormat": "{{user_id}} - Average"
          }
        ]
      },
      {
        "title": "User Satisfaction",
        "type": "graph",
        "targets": [
          {
            "expr": "user_satisfaction_score",
            "legendFormat": "{{user_id}} - Satisfaction"
          }
        ]
      },
      {
        "title": "Quality Distribution",
        "type": "histogram",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, rate(response_quality_scores_bucket[5m]))",
            "legendFormat": "Median"
          },
          {
            "expr": "histogram_quantile(0.95, rate(response_quality_scores_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

---

## Alerting Configuration

### **1. Critical Alerts**

#### **Service Down Alerts**
```yaml
# alerts/service-down.yml
groups:
- name: service-down
  rules:
  - alert: ServiceDown
    expr: up{job=~"upload-pipeline|rag-service|agent-api"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service {{ $labels.job }} is down"
      description: "Service {{ $labels.job }} has been down for more than 1 minute"

  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate for {{ $labels.job }}"
      description: "Error rate is {{ $value }} for service {{ $labels.job }}"
```

#### **Performance Alerts**
```yaml
# alerts/performance.yml
groups:
- name: performance
  rules:
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time for {{ $labels.job }}"
      description: "95th percentile response time is {{ $value }}s for {{ $labels.job }}"

  - alert: HighMemoryUsage
    expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage for {{ $labels.pod }}"
      description: "Memory usage is {{ $value }}% for pod {{ $labels.pod }}"

  - alert: HighCPUUsage
    expr: (rate(container_cpu_usage_seconds_total[5m]) / container_spec_cpu_quota) > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage for {{ $labels.pod }}"
      description: "CPU usage is {{ $value }}% for pod {{ $labels.pod }}"
```

#### **Business Alerts**
```yaml
# alerts/business.yml
groups:
- name: business
  rules:
  - alert: LowResponseQuality
    expr: response_quality_average < 0.7
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Low response quality for {{ $labels.user_id }}"
      description: "Response quality is {{ $value }} for user {{ $labels.user_id }}"

  - alert: HighDocumentProcessingTime
    expr: histogram_quantile(0.95, rate(document_processing_duration_seconds_bucket[5m])) > 60
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High document processing time"
      description: "95th percentile processing time is {{ $value }}s"

  - alert: LowUserSatisfaction
    expr: user_satisfaction_score < 4.0
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: "Low user satisfaction for {{ $labels.user_id }}"
      description: "User satisfaction is {{ $value }} for user {{ $labels.user_id }}"
```

### **2. Alert Routing**

#### **AlertManager Configuration**
```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@yourdomain.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://127.0.0.1:5001/'

- name: 'critical-alerts'
  email_configs:
  - to: 'oncall@yourdomain.com'
    subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts-critical'
    title: 'CRITICAL: {{ .GroupLabels.alertname }}'
    text: |
      {{ range .Alerts }}
      {{ .Annotations.summary }}
      {{ .Annotations.description }}
      {{ end }}

- name: 'warning-alerts'
  email_configs:
  - to: 'team@yourdomain.com'
    subject: 'WARNING: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts-warning'
    title: 'WARNING: {{ .GroupLabels.alertname }}'
    text: |
      {{ range .Alerts }}
      {{ .Annotations.summary }}
      {{ .Annotations.description }}
      {{ end }}
```

---

## Logging Configuration

### **1. Application Logging**

#### **Structured Logging**
```python
# logging/structured_logging.py
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_request(self, method, endpoint, status, duration, user_id=None):
        """Log HTTP request with structured data."""
        log_data = {
            "event_type": "http_request",
            "method": method,
            "endpoint": endpoint,
            "status": status,
            "duration": duration,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))
    
    def log_document_processing(self, document_id, stage, status, duration, user_id):
        """Log document processing event."""
        log_data = {
            "event_type": "document_processing",
            "document_id": document_id,
            "stage": stage,
            "status": status,
            "duration": duration,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))
    
    def log_rag_query(self, query_id, user_id, query_type, status, duration, chunks_retrieved):
        """Log RAG query event."""
        log_data = {
            "event_type": "rag_query",
            "query_id": query_id,
            "user_id": user_id,
            "query_type": query_type,
            "status": status,
            "duration": duration,
            "chunks_retrieved": chunks_retrieved,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))
    
    def log_chat_message(self, message_id, user_id, message_type, status, duration, quality_score):
        """Log chat message event."""
        log_data = {
            "event_type": "chat_message",
            "message_id": message_id,
            "user_id": user_id,
            "message_type": message_type,
            "status": status,
            "duration": duration,
            "quality_score": quality_score,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))
```

#### **Log Configuration**
```yaml
# logging/logging.yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  json:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    class: 'pythonjsonlogger.jsonlogger.JsonFormatter'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: /var/log/agents-integration/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: json
    filename: /var/log/agents-integration/error.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  upload_pipeline:
    level: INFO
    handlers: [console, file, error_file]
    propagate: false
  
  rag_service:
    level: INFO
    handlers: [console, file, error_file]
    propagate: false
  
  agent_api:
    level: INFO
    handlers: [console, file, error_file]
    propagate: false

root:
  level: INFO
  handlers: [console, file, error_file]
```

### **2. Log Collection**

#### **Fluentd Configuration**
```yaml
# logging/fluentd.conf
<source>
  @type tail
  path /var/log/agents-integration/*.log
  pos_file /var/log/fluentd/agents-integration.log.pos
  tag agents-integration.*
  format json
  time_key timestamp
  time_format %Y-%m-%dT%H:%M:%S.%LZ
</source>

<filter agents-integration.**>
  @type record_transformer
  <record>
    service_name ${tag_parts[1]}
    log_level ${record["levelname"]}
  </record>
</filter>

<match agents-integration.**>
  @type elasticsearch
  host elasticsearch.monitoring.svc.cluster.local
  port 9200
  index_name agents-integration
  type_name _doc
  <buffer>
    @type file
    path /var/log/fluentd/buffers/agents-integration
    flush_mode interval
    flush_interval 5s
  </buffer>
</match>
```

---

## Distributed Tracing

### **1. OpenTelemetry Configuration**

#### **Tracing Setup**
```python
# tracing/tracing_setup.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

def setup_tracing(service_name, jaeger_endpoint):
    """Set up distributed tracing."""
    # Create tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger-agent.monitoring.svc.cluster.local",
        agent_port=14268,
    )
    
    # Create span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrument libraries
    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor().instrument()
    Psycopg2Instrumentor().instrument()
    
    return tracer

def create_span(tracer, operation_name, attributes=None):
    """Create a span for an operation."""
    span = tracer.start_span(operation_name)
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    return span
```

#### **Tracing Usage**
```python
# tracing/traced_operations.py
from tracing.tracing_setup import create_span

async def traced_document_upload(user_id, document_data):
    """Document upload with tracing."""
    with create_span("document_upload", {"user_id": user_id}) as span:
        # Upload document
        upload_result = await upload_document(document_data)
        span.set_attribute("document_id", upload_result["document_id"])
        span.set_attribute("file_size", document_data["file_size"])
        
        # Process document
        with create_span("document_processing", {"document_id": upload_result["document_id"]}) as processing_span:
            processing_result = await process_document(upload_result["document_id"])
            processing_span.set_attribute("processing_stage", processing_result["stage"])
            processing_span.set_attribute("processing_status", processing_result["status"])
        
        return upload_result

async def traced_rag_query(user_id, query):
    """RAG query with tracing."""
    with create_span("rag_query", {"user_id": user_id, "query": query}) as span:
        # Retrieve chunks
        with create_span("chunk_retrieval", {"user_id": user_id}) as retrieval_span:
            chunks = await retrieve_chunks(user_id, query)
            retrieval_span.set_attribute("chunks_retrieved", len(chunks))
        
        # Generate response
        with create_span("response_generation", {"user_id": user_id}) as response_span:
            response = await generate_response(query, chunks)
            response_span.set_attribute("response_length", len(response))
            response_span.set_attribute("quality_score", response.get("quality_score", 0))
        
        return response
```

---

## Monitoring Deployment

### **1. Kubernetes Monitoring Stack**

#### **Prometheus Deployment**
```yaml
# monitoring/prometheus-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: storage
          mountPath: /prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: storage
        persistentVolumeClaim:
          claimName: prometheus-storage
```

#### **Grafana Deployment**
```yaml
# monitoring/grafana-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-secrets
              key: admin-password
        volumeMounts:
        - name: storage
          mountPath: /var/lib/grafana
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: grafana-storage
```

### **2. Monitoring Configuration**

#### **Service Monitor**
```yaml
# monitoring/service-monitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: agents-integration
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: agents-integration
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

---

## Success Criteria

### **1. Monitoring Coverage**
- [ ] **Service Health**: 100% service monitoring coverage
- [ ] **Performance Metrics**: All performance metrics tracked
- [ ] **Business Metrics**: All business metrics tracked
- [ ] **Error Tracking**: All errors tracked and alerted
- [ ] **User Activity**: All user activity tracked

### **2. Alerting Effectiveness**
- [ ] **Critical Alerts**: 100% critical issue detection
- [ ] **Alert Response**: < 5 minutes for critical alerts
- [ ] **False Positives**: < 5% false positive rate
- [ ] **Alert Resolution**: < 30 minutes for critical issues
- [ ] **Escalation**: Proper escalation procedures

### **3. Dashboard Usability**
- [ ] **System Overview**: Clear system health overview
- [ ] **Service Details**: Detailed service monitoring
- [ ] **Business Insights**: Business metrics visualization
- [ ] **Troubleshooting**: Effective troubleshooting tools
- [ ] **Performance Analysis**: Performance trend analysis

---

## Conclusion

This comprehensive monitoring and observability setup ensures that Phase 3 deployment maintains **high visibility** into system health, performance, and user experience while building on the **successful Phase 2 RAG system** and integrating the **upload pipeline** for complete document-to-chat functionality.

### **Key Benefits**
- **Complete Visibility**: Monitor all aspects of the system
- **Proactive Alerting**: Early detection of issues
- **Performance Tracking**: Maintain performance standards
- **Quality Assurance**: Monitor response quality and user satisfaction
- **Business Insights**: Track user activity and document processing

The monitoring setup provides the foundation for reliable production operation while ensuring the system meets all quality and performance standards established in Phase 2.

---

**Monitoring Setup Status**: 📋 **SETUP COMPLETE**  
**Implementation**: 📋 **READY FOR DEPLOYMENT**  
**Coverage**: Comprehensive monitoring across all system components  
**Quality Assurance**: Maintains Phase 2 quality standards

---

**Document Version**: 1.0  
**Last Updated**: January 7, 2025  
**Author**: AI Assistant  
**Setup Status**: 📋 **COMPLETE**
