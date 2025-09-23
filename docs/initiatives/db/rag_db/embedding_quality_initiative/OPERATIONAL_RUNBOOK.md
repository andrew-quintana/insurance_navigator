# Operational Runbook - Embedding Quality Monitoring

## Overview

This runbook provides step-by-step procedures for operating and maintaining the Embedding Quality Monitoring system, including incident response, routine maintenance, and troubleshooting.

## Quick Reference

### Critical Error Codes

| Error Code | Severity | Immediate Action |
|------------|----------|------------------|
| `ZERO_EMBEDDING_DETECTED` | Critical | Stop processing, investigate API |
| `MOSTLY_ZERO_EMBEDDING_DETECTED` | Critical | Stop processing, check API health |
| `INVALID_EMBEDDING_DIMENSIONS` | Critical | Check model configuration |
| `NAN_VALUE_DETECTED` | Critical | Investigate input data quality |
| `INFINITE_VALUE_DETECTED` | Critical | Investigate input data quality |

### Emergency Contacts

- **On-Call Engineer**: Check current rotation
- **System Owner**: Database/RAG team lead
- **Escalation**: Engineering manager

## Incident Response Procedures

### 1. Zero Embedding Alert

**Alert**: `ZERO_EMBEDDING_DETECTED` or `MOSTLY_ZERO_EMBEDDING_DETECTED`

**Severity**: Critical (P1)

**Immediate Response (5 minutes)**:

1. **Check System Status**:
   ```bash
   # Check if embeddings are being generated
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/embeddings \
        -d '{"model": "text-embedding-3-small", "input": "test"}'
   
   # Check recent logs for API errors
   kubectl logs -l app=worker --since=10m | grep -i "embedding\|openai"
   ```

2. **Verify API Key**:
   ```bash
   # Check API key status
   echo $OPENAI_API_KEY | wc -c  # Should be ~51 characters
   
   # Test API key validity
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

3. **Check Rate Limiting**:
   ```bash
   # Look for rate limit errors in logs
   kubectl logs -l app=worker --since=30m | grep -i "rate.limit\|429\|quota"
   ```

**Investigation (15 minutes)**:

1. **Review Error Context**:
   - Check correlation ID in logs
   - Identify affected user/document
   - Review input text that caused the issue

2. **Check System Dependencies**:
   ```bash
   # Database connectivity
   kubectl exec -it postgres-pod -- psql -c "SELECT 1;"
   
   # Network connectivity to OpenAI
   kubectl exec -it worker-pod -- curl -I https://api.openai.com
   ```

3. **Review Recent Changes**:
   - Check recent deployments
   - Review configuration changes
   - Verify environment variables

**Resolution Actions**:

1. **If API Key Issues**:
   ```bash
   # Update API key in secrets
   kubectl create secret generic openai-secret \
     --from-literal=api-key=$NEW_OPENAI_API_KEY \
     --dry-run=client -o yaml | kubectl apply -f -
   
   # Restart workers to pick up new key
   kubectl rollout restart deployment/worker
   ```

2. **If Rate Limiting**:
   ```bash
   # Scale down workers temporarily
   kubectl scale deployment/worker --replicas=2
   
   # Monitor rate limit recovery
   # Scale back up after 10 minutes
   kubectl scale deployment/worker --replicas=5
   ```

3. **If Input Data Issues**:
   - Identify problematic input text
   - Check for empty strings, special characters
   - Review document preprocessing pipeline

### 2. High Error Rate Alert

**Alert**: `BATCH_HIGH_CRITICAL_RATE` or `BATCH_LOW_QUALITY_SCORE`

**Severity**: High (P2)

**Response Procedure**:

1. **Assess Impact**:
   ```bash
   # Check current error rates
   kubectl logs -l app=worker --since=1h | \
     grep "EMBEDDING_VALIDATION_FAILED" | wc -l
   
   # Check recent processing success rate
   kubectl logs -l app=worker --since=1h | \
     grep "embeddings_stored" | wc -l
   ```

2. **Identify Pattern**:
   ```bash
   # Group errors by type
   kubectl logs -l app=worker --since=1h | \
     grep "EMBEDDING_VALIDATION_FAILED" | \
     cut -d: -f2 | sort | uniq -c
   
   # Check if errors are user-specific
   kubectl logs -l app=worker --since=1h | \
     grep "user_id" | cut -d'"' -f4 | sort | uniq -c
   ```

3. **Mitigate Impact**:
   - Consider temporary threshold adjustments
   - Route problematic users to fallback processing
   - Enable enhanced logging for investigation

### 3. Performance Degradation

**Alert**: Slow embedding processing, timeouts

**Response Procedure**:

1. **Check System Resources**:
   ```bash
   # CPU and memory usage
   kubectl top nodes
   kubectl top pods -l app=worker
   
   # Check database performance
   kubectl exec -it postgres-pod -- psql -c "\
     SELECT query, calls, mean_exec_time \
     FROM pg_stat_statements \
     WHERE query LIKE '%embedding%' \
     ORDER BY mean_exec_time DESC LIMIT 5;"
   ```

2. **Review Validation Overhead**:
   ```bash
   # Check validation timing logs
   kubectl logs -l app=worker --since=30m | \
     grep "validation_time" | \
     awk '{print $NF}' | \
     sort -n
   ```

3. **Optimization Actions**:
   - Adjust batch sizes if needed
   - Consider disabling non-critical validation temporarily
   - Scale up worker instances

## Routine Maintenance

### Daily Tasks

1. **Review Quality Metrics**:
   ```bash
   # Get daily quality summary
   kubectl exec -it worker-pod -- python3 -c "
   from backend.shared.monitoring.embedding_monitor import EmbeddingQualityMonitor
   monitor = EmbeddingQualityMonitor()
   metrics = monitor.get_metrics_summary()
   print(f'Quality Score: {metrics[\"quality_score\"]}')
   print(f'Total Processed: {metrics[\"total_processed\"]}')
   print(f'Zero Embeddings: {metrics[\"zero_count\"]}')
   "
   ```

2. **Check Alert Volume**:
   ```bash
   # Count alerts in last 24 hours
   kubectl logs -l app=worker --since=24h | \
     grep "EMBEDDING_ALERT" | wc -l
   
   # Group alerts by type
   kubectl logs -l app=worker --since=24h | \
     grep "EMBEDDING_ALERT" | \
     cut -d: -f2 | sort | uniq -c
   ```

3. **Review Error Trends**:
   ```bash
   # Check if any new error patterns emerged
   kubectl logs -l app=worker --since=24h | \
     grep "EMBEDDING_VALIDATION_FAILED" | \
     tail -10
   ```

### Weekly Tasks

1. **Threshold Review**:
   - Analyze false positive rates
   - Review missed critical issues
   - Adjust thresholds if needed

2. **Performance Analysis**:
   - Review validation overhead trends
   - Check processing latency
   - Optimize if degradation detected

3. **Alert Tuning**:
   - Review alert frequency
   - Adjust cooldown periods if needed
   - Update alert recipients

### Monthly Tasks

1. **Comprehensive Health Check**:
   ```bash
   # Run full validation test suite
   kubectl exec -it worker-pod -- python3 -m pytest \
     tests/embedding_validation/ -v
   ```

2. **Documentation Updates**:
   - Update runbook based on incidents
   - Review and update thresholds documentation
   - Update contact information

3. **Capacity Planning**:
   - Review resource usage trends
   - Plan for scaling if needed
   - Update monitoring dashboards

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Quality Metrics**:
   - Overall quality score
   - Zero embedding rate
   - Critical issue rate
   - Validation success rate

2. **Performance Metrics**:
   - Validation latency
   - Processing throughput
   - Resource utilization
   - Error rates

3. **Operational Metrics**:
   - Alert frequency
   - Incident response time
   - System availability
   - API quota usage

### Dashboard Setup

```yaml
# Example Grafana dashboard config
apiVersion: v1
kind: ConfigMap
metadata:
  name: embedding-quality-dashboard
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "Embedding Quality Monitoring",
        "panels": [
          {
            "title": "Quality Score",
            "type": "stat",
            "targets": [
              {
                "expr": "embedding_quality_score",
                "legendFormat": "Quality Score"
              }
            ]
          },
          {
            "title": "Error Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(embedding_validation_errors_total[5m])",
                "legendFormat": "Error Rate"
              }
            ]
          }
        ]
      }
    }
```

### Alert Rules

```yaml
# Example alert rules
groups:
  - name: embedding_quality
    rules:
      - alert: ZeroEmbeddingDetected
        expr: increase(embedding_zero_errors_total[5m]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Zero embedding detected"
          description: "Zero embeddings detected in the last 5 minutes"
      
      - alert: HighEmbeddingErrorRate
        expr: rate(embedding_validation_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High embedding error rate"
          description: "Embedding error rate is above 10% for 5 minutes"
      
      - alert: LowQualityScore
        expr: embedding_quality_score < 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low embedding quality score"
          description: "Embedding quality score is below 0.8"
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: False Positive Alerts

**Symptoms**: Valid embeddings flagged as problematic

**Investigation**:
```bash
# Check recent validation results
kubectl logs -l app=worker --since=1h | \
  grep "validation_metrics" | \
  tail -5 | \
  jq '.validation_metrics'

# Check if thresholds are too strict
kubectl exec -it worker-pod -- python3 -c "
from backend.shared.validation.embedding_validator import EmbeddingValidator
validator = EmbeddingValidator()
print('Current thresholds:', validator.thresholds)
"
```

**Solution**:
1. Adjust thresholds based on analysis
2. Update validation logic if needed
3. Review input data patterns

#### Issue: Missed Critical Issues

**Symptoms**: Zero embeddings not detected

**Investigation**:
```bash
# Check if validation is enabled
kubectl get configmap worker-config -o yaml | \
  grep EMBEDDING_VALIDATION_ENABLED

# Check for import errors
kubectl logs -l app=worker --since=1h | \
  grep "validation modules not found"

# Manually test validation
kubectl exec -it worker-pod -- python3 -c "
from backend.shared.validation.embedding_validator import EmbeddingValidator
validator = EmbeddingValidator()
result = validator.validate_embedding([0.0] * 1536)
print('Zero embedding detected:', result.issue_type)
"
```

**Solution**:
1. Ensure validation modules are properly installed
2. Check import paths and dependencies
3. Verify fallback validation is working

#### Issue: Performance Impact

**Symptoms**: Slow embedding processing

**Investigation**:
```bash
# Profile validation performance
kubectl exec -it worker-pod -- python3 -c "
import time
from backend.shared.validation.embedding_validator import EmbeddingValidator
import numpy as np

validator = EmbeddingValidator()
embeddings = [np.random.normal(0, 0.1, 1536).tolist() for _ in range(100)]

start_time = time.time()
for embedding in embeddings:
    validator.validate_embedding(embedding)
end_time = time.time()

print(f'Validation time per embedding: {(end_time - start_time) / 100 * 1000:.2f}ms')
"
```

**Solution**:
1. Optimize validation logic if needed
2. Adjust batch sizes
3. Consider async validation for large batches

### Debugging Commands

#### Check Current System State

```bash
# Overall system health
kubectl get pods -l app=worker
kubectl top pods -l app=worker

# Recent error summary
kubectl logs -l app=worker --since=1h | \
  grep -E "(ERROR|CRITICAL)" | \
  tail -10

# Database connection status
kubectl exec -it worker-pod -- python3 -c "
import asyncio
from core.database import DatabaseManager, create_database_config

async def test_db():
    db_config = create_database_config()
    db = DatabaseManager(db_config)
    await db.initialize()
    print('Database connection: OK')
    await db.close()

asyncio.run(test_db())
"
```

#### Test Validation Components

```bash
# Test validator directly
kubectl exec -it worker-pod -- python3 -c "
from backend.shared.validation.embedding_validator import EmbeddingValidator

validator = EmbeddingValidator()

# Test with zero embedding
result = validator.validate_embedding([0.0] * 1536)
print(f'Zero embedding test: {result.issue_type.value}')

# Test with valid embedding
import numpy as np
valid_embedding = np.random.normal(0, 0.1, 1536).tolist()
result = validator.validate_embedding(valid_embedding)
print(f'Valid embedding test: {result.issue_type.value}')
"

# Test monitor functionality
kubectl exec -it worker-pod -- python3 -c "
from backend.shared.monitoring.embedding_monitor import EmbeddingQualityMonitor

monitor = EmbeddingQualityMonitor()
metrics = monitor.get_metrics_summary()
print('Current metrics:', metrics)

recent_issues = monitor.get_recent_issues(limit=3)
print('Recent issues:', len(recent_issues))
"
```

#### Manual Quality Check

```bash
# Check random embeddings from database
kubectl exec -it postgres-pod -- psql -c "
SELECT 
    chunk_id,
    LENGTH(embedding) as embedding_length,
    CASE 
        WHEN embedding = '[' || REPEAT('0,', 1535) || '0]' THEN 'ALL_ZEROS'
        ELSE 'NOT_ZERO'
    END as quality_check
FROM upload_pipeline.document_chunks 
WHERE embedding IS NOT NULL 
ORDER BY updated_at DESC 
LIMIT 10;
"
```

## Configuration Management

### Environment Variables

```bash
# Production configuration
export EMBEDDING_VALIDATION_ENABLED=true
export EMBEDDING_MONITORING_ENABLED=true
export EMBEDDING_ALERTS_ENABLED=true

# Threshold configuration
export EMBEDDING_ZERO_TOLERANCE=1e-10
export EMBEDDING_MOSTLY_ZEROS_THRESHOLD=0.95
export EMBEDDING_EXTREME_VALUE_THRESHOLD=10.0

# Alert configuration
export EMBEDDING_ALERT_CRITICAL_THRESHOLD=0.05
export EMBEDDING_ALERT_QUALITY_THRESHOLD=0.8
export EMBEDDING_ALERT_COOLDOWN_MINUTES=5
```

### Configuration Updates

```bash
# Update configuration
kubectl create configmap worker-config \
  --from-env-file=worker.env \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart workers to pick up new config
kubectl rollout restart deployment/worker

# Verify configuration
kubectl exec -it worker-pod -- env | grep EMBEDDING_
```

## Emergency Procedures

### Complete System Failure

1. **Immediate Actions**:
   - Switch to fallback validation mode
   - Disable strict validation temporarily
   - Alert engineering team

2. **Fallback Configuration**:
   ```bash
   # Disable enhanced validation
   kubectl patch configmap worker-config -p \
     '{"data":{"EMBEDDING_VALIDATION_ENABLED":"false"}}'
   
   # Restart workers
   kubectl rollout restart deployment/worker
   ```

3. **Recovery Steps**:
   - Identify root cause
   - Fix underlying issue
   - Re-enable validation gradually
   - Monitor for stability

### Data Corruption Detection

1. **If zero embeddings found in database**:
   ```sql
   -- Find affected chunks
   SELECT chunk_id, document_id, updated_at
   FROM upload_pipeline.document_chunks
   WHERE embedding = '[' || REPEAT('0,', 1535) || '0]'
   ORDER BY updated_at DESC;
   
   -- Count total affected
   SELECT COUNT(*) as zero_embedding_count
   FROM upload_pipeline.document_chunks
   WHERE embedding = '[' || REPEAT('0,', 1535) || '0]';
   ```

2. **Recovery Actions**:
   - Identify affected documents
   - Re-queue for embedding generation
   - Monitor re-processing
   - Verify quality of new embeddings

## Contact Information

### Escalation Path

1. **Level 1**: On-call engineer (immediate response)
2. **Level 2**: System owner/Database team lead
3. **Level 3**: Engineering manager
4. **Level 4**: VP of Engineering

### External Dependencies

- **OpenAI Support**: For API-related issues
- **Cloud Provider**: For infrastructure issues
- **Database Vendor**: For database-specific problems

### Communication Channels

- **Incident Channel**: #incidents-embedding-quality
- **Team Channel**: #db-rag-team
- **Status Page**: Update system status as needed