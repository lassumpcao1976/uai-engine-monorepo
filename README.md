# UAI Engine

**You think, we build.**

UAI Engine is an AI-powered website builder that generates, builds, and previews Next.js applications from natural language prompts.

## Architecture

This is a production-grade monorepo built with:

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend API**: FastAPI, Python 3.11+, PostgreSQL, Redis
- **Build Runner**: Docker-based sandboxed build execution
- **Monitoring**: Prometheus + Grafana
- **Monorepo**: Turborepo + pnpm

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ and pnpm
- Python 3.11+ (for local API development)

### One-Command Setup

```bash
./scripts/setup.sh
```

This will:
1. Install dependencies
2. Start PostgreSQL, Redis, Prometheus, and Grafana
3. Run database migrations
4. Set up environment variables

### Start All Services

**Option 1: Docker Compose (Recommended)**
```bash
./scripts/start.sh
```

Or manually:
```bash
cd infra
docker-compose up
```

**Option 2: Development Mode**
```bash
./scripts/dev.sh
```

## Service URLs

Once running, access services at:

- **Web Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Runner Service**: http://localhost:8001
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

## Project Structure

```
uai-engine/
├── apps/
│   ├── api/          # FastAPI backend
│   ├── web/          # Next.js frontend
│   └── runner/       # Docker build executor
├── packages/
│   └── sdk/          # TypeScript SDK
├── infra/            # Docker Compose configs
└── scripts/          # Setup and utility scripts
```

## Features (Phase 1)

- ✅ User authentication (email/password, JWT)
- ✅ Project management
- ✅ Version generation from prompts
- ✅ Unified diffs between versions
- ✅ File tree visualization
- ✅ Docker-based builds
- ✅ Build logs streaming
- ✅ Preview iframe
- ✅ Credits wallet system
- ✅ Charge rules for builds and exports

## Development

### Running Individual Services

**API:**
```bash
cd apps/api
uvicorn app.main:app --reload
```

**Web:**
```bash
cd apps/web
pnpm dev
```

**Runner:**
```bash
cd apps/runner
uvicorn app.main:app --reload --port 8001
```

### Database Migrations

```bash
cd apps/api
alembic upgrade head
```

### Testing

```bash
# Run all tests
pnpm test

# Run API tests
cd apps/api && pytest

# Run web tests
cd apps/web && pnpm test
```

## Environment Variables

See `.env.example` for all available environment variables. Key ones:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `API_SECRET_KEY`: JWT secret key (change in production!)
- `RUNNER_URL`: Runner service URL
- `CREDITS_PER_BUILD`: Credits charged per build (default: 10)
- `CREDITS_PER_EXPORT`: Credits charged per export (default: 50)

## End-to-End Flow

1. **Sign Up**: Create an account at `/signup`
2. **Sign In**: Login at `/signin`
3. **Create Project**: Click "New Project" on dashboard
4. **Generate Version**: Enter a prompt describing your website
5. **Build**: Click "Build" on a version
6. **Preview**: View the built site in the preview iframe
7. **View Diffs**: See unified diffs between versions
8. **File Tree**: Browse the generated file structure

## Credits System

- New users start with 1000 credits
- Builds cost 10 credits
- Exports cost 50 credits
- Credits are checked before operations
- Failed builds can be refunded

## Monitoring

- **Prometheus**: Collects metrics from API and Runner services
- **Grafana**: Visualizes metrics and provides dashboards
- **Structured Logging**: JSON logs from all services

## Production Deployment

For Render deployment, see `render.yaml` (to be created). The Docker Compose setup is suitable for local development and can be adapted for production.

## License

Private - All Rights Reserved
