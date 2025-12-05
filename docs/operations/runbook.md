# Auto-SEO Operations Runbook

## Table of Contents

1. [Overview](#overview)
2. [Service Health Checks](#service-health-checks)
3. [Common Operations](#common-operations)
4. [Incident Response](#incident-response)
5. [Backup & Recovery](#backup--recovery)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Troubleshooting Guide](#troubleshooting-guide)

## Overview

This runbook provides operational procedures for maintaining the Auto-SEO platform.

### Service Architecture

| Service | Port | Health Endpoint | Critical |
|---------|------|-----------------|----------|
| API Gateway | 8000 | /health | Yes |
| Auth Service | 8001 | /health | Yes |
| Content Generator | 8002 | /health | Yes |
| SEO Scorer | 8003 | /health | No |
| Keyword Ingestion | 8004 | /health | No |
| Analytics | 8005 | /health | No |
| Notification | 8006 | /health | No |

### Key Dependencies

- PostgreSQL: Primary database
- Redis: Caching and sessions
- RabbitMQ: Message queue
- ClickHouse: Analytics database
- MinIO: Object storage

## Service Health Checks

### Quick Health Check

```bash
# Check all services
for svc in api-gateway auth-service content-generator seo-scorer; do
  echo "Checking $svc..."
  kubectl exec -it deploy/$svc -n autoseo-prod -- curl -s localhost:8000/health
done
```

### Database Health

```bash
# PostgreSQL
kubectl exec -it statefulset/postgres -n autoseo-prod -- \
  pg_isready -U autoseo -d autoseo

# Redis
kubectl exec -it statefulset/redis-master -n autoseo-prod -- \
  redis-cli ping

# ClickHouse
kubectl exec -it statefulset/clickhouse -n autoseo-prod -- \
  clickhouse-client --query "SELECT 1"
```

### RabbitMQ Health

```bash
kubectl exec -it statefulset/rabbitmq -n autoseo-prod -- \
  rabbitmqctl status
```

## Common Operations

### Restart a Service

```bash
# Restart deployment
kubectl rollout restart deployment/api-gateway -n autoseo-prod

# Wait for completion
kubectl rollout status deployment/api-gateway -n autoseo-prod
```

### Scale a Service

```bash
# Scale up
kubectl scale deployment/api-gateway --replicas=5 -n autoseo-prod

# Scale down
kubectl scale deployment/api-gateway --replicas=2 -n autoseo-prod
```

### View Logs

```bash
# Current logs
kubectl logs -f deployment/api-gateway -n autoseo-prod

# Previous container logs
kubectl logs deployment/api-gateway -n autoseo-prod --previous

# Logs from all pods
kubectl logs -l app=api-gateway -n autoseo-prod --all-containers
```

### Run Database Migration

```bash
# Create migration job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-$(date +%s)
  namespace: autoseo-prod
spec:
  template:
    spec:
      containers:
      - name: migration
        image: your-registry/auth-service:latest
        command: ["alembic", "upgrade", "head"]
        envFrom:
        - secretRef:
            name: auto-seo-secrets
      restartPolicy: Never
  backoffLimit: 3
EOF

# Check status
kubectl get jobs -n autoseo-prod
```

### Clear Cache

```bash
# Clear all Redis keys (use with caution)
kubectl exec -it statefulset/redis-master -n autoseo-prod -- \
  redis-cli FLUSHALL

# Clear specific pattern
kubectl exec -it statefulset/redis-master -n autoseo-prod -- \
  redis-cli KEYS "session:*" | xargs redis-cli DEL
```

## Incident Response

### Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| P1 | Critical | 15 minutes | Full outage, data loss |
| P2 | High | 1 hour | Major feature broken |
| P3 | Medium | 4 hours | Minor feature broken |
| P4 | Low | 24 hours | Cosmetic issues |

### P1 Incident Checklist

1. [ ] Acknowledge incident
2. [ ] Notify stakeholders
3. [ ] Gather initial information
4. [ ] Identify affected services
5. [ ] Implement mitigation
6. [ ] Root cause analysis
7. [ ] Post-incident review

### Service Outage Recovery

```bash
# 1. Check pod status
kubectl get pods -n autoseo-prod

# 2. Check events
kubectl get events -n autoseo-prod --sort-by='.lastTimestamp'

# 3. Check node health
kubectl get nodes
kubectl top nodes

# 4. Force restart if needed
kubectl delete pod -l app=api-gateway -n autoseo-prod

# 5. Verify recovery
kubectl rollout status deployment/api-gateway -n autoseo-prod
```

### Database Recovery

```bash
# Check PostgreSQL status
kubectl exec -it postgres-0 -n autoseo-prod -- pg_isready

# If not ready, check logs
kubectl logs postgres-0 -n autoseo-prod

# Force failover (if using replication)
kubectl exec -it postgres-0 -n autoseo-prod -- patronictl failover
```

## Backup & Recovery

### Database Backup

```bash
# Create backup
kubectl exec -it postgres-0 -n autoseo-prod -- \
  pg_dump -U autoseo autoseo | gzip > backup_$(date +%Y%m%d).sql.gz

# Upload to S3 (example)
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://autoseo-backups/postgres/
```

### Scheduled Backup (CronJob)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: autoseo-prod
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h postgres -U autoseo autoseo | gzip | \
              aws s3 cp - s3://autoseo-backups/postgres/backup_$(date +%Y%m%d).sql.gz
            envFrom:
            - secretRef:
                name: auto-seo-secrets
          restartPolicy: OnFailure
```

### Restore from Backup

```bash
# Download backup
aws s3 cp s3://autoseo-backups/postgres/backup_YYYYMMDD.sql.gz .

# Restore
gunzip -c backup_YYYYMMDD.sql.gz | \
  kubectl exec -i postgres-0 -n autoseo-prod -- psql -U autoseo autoseo
```

### Disaster Recovery

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 1 hour

Recovery Steps:

1. Identify failure scope
2. Provision replacement infrastructure
3. Restore latest backup
4. Apply configuration
5. Verify data integrity
6. Update DNS/routing
7. Validate functionality

## Monitoring & Alerting

### Grafana Dashboards

| Dashboard | Purpose |
|-----------|---------|
| System Overview | High-level metrics |
| API Performance | Request latency, errors |
| Database Metrics | Query performance |
| Content Generation | Article generation stats |
| Resource Usage | CPU, Memory, Disk |

### Key Metrics to Monitor

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 80% | > 95% |
| Disk Usage | > 70% | > 90% |
| Error Rate | > 1% | > 5% |
| p95 Latency | > 500ms | > 1000ms |
| Queue Depth | > 1000 | > 5000 |

### Alert Configuration

```yaml
# Example Prometheus alert rules
groups:
  - name: autoseo
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          
      - alert: ServiceDown
        expr: up{job="api-gateway"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: API Gateway is down
```

### Viewing Metrics

```bash
# Port forward Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n autoseo-prod

# Port forward Grafana
kubectl port-forward svc/grafana 3000:3000 -n autoseo-prod
```

## Troubleshooting Guide

### High CPU Usage

1. Identify pod with high CPU:
   ```bash
   kubectl top pods -n autoseo-prod
   ```

2. Check for runaway processes:
   ```bash
   kubectl exec -it <pod> -n autoseo-prod -- top
   ```

3. Scale up if legitimate load:
   ```bash
   kubectl scale deployment/<service> --replicas=3 -n autoseo-prod
   ```

### High Memory Usage

1. Check memory usage:
   ```bash
   kubectl top pods -n autoseo-prod
   ```

2. Check for memory leaks (trending up over time)

3. Restart pod if OOM:
   ```bash
   kubectl delete pod <pod-name> -n autoseo-prod
   ```

### Database Connection Issues

1. Check connection count:
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```

2. Kill long-running queries:
   ```sql
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE state = 'active' AND now() - query_start > interval '5 minutes';
   ```

3. Check connection pool settings

### Queue Buildup

1. Check queue depth:
   ```bash
   kubectl exec -it rabbitmq-0 -n autoseo-prod -- \
     rabbitmqctl list_queues
   ```

2. Scale consumers:
   ```bash
   kubectl scale deployment/content-generator --replicas=5 -n autoseo-prod
   ```

3. Check for failed messages

### Slow API Responses

1. Check endpoint latency in Grafana
2. Review slow query log
3. Check external service health (OpenAI, etc.)
4. Check resource utilization
5. Review recent deployments

## Contact Information

| Role | Contact | Escalation |
|------|---------|------------|
| On-Call Engineer | PagerDuty | Primary |
| DevOps Lead | [email] | Secondary |
| Engineering Manager | [email] | Escalation |

## Appendix

### Useful Commands

```bash
# Get all resources in namespace
kubectl get all -n autoseo-prod

# Describe resource
kubectl describe deployment/api-gateway -n autoseo-prod

# Execute command in pod
kubectl exec -it <pod> -n autoseo-prod -- /bin/sh

# Copy files
kubectl cp <pod>:/path/file ./local-file -n autoseo-prod

# Port forward
kubectl port-forward svc/api-gateway 8000:8000 -n autoseo-prod
```

### Environment Variables

See `docs/deployment/production-guide.md` for full list.
