# Kubernetes Deployment Guide

This guide covers deploying Auto-SEO to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.27+)
- kubectl configured with cluster access
- Helm (optional, for advanced deployments)
- Persistent storage class available

## Cluster Requirements

### Minimum Resources (Development)
- 3 nodes with 4 CPU, 8GB RAM each
- 100GB persistent storage

### Recommended Resources (Production)
- 5+ nodes with 8 CPU, 16GB RAM each
- SSD-backed persistent storage
- Load balancer support

## Deployment Steps

### 1. Create Namespaces

```bash
kubectl apply -f k8s/namespaces/namespaces.yaml
```

This creates:
- `autoseo-dev` - Development environment
- `autoseo-staging` - Staging environment
- `autoseo-prod` - Production environment

### 2. Create ConfigMaps and Secrets

```bash
# Apply ConfigMaps
kubectl apply -f k8s/configmaps/configmaps.yaml

# Apply Secrets (update with real values for production!)
kubectl apply -f k8s/secrets/secrets.yaml
```

> **Warning**: Never commit real secrets to Git. Use sealed-secrets or external-secrets in production.

### 3. Deploy Databases

```bash
# PostgreSQL
kubectl apply -f k8s/databases/postgres.yaml

# Redis
kubectl apply -f k8s/databases/redis.yaml

# ClickHouse
kubectl apply -f k8s/databases/clickhouse.yaml

# MinIO
kubectl apply -f k8s/databases/minio.yaml
```

### 4. Verify Database Deployments

```bash
# Check all pods
kubectl get pods -n autoseo-dev

# Check StatefulSets
kubectl get statefulsets -n autoseo-dev

# Check PVCs
kubectl get pvc -n autoseo-dev
```

### 5. Deploy Monitoring

```bash
kubectl apply -f k8s/monitoring/prometheus.yaml
kubectl apply -f k8s/monitoring/grafana.yaml
```

### 6. Access Services

For development, use port-forwarding:

```bash
# PostgreSQL
kubectl port-forward -n autoseo-dev svc/postgres 5432:5432

# Redis
kubectl port-forward -n autoseo-dev svc/redis 6379:6379

# ClickHouse
kubectl port-forward -n autoseo-dev svc/clickhouse 8123:8123

# MinIO
kubectl port-forward -n autoseo-dev svc/minio 9000:9000 9001:9001

# Grafana
kubectl port-forward -n autoseo-dev svc/grafana 3000:3000

# Prometheus
kubectl port-forward -n autoseo-dev svc/prometheus 9090:9090
```

## Production Considerations

### Secret Management

Use one of these approaches for production secrets:

1. **Sealed Secrets**
   ```bash
   # Install sealed-secrets controller
   helm install sealed-secrets sealed-secrets/sealed-secrets
   
   # Seal your secrets
   kubeseal --format yaml < secret.yaml > sealed-secret.yaml
   ```

2. **External Secrets Operator**
   ```bash
   # Install external-secrets
   helm install external-secrets external-secrets/external-secrets
   
   # Configure your secret store (AWS, GCP, Azure, Vault, etc.)
   ```

### Ingress Configuration

Create an Ingress for external access:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: autoseo-ingress
  namespace: autoseo-prod
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - api.autoseo.com
        - grafana.autoseo.com
      secretName: autoseo-tls
  rules:
    - host: api.autoseo.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-gateway
                port:
                  number: 8080
    - host: grafana.autoseo.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: grafana
                port:
                  number: 3000
```

### Resource Limits

All deployments include resource limits. Adjust based on your workload:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### High Availability

For production, increase replicas:

```bash
kubectl scale statefulset postgres -n autoseo-prod --replicas=3
kubectl scale deployment api-gateway -n autoseo-prod --replicas=3
```

### Backup Strategy

Set up regular backups for databases:

```bash
# PostgreSQL backup example
kubectl exec -n autoseo-prod postgres-0 -- pg_dump -U autoseo autoseo > backup.sql

# MinIO backup
mc mirror myminio/autoseo-content backup/autoseo-content
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n autoseo-dev

# Check logs
kubectl logs <pod-name> -n autoseo-dev
```

### Persistent Volume Issues

```bash
# Check PVC status
kubectl get pvc -n autoseo-dev

# Describe PVC for events
kubectl describe pvc <pvc-name> -n autoseo-dev
```

### Service Connectivity

```bash
# Test service DNS resolution
kubectl run test --rm -i --tty --image=busybox -- nslookup postgres.autoseo-dev.svc.cluster.local

# Test connectivity
kubectl run test --rm -i --tty --image=postgres:15-alpine -- psql -h postgres -U autoseo -d autoseo
```

## Cleanup

To remove all Auto-SEO resources:

```bash
# Delete all resources in namespace
kubectl delete namespace autoseo-dev

# Or delete specific resources
kubectl delete -f k8s/monitoring/
kubectl delete -f k8s/databases/
kubectl delete -f k8s/secrets/
kubectl delete -f k8s/configmaps/
kubectl delete -f k8s/namespaces/
```

## Next Steps

1. Set up CI/CD pipeline for automated deployments
2. Configure external-secrets for production
3. Set up Ingress with TLS
4. Configure backup automation
5. Set up alerting in Prometheus/Grafana
