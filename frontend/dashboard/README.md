# Auto-SEO Dashboard

Modern, responsive admin dashboard for managing the Auto-SEO platform. Built with React, TypeScript, and TailwindCSS.

## Features

### 🔐 Authentication
- Secure login/register with JWT tokens
- Role-based access control
- Session management

### 📊 Dashboard Home
- Overview metrics and KPIs
- Quick access to main features
- Service health monitoring

### 🔑 Keyword Management
- Upload and manage keyword lists
- View keyword metrics (volume, difficulty, CPC)
- Filter and search capabilities

### 🎯 Topic Clustering
- Drag-and-drop interface for grouping keywords
- AI-assisted clustering
- Visual cluster management

### 📝 Content Planning
- Create content plans from keyword clusters
- Define article parameters
- Content calendar view

### ✍️ Article Management
- View all generated articles
- Edit article content and metadata
- SEO optimization tools

### 🎨 Publishing
- WordPress integration
- Schedule publications
- Track publishing status

### 📈 Analytics
- Performance charts and graphs
- Token usage and cost tracking
- Per-workspace statistics

### ⚙️ System Status
- Real-time service health monitoring
- Build and version information
- Environment diagnostics

## Development

### Prerequisites
- Node.js 20+
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run linter
npm run lint
```

### Environment Variables

Create a `.env.development` file:

```env
VITE_API_BASE_URL=http://localhost:9101
VITE_APP_ENV=development
VITE_APP_TITLE=Auto-SEO Dashboard (Dev)
```

For production, create `.env.production`:

```env
VITE_API_BASE_URL=http://your-api-gateway:9101
VITE_APP_ENV=production
VITE_APP_TITLE=Auto-SEO Dashboard
```

## Project Structure

```
dashboard/
├── public/              # Static assets
├── src/
│   ├── api/            # API client and endpoints
│   │   ├── client.ts   # Axios instance with JWT interceptor
│   │   ├── auth.ts     # Authentication API
│   │   ├── workspaces.ts
│   │   ├── keywords.ts
│   │   ├── content.ts
│   │   ├── analytics.ts
│   │   └── diagnostics.ts
│   ├── components/     # React components
│   │   ├── auth/       # Login, Register
│   │   ├── layout/     # Layout, Sidebar, TopBar
│   │   ├── workspace/  # Workspace management
│   │   ├── keywords/   # Keyword components
│   │   ├── clustering/ # Drag-and-drop clustering
│   │   ├── content/    # Article and plan components
│   │   └── analytics/  # Charts and metrics
│   ├── hooks/          # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useWorkspace.ts
│   │   └── useKeywords.ts
│   ├── pages/          # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Keywords.tsx
│   │   ├── Clustering.tsx
│   │   ├── ContentPlans.tsx
│   │   ├── Articles.tsx
│   │   ├── Publishing.tsx
│   │   ├── Analytics.tsx
│   │   ├── SystemStatus.tsx
│   │   └── Settings.tsx
│   ├── store/          # State management
│   │   ├── authStore.ts
│   │   └── workspaceStore.ts
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Entry point
├── Dockerfile          # Production Docker build
├── nginx.conf          # Nginx configuration
└── vite.config.ts      # Vite configuration
```

## Building for Production

### Docker Build

```bash
# Build Docker image
docker build -t auto-seo-dashboard .

# Run container
docker run -p 9100:80 auto-seo-dashboard
```

The dashboard will be available at `http://localhost:9100`

### Manual Build

```bash
# Build static files
npm run build

# Output will be in ./dist directory
# Serve with any static file server (nginx, apache, etc.)
```

## Features in Detail

### Authentication Flow
1. User enters credentials on login page
2. API client sends POST to `/api/v1/auth/login`
3. JWT tokens stored in localStorage
4. Axios interceptor adds `Authorization: Bearer <token>` to all requests
5. On 401 error, user redirected to login and tokens cleared

### API Client
- Centralized Axios instance
- Automatic JWT token attachment
- Global error handling
- Request/response interceptors
- TypeScript types for all endpoints

### State Management
- React Query for server state (caching, refetching)
- Zustand for client state (auth, workspace selection)
- Local storage for persistence

### Styling
- TailwindCSS for utility-first styling
- Responsive design (mobile, tablet, desktop)
- Heroicons for consistent iconography

## Testing

```bash
# Run unit tests
npm test

# Run tests in watch mode
npm run test:watch
```

## Deployment

The dashboard is deployed as part of the Auto-SEO platform:

```yaml
# docker-compose.prod.yml
dashboard:
  image: ghcr.io/minhson226/agent-auto-seo-v2/dashboard:latest
  ports:
    - "9100:80"
  depends_on:
    - api-gateway
```

Access the production dashboard at: `http://<server-ip>:9100`

## License

Proprietary - All rights reserved
