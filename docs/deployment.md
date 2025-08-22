# Deployment Guide

## Overview

This guide covers deployment options for the Universal File Extractor API, from local development to production environments.

## Deployment Options

### 1. Docker Compose (Recommended)

#### Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Testing Environment

```bash
# Start with full monitoring stack
docker-compose -f docker-compose.test.yml up -d

# Access monitoring tools:
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090
# - Jaeger: http://localhost:16686
# - Kibana: http://localhost:5601
```

#### Production Environment

```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Set environment variables
export GRAFANA_PASSWORD=your_secure_password
export GRAFANA_USER=admin
```

### 2. Kubernetes Deployment

#### Prerequisites

- Kubernetes cluster (1.20+)
- Helm 3.x
- kubectl configured

#### Deploy with Helm

```bash
# Add the Helm repository
helm repo add file-extractor https://your-repo.com/charts

# Install the application
helm install file-extractor file-extractor/universal-file-extractor \
  --namespace file-extractor \
  --create-namespace \
  --set redis.enabled=true \
  --set monitoring.enabled=true
```

#### Custom Values

Create `values.yaml`:

```yaml
api:
  replicaCount: 3
  resources:
    limits:
      memory: 2Gi
      cpu: 1000m
    requests:
      memory: 1Gi
      cpu: 500m

worker:
  replicaCount: 5
  resources:
    limits:
      memory: 4Gi
      cpu: 2000m

redis:
  enabled: true
  auth:
    enabled: true
    password: "your-secure-password"

monitoring:
  enabled: true
  grafana:
    adminPassword: "your-secure-password"
```

### 3. Cloud Deployment

#### AWS ECS

```bash
# Build and push Docker image
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-west-2.amazonaws.com

docker build -t universal-file-extractor .
docker tag universal-file-extractor:latest your-account.dkr.ecr.us-west-2.amazonaws.com/universal-file-extractor:latest
docker push your-account.dkr.ecr.us-west-2.amazonaws.com/universal-file-extractor:latest

# Deploy with ECS
aws ecs create-service \
  --cluster your-cluster \
  --service-name file-extractor \
  --task-definition file-extractor:1 \
  --desired-count 3
```

#### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/your-project/universal-file-extractor

gcloud run deploy universal-file-extractor \
  --image gcr.io/your-project/universal-file-extractor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

#### Azure Container Instances

```bash
# Deploy to Azure
az container create \
  --resource-group your-rg \
  --name file-extractor \
  --image your-registry.azurecr.io/universal-file-extractor:latest \
  --dns-name-label file-extractor \
  --ports 8000 \
  --memory 2 \
  --cpu 2
```

## Environment Configuration

### Production Environment Variables

```bash
# API Configuration
DEBUG=false
LOG_LEVEL=WARNING
MAX_FILE_SIZE=157286400
ENABLE_ASYNC_PROCESSING=true

# Redis Configuration
REDIS_URL=redis://your-redis-host:6379
REDIS_PASSWORD=your-secure-password

# Worker Configuration
MAX_CONCURRENT_EXTRACTIONS=20
WORKER_PROCESSES=8

# Monitoring
ENABLE_OPENTELEMETRY=true
JAEGER_HOST=your-jaeger-host
JAEGER_PORT=6831
PROMETHEUS_ENABLED=true

# Security
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
CORS_ORIGINS=https://your-frontend.com
```

### SSL/TLS Configuration

#### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring and Observability

### Prometheus Metrics

The API exposes metrics at `/metrics`:

```bash
# Scrape metrics
curl http://localhost:8000/metrics
```

### Grafana Dashboards

Import the provided dashboards:

1. **API Overview**: Request rate, response times, error rates
2. **Extraction Metrics**: Success rate, processing time, file types
3. **System Resources**: CPU, memory, disk usage
4. **Queue Monitoring**: Job queue length, worker status

### Log Aggregation

#### ELK Stack Configuration

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  paths:
    - /var/log/app/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "file-extractor-%{+yyyy.MM.dd}"
```

## Security Considerations

### Container Security

```dockerfile
# Use non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# Read-only filesystem
RUN --mount=type=tmpfs,target=/tmp
```

### Network Security

```yaml
# docker-compose.prod.yml
services:
  api:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

### Secrets Management

```bash
# Use Docker secrets
echo "your-secret-password" | docker secret create redis_password -

# Or use environment files
docker-compose --env-file .env.prod up -d
```

## Scaling Strategies

### Horizontal Scaling

```bash
# Scale API instances
docker-compose up -d --scale api=3 --scale worker=5

# Or with Kubernetes
kubectl scale deployment file-extractor-api --replicas=5
```

### Load Balancing

```nginx
upstream api_backend {
    least_conn;
    server api1:8000;
    server api2:8000;
    server api3:8000;
}
```

### Auto-scaling

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: file-extractor-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: file-extractor-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Backup and Recovery

### Data Backup

```bash
# Backup Redis data
docker exec file_extractor_redis redis-cli BGSAVE
docker cp file_extractor_redis:/data/dump.rdb ./backup/

# Backup application data
tar -czf backup-$(date +%Y%m%d).tar.gz logs/ temp_files/
```

### Disaster Recovery

```bash
# Restore from backup
docker cp ./backup/dump.rdb file_extractor_redis:/data/
docker exec file_extractor_redis redis-cli BGREWRITEAOF
```

## Performance Tuning

### Resource Optimization

```yaml
# Optimize for high throughput
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '4.0'
        reservations:
          memory: 2G
          cpus: '2.0'
```

### Caching Strategy

```python
# Redis caching
import redis
from functools import lru_cache

redis_client = redis.Redis(host='redis', port=6379, db=0)

@lru_cache(maxsize=1000)
def get_cached_result(key):
    return redis_client.get(key)
```

## Troubleshooting

### Common Issues

1. **Memory Issues**: Increase container memory limits
2. **Port Conflicts**: Check for existing services on required ports
3. **Permission Errors**: Ensure proper file permissions
4. **Network Issues**: Verify Docker network configuration

### Debug Commands

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs api

# Access container shell
docker-compose exec api bash

# Check resource usage
docker stats

# Monitor network
docker network ls
docker network inspect file_extractor_network
```
