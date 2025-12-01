# Local Development Setup Guide

This guide will help you set up the Auto-SEO development environment on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (v20.10+): [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (v2.0+): Usually included with Docker Desktop
- **Git**: [Install Git](https://git-scm.com/downloads)
- **kubectl** (optional, for Kubernetes): [Install kubectl](https://kubernetes.io/docs/tasks/tools/)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/auto-seo.git
cd auto-seo
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your local settings (optional for development)
# The default values should work out of the box
```

### 3. Start the Infrastructure

```bash
# Start all services
docker-compose up -d

# Or start specific services
docker-compose up -d postgres redis

# View logs
docker-compose logs -f
```

### 4. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

You should see the following services:
- `autoseo-postgres` - PostgreSQL database (port 5432)
- `autoseo-redis` - Redis cache (port 6379)
- `autoseo-clickhouse` - ClickHouse analytics (ports 8123, 9000)
- `autoseo-minio` - MinIO object storage (ports 9001, 9002)
- `autoseo-prometheus` - Prometheus monitoring (port 9090)
- `autoseo-grafana` - Grafana dashboards (port 3000)

## Service Access

### PostgreSQL

```bash
# Connect via CLI
docker-compose exec postgres psql -U autoseo -d autoseo

# Connection string
postgresql://autoseo:autoseo_secret@localhost:5432/autoseo
```

### Redis

```bash
# Connect via CLI
docker-compose exec redis redis-cli -a redis_secret

# Test connection
docker-compose exec redis redis-cli -a redis_secret ping
```

### ClickHouse

```bash
# Access via HTTP interface
curl "http://localhost:8123/?query=SELECT%201"

# Connect via CLI
docker-compose exec clickhouse clickhouse-client

# Web interface available at http://localhost:8123/play
```

### MinIO (S3-compatible storage)

- **Console URL**: http://localhost:9001
- **API URL**: http://localhost:9002
- **Default credentials**: minioadmin / minioadmin_secret

### Grafana

- **URL**: http://localhost:3000
- **Default credentials**: admin / grafana_secret

### Prometheus

- **URL**: http://localhost:9090

## Running Migrations

Database migrations are stored in the `migrations/` directory.

```bash
# Apply migrations manually (during development)
docker-compose exec postgres psql -U autoseo -d autoseo -f /docker-entrypoint-initdb.d/01-init.sql

# Or copy and run specific migration files
docker cp migrations/001_create_users_table.sql autoseo-postgres:/tmp/
docker-compose exec postgres psql -U autoseo -d autoseo -f /tmp/001_create_users_table.sql
```

## Development Workflow

### Starting Fresh

```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
```

### Executing Commands in Containers

```bash
# PostgreSQL
docker-compose exec postgres psql -U autoseo

# Redis
docker-compose exec redis redis-cli

# ClickHouse
docker-compose exec clickhouse clickhouse-client
```

## Troubleshooting

### Port Conflicts

If you have port conflicts, edit the `.env` file to use different ports:

```bash
POSTGRES_PORT=5433
REDIS_PORT=6380
```

### Permission Issues

On Linux, you might need to fix permissions:

```bash
sudo chown -R $USER:$USER .
```

### Container Won't Start

Check logs for the specific container:

```bash
docker-compose logs postgres
```

### Database Connection Issues

Ensure the database is healthy:

```bash
docker-compose exec postgres pg_isready -U autoseo
```

## Next Steps

After setting up the local environment:

1. **Run migrations** to set up the database schema
2. **Configure MinIO buckets** (done automatically on first start)
3. **Import sample data** (if available)
4. **Start developing!**

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [ClickHouse Documentation](https://clickhouse.com/docs/)
- [MinIO Documentation](https://min.io/docs/)
