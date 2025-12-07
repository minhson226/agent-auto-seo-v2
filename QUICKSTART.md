# Quick Start Guide - Auto-SEO Platform

Get the Auto-SEO platform running in 5 minutes!

## Prerequisites

- Docker 20.10+ and Docker Compose v2+
- Git
- At least 8GB RAM available

## Step 1: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/minhson226/agent-auto-seo-v2.git
cd agent-auto-seo-v2

# Copy environment template
cp .env.example .env

# Edit .env and set required secrets
# Minimum required:
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD
# - JWT_SECRET_KEY
# - MINIO_ROOT_USER
# - MINIO_ROOT_PASSWORD
nano .env  # or your favorite editor
```

## Step 2: Start the Platform

```bash
# Pull pre-built images (faster)
docker compose -f docker-compose.prod.yml pull

# Or build locally (if images not available)
docker compose -f docker-compose.prod.yml build

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy (30-60 seconds)
docker compose -f docker-compose.prod.yml ps
```

## Step 3: Access the Dashboard

Open your browser to: **http://localhost:9100**

### First Login
1. Click "Create new account"
2. Enter email and password
3. Submit to create admin user
4. Login with your credentials

## Step 4: Verify System Health

Visit: **http://localhost:9100/system-status**

All services should show as "healthy" (green).

## Step 5: Your First Workflow

### 1. Create a Workspace
- Go to Dashboard home
- Click "Create Workspace"
- Enter name (e.g., "My Blog")

### 2. Upload Keywords
- Go to "Keywords" page
- Click "Upload Keywords"
- Upload a CSV file with keywords (or paste manually)
- View your keywords list

### 3. Create Topic Clusters
- Go to "Clustering" page
- Drag and drop keywords into topic groups
- Save clusters

### 4. Create Content Plan
- Go to "Content Plans"
- Click "Create Plan"
- Select workspace and keywords
- Configure article parameters (tone, length, etc.)
- Generate plan

### 5. Generate Articles
- Go to "Articles" page
- View articles from your plan
- Click "Generate" on any article
- Wait for AI to create content
- Review and edit as needed

### 6. Check SEO Score
- On article detail page
- Click "Run SEO Analysis"
- View score and recommendations
- Optimize based on feedback

### 7. Publish
- Go to "Publishing" page
- Configure WordPress connection
- Schedule or publish immediately

## Common Tasks

### View Logs
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f dashboard
docker compose -f docker-compose.prod.yml logs -f api-gateway
```

### Restart a Service
```bash
docker compose -f docker-compose.prod.yml restart dashboard
```

### Stop Everything
```bash
docker compose -f docker-compose.prod.yml down
```

### Stop and Remove Data
```bash
docker compose -f docker-compose.prod.yml down -v  # WARNING: Deletes all data!
```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:9100 | Main admin UI |
| **API Gateway** | http://localhost:9101 | REST API |
| **API Docs** | http://localhost:9101/docs | Swagger UI |
| **System Diagnostics** | http://localhost:9101/api/v1/diagnostics/ | Health status |
| MinIO Console | http://localhost:9001 | Object storage |
| Grafana | http://localhost:3000 | Monitoring |

## Troubleshooting

### Dashboard won't load
```bash
# Check if container is running
docker compose -f docker-compose.prod.yml ps dashboard

# Check logs
docker compose -f docker-compose.prod.yml logs dashboard

# Restart
docker compose -f docker-compose.prod.yml restart dashboard
```

### API Gateway errors
```bash
# Check health
curl http://localhost:9101/health

# View logs
docker compose -f docker-compose.prod.yml logs api-gateway

# Check if all backend services are healthy
curl http://localhost:9101/api/v1/diagnostics/
```

### Database connection errors
```bash
# Check PostgreSQL
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U autoseo

# Check Redis
docker compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} ping
```

### Services stuck on startup
```bash
# Check dependencies are healthy
docker compose -f docker-compose.prod.yml ps

# Restart in order
docker compose -f docker-compose.prod.yml restart postgres redis rabbitmq
sleep 30
docker compose -f docker-compose.prod.yml restart api-gateway auth-service
sleep 10
docker compose -f docker-compose.prod.yml restart dashboard
```

## Development Mode

For local development with hot-reload:

```bash
# Frontend only
cd frontend/dashboard
npm install
npm run dev
# Dashboard: http://localhost:5173

# Backend services
docker compose up -d postgres redis rabbitmq
# Then run individual services with `uvicorn` or IDE
```

## Production Deployment

See `IMPLEMENTATION_SUMMARY.md` for detailed production deployment guide.

Quick production checklist:
- [ ] Use strong passwords in .env
- [ ] Set JWT_SECRET_KEY to random string
- [ ] Configure SMTP for email notifications
- [ ] Set up reverse proxy (Nginx/Caddy) with HTTPS
- [ ] Configure backups for PostgreSQL
- [ ] Set up monitoring (Grafana/Prometheus)
- [ ] Configure log aggregation
- [ ] Test disaster recovery

## Getting Help

1. **Check System Status:** http://localhost:9100/system-status
2. **View Logs:** `docker compose -f docker-compose.prod.yml logs`
3. **API Documentation:** http://localhost:9101/docs
4. **Read Docs:** Check `README.md` and `IMPLEMENTATION_SUMMARY.md`

## Next Steps

- Read the full documentation in `README.md`
- Explore the API at http://localhost:9101/docs
- Check out the phase specifications in `docs/phase-specs/`
- Configure integrations (WordPress, external APIs)
- Set up monitoring and alerting

---

**Questions?** Check the documentation or open an issue!

**Happy SEO automating!** 🚀
