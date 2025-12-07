# Auto-SEO Platform

A comprehensive **Content & SEO Automation Platform** built with microservices architecture. The platform enables automated keyword research, content generation, SEO optimization, publishing, and performance analytics.

[![CI/CD Pipeline](https://github.com/your-org/auto-seo/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/your-org/auto-seo/actions/workflows/ci-cd.yml)

## 🚀 Quick Start

### Prerequisites

- Docker (v20.10+)
- Docker Compose (v2.0+)
- Git

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/auto-seo.git
cd auto-seo

# Copy environment variables
cp .env.example .env

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

### Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:9100 | Admin dashboard for managing the platform |
| **API Gateway** | http://localhost:9101 | Unified API endpoint for all services |
| PostgreSQL | localhost:5432 | Primary database (autoseo / autoseo_secret) |
| Redis | localhost:6379 | Cache and rate limiting |
| ClickHouse | localhost:8123 | Analytics database |
| MinIO Console | http://localhost:9001 | Object storage (minioadmin / minioadmin_secret) |
| Grafana | http://localhost:3000 | Monitoring dashboards (admin / grafana_secret) |
| Prometheus | http://localhost:9090 | Metrics collection |

## 📁 Project Structure

```
auto-seo/
├── frontend/                 # Frontend applications
│   └── dashboard/           # React admin dashboard
├── services/                 # Microservices
│   ├── api-gateway/         # API Gateway service
│   ├── auth-service/        # Authentication service
│   ├── keyword-ingestion/   # Keyword research service
│   ├── seo-strategy/        # SEO strategy & content planning
│   ├── content-generator/   # AI content generation
│   ├── seo-scorer/          # SEO scoring & analysis
│   ├── analytics/           # Analytics & reporting
│   └── notification-service/ # Notification service
├── infrastructure/          # Infrastructure configurations
│   ├── postgres/            # PostgreSQL configs
│   ├── redis/               # Redis configs
│   ├── clickhouse/          # ClickHouse configs
│   ├── minio/               # MinIO configs
│   └── monitoring/          # Prometheus & Grafana configs
├── k8s/                     # Kubernetes manifests
│   ├── namespaces/          # Namespace definitions
│   ├── databases/           # Database deployments
│   ├── monitoring/          # Monitoring stack
│   ├── configmaps/          # ConfigMaps
│   └── secrets/             # Secrets (dev only)
├── migrations/              # Database migrations
├── docs/                    # Documentation
│   ├── setup/               # Setup guides
│   ├── architecture/        # Architecture docs
│   └── deployment/          # Deployment guides
├── docker-compose.yml       # Local development
└── docker-compose.dev.yml   # Development overrides
```

## 🏗️ Architecture

Auto-SEO uses a microservices architecture with event-driven communication:

- **Dashboard**: React-based admin UI for managing the entire platform
- **API Gateway**: Unified REST API, request routing, rate limiting, authentication
- **Core Services**: Auth, Workspace Management, Notifications
- **Domain Services**: Keyword Ingestion, SEO Strategy, Content Generation, SEO Scoring, Analytics
- **Data Layer**: PostgreSQL, Redis, ClickHouse, MinIO

See [Architecture Overview](docs/architecture/overview.md) for detailed documentation.

## 🎯 Main User Workflows

The dashboard provides end-to-end workflows for automated SEO content creation:

### 1. Keyword Research & Ingestion
- Upload keyword lists or integrate with keyword research tools
- View keyword metrics (volume, difficulty, CPC)
- Organize keywords into collections

### 2. Topic Clustering
- Drag-and-drop interface for grouping related keywords
- AI-assisted clustering suggestions
- Create topic groups for content planning

### 3. Content Planning
- Generate content plans from keyword clusters
- Define article parameters (tone, length, structure)
- Schedule content calendar

### 4. Content Generation
- AI-powered article generation using GPT-4 or other LLMs
- Rich text editor for review and refinement
- SEO metadata generation (title, description, keywords)

### 5. SEO Scoring & Optimization
- Automated SEO analysis of generated content
- On-page SEO recommendations
- Keyword density and placement optimization

### 6. Publishing & Distribution
- WordPress integration for direct publishing
- Schedule publication dates
- Track publishing status

### 7. Analytics & Reporting
- Performance metrics (traffic, rankings, conversions)
- ROI tracking and cost analysis
- Visual dashboards and reports

## 🛠️ Technology Stack

| Category | Technologies |
|----------|-------------|
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS, React Query |
| **Backend** | Python 3.11+, FastAPI, Node.js, Go |
| **Databases** | PostgreSQL 15+, Redis 7+, ClickHouse |
| **Storage** | MinIO (S3-compatible) |
| **Container** | Docker, Kubernetes |
| **CI/CD** | GitHub Actions |
| **Monitoring** | Prometheus, Grafana |

## 📖 Documentation

- [Local Development Setup](docs/setup/local-development.md)
- [Architecture Overview](docs/architecture/overview.md)
- [Kubernetes Deployment](docs/deployment/kubernetes.md)
- [Phase Specifications](docs/phase-specs/PLAN_OVERVIEW.md)

## 🧪 Testing

```bash
# Run infrastructure tests
docker-compose up -d postgres redis
docker-compose exec postgres pg_isready -U autoseo
docker-compose exec redis redis-cli -a redis_secret ping
```

## 🚢 Deployment

### Kubernetes

```bash
# Create namespaces
kubectl apply -f k8s/namespaces/

# Deploy databases
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/databases/

# Deploy monitoring
kubectl apply -f k8s/monitoring/
```

See [Kubernetes Deployment Guide](docs/deployment/kubernetes.md) for detailed instructions.

## 📊 Monitoring

- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Health Checks**: All services include health endpoints

## 🔒 Security

- JWT-based authentication
- Role-based access control (RBAC)
- Secrets managed via Kubernetes Secrets
- Encryption at rest and in transit

## 🤝 Contributing

1. Read the phase specifications in `docs/phase-specs/`
2. Follow the implementation prompts in each phase YAML file
3. Ensure tests pass before submitting PR
4. Update documentation as needed

## 📄 License

This project is proprietary. All rights reserved.

---

## Phase Planning (Legacy)

This repository also includes the Phase Planner tooling:

- **Phase Specs**: `docs/phase-specs/phases/`
- **Plan Overview**: `docs/phase-specs/PLAN_OVERVIEW.md`
- **Validation Report**: `docs/phase-specs/VALIDATION_REPORT.md`

The Phase Planner extracts implementation phases from master specifications and generates implementation prompts for automated development.
