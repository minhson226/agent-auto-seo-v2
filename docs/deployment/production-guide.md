# Production Deployment Guide

This guide covers deploying Auto-SEO to a production Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.27+)
- Helm 3.x
- kubectl configured with cluster access
- Domain with SSL certificate
- External PostgreSQL, Redis (or use in-cluster deployments)
- Container registry access

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Ingress                                │
│                    (nginx-ingress/traefik)                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
         ┌──────────┐    ┌──────────┐    ┌──────────┐
         │ Frontend │    │   API    │    │ Grafana  │
         │Dashboard │    │ Gateway  │    │          │
         └──────────┘    └──────────┘    └──────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
     ┌────────────┐      ┌────────────┐      ┌────────────┐
     │    Auth    │      │  Content   │      │    SEO     │
     │  Service   │      │ Generator  │      │   Scorer   │
     └────────────┘      └────────────┘      └────────────┘
            │                   │                   │
            └───────────────────┴───────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
     ┌────────────┐      ┌────────────┐      ┌────────────┐
     │ PostgreSQL │      │   Redis    │      │ClickHouse │
     └────────────┘      └────────────┘      └────────────┘
```

## Step-by-Step Deployment

### 1. Setup Secrets

Create secrets for sensitive configuration:

```bash
# Create namespace first
kubectl create namespace autoseo-prod

# Create secrets
kubectl create secret generic auto-seo-secrets -n autoseo-prod \
  --from-literal=jwt-secret=$(openssl rand -base64 32) \
  --from-literal=db-password=$(openssl rand -base64 16) \
  --from-literal=redis-password=$(openssl rand -base64 16) \
  --from-literal=openai-api-key=sk-your-api-key-here \
  --from-literal=encryption-key=$(openssl rand -base64 32)

# For external databases, create connection strings
kubectl create secret generic db-credentials -n autoseo-prod \
  --from-literal=postgres-url='postgresql://user:pass@host:5432/autoseo' \
  --from-literal=redis-url='redis://:pass@host:6379/0' \
  --from-literal=clickhouse-url='http://user:pass@host:8123'
```

### 2. Deploy Databases (If Using In-Cluster)

For production, we recommend managed database services. If deploying in-cluster:

```bash
# PostgreSQL
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgresql bitnami/postgresql \
  --namespace autoseo-prod \
  --set auth.postgresPassword=$POSTGRES_PASSWORD \
  --set auth.database=autoseo \
  --set persistence.size=100Gi \
  --set primary.resources.requests.memory=2Gi \
  --set primary.resources.requests.cpu=1000m

# Redis
helm install redis bitnami/redis \
  --namespace autoseo-prod \
  --set auth.password=$REDIS_PASSWORD \
  --set replica.replicaCount=2 \
  --set master.persistence.size=10Gi

# RabbitMQ
helm install rabbitmq bitnami/rabbitmq \
  --namespace autoseo-prod \
  --set auth.username=autoseo \
  --set auth.password=$RABBITMQ_PASSWORD \
  --set persistence.size=20Gi
```

### 3. Deploy Application Services

Apply Kubernetes manifests:

```bash
# Apply ConfigMaps
kubectl apply -f k8s/configmaps/ -n autoseo-prod

# Apply Services
kubectl apply -f k8s/services/ -n autoseo-prod

# Wait for deployments to be ready
kubectl rollout status deployment/api-gateway -n autoseo-prod
kubectl rollout status deployment/auth-service -n autoseo-prod
kubectl rollout status deployment/content-generator -n autoseo-prod
```

### 4. Deploy Frontend

```bash
# Build frontend image
cd frontend/dashboard
docker build -t your-registry/autoseo-dashboard:latest .
docker push your-registry/autoseo-dashboard:latest

# Deploy
kubectl apply -f k8s/frontend/ -n autoseo-prod
```

### 5. Configure Ingress

Create Ingress resource with TLS:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: autoseo-ingress
  namespace: autoseo-prod
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
spec:
  tls:
    - hosts:
        - app.autoseo.com
        - api.autoseo.com
      secretName: autoseo-tls
  rules:
    - host: app.autoseo.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: dashboard
                port:
                  number: 80
    - host: api.autoseo.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-gateway
                port:
                  number: 8000
```

Apply the ingress:

```bash
kubectl apply -f ingress.yaml -n autoseo-prod
```

### 6. Deploy Monitoring

```bash
# Apply monitoring stack
kubectl apply -f k8s/monitoring/ -n autoseo-prod

# Access Grafana
kubectl port-forward svc/grafana 3000:3000 -n autoseo-prod
```

### 7. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n autoseo-prod

# Check services
kubectl get svc -n autoseo-prod

# Check ingress
kubectl get ingress -n autoseo-prod

# View logs
kubectl logs -f deployment/api-gateway -n autoseo-prod

# Test health endpoint
curl https://api.autoseo.com/health
```

## Production Checklist

### Pre-Deployment

- [ ] All secrets configured
- [ ] Database migrations applied
- [ ] SSL certificates ready
- [ ] DNS records configured
- [ ] Backup strategy in place
- [ ] Monitoring dashboards ready

### Post-Deployment

- [ ] All pods running
- [ ] Health endpoints responding
- [ ] Ingress routing correctly
- [ ] SSL working
- [ ] Monitoring receiving metrics
- [ ] Alerts configured
- [ ] Login functionality working
- [ ] API endpoints responding

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: autoseo-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Manual Scaling

```bash
kubectl scale deployment api-gateway --replicas=5 -n autoseo-prod
```

## Rollback Procedure

If deployment fails:

```bash
# Check rollout history
kubectl rollout history deployment/api-gateway -n autoseo-prod

# Rollback to previous version
kubectl rollout undo deployment/api-gateway -n autoseo-prod

# Rollback to specific revision
kubectl rollout undo deployment/api-gateway --to-revision=2 -n autoseo-prod
```

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod for events
kubectl describe pod <pod-name> -n autoseo-prod

# Check logs
kubectl logs <pod-name> -n autoseo-prod --previous
```

### Connection Issues

```bash
# Test internal DNS
kubectl run debug --rm -i --tty --image=busybox -- nslookup api-gateway

# Test connectivity
kubectl run debug --rm -i --tty --image=curlimages/curl -- curl api-gateway:8000/health
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n autoseo-prod

# Check node resources
kubectl top nodes
```

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `JWT_SECRET` | Secret for JWT signing | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `RABBITMQ_URL` | RabbitMQ connection string | Yes |
| `ENCRYPTION_KEY` | Key for encrypting sensitive data | Yes |
| `LOG_LEVEL` | Logging level (INFO/DEBUG/ERROR) | No |
| `ENVIRONMENT` | Environment name (prod/staging) | No |

## Security Considerations

1. **Secrets Management**: Use sealed-secrets or external-secrets operator
2. **Network Policies**: Restrict pod-to-pod communication
3. **RBAC**: Limit service account permissions
4. **Pod Security**: Run as non-root, drop capabilities
5. **Image Security**: Scan images for vulnerabilities

## Next Steps

1. Set up CI/CD pipeline
2. Configure backup automation
3. Set up log aggregation (Loki/ELK)
4. Configure alerting rules
5. Document runbook procedures
