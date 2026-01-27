# UAI Engine MVP

A premium project template generator that runs locally with one command.

## Quick Start

```bash
make dev
```

Or:

```bash
docker compose -f infra/docker-compose.yml up --build
```

This will start:
- Web frontend on http://localhost:3000
- API backend on http://localhost:8000
- PostgreSQL database on localhost:5432

## Project Structure

```
.
├── apps/
│   ├── web/          # Next.js 14 frontend
│   ├── api/          # FastAPI backend
│   └── runner/        # Build runner service (Docker builds)
├── packages/
│   └── sdk/          # Shared SDK (future)
├── infra/
│   ├── docker-compose.yml      # Production config
│   └── docker-compose.dev.yml  # Development config
└── Makefile
```

## Architecture

### Services

1. **Web** (`apps/web`): Next.js 14 frontend application
   - Serves the user interface
   - Communicates with API via REST

2. **API** (`apps/api`): FastAPI backend application
   - Handles authentication, projects, credits, builds
   - Does NOT run Docker builds directly
   - Communicates with Runner service via HTTP for builds

3. **Runner** (`apps/runner`): Build execution service
   - Handles all Docker builds in isolated containers
   - Owns Docker socket access
   - Receives build requests from API via authenticated HTTP calls
   - Manages project workspaces and build artifacts

4. **PostgreSQL**: Database for all persistent data

### Build Flow

1. User sends prompt via API
2. API processes prompt, creates version, applies changes
3. API calls Runner service via HTTP with authentication
4. Runner executes build in Docker container with resource limits
5. Runner returns build results (logs, exit code) to API
6. API stores build results in database
7. Frontend displays build status and preview

### Environment Variables

#### Required for All Modes

- `JWT_SECRET`: Secret key for JWT tokens (minimum 32 characters)
- `RUNNER_SECRET`: Secret key for API-Runner authentication (minimum 32 characters)

#### API Service

- `DATABASE_URL`: PostgreSQL connection string
- `ARTIFACTS_DIR`: Directory for build artifacts
- `TEMPLATES_DIR`: Directory for project templates
- `PROJECTS_DIR`: Directory for project workspaces
- `RUNNER_URL`: URL of runner service (default: `http://runner:8001`)
- `RUNNER_SECRET`: Secret for authenticating with runner

#### Runner Service

- `PROJECTS_DIR`: Directory for project workspaces (must match API)
- `RUNNER_SECRET`: Secret for authenticating API requests
- `PORT`: Port to listen on (default: 8001)

#### Web Service

- `NEXT_PUBLIC_API_URL`: Public API URL (e.g., `http://localhost:8000`)

### Docker Socket Access

- **API service**: Does NOT mount Docker socket (no Docker access)
- **Runner service**: Mounts Docker socket (`/var/run/docker.sock`) for build execution
- This separation ensures API can be deployed on platforms like Render without Docker-in-Docker requirements

## Development

- `make dev` - Start all services in development mode (hot reload, bind mounts)
- `make prod` - Start all services in production mode (no bind mounts, optimized builds)
- `make lint` - Run linters
- `make test` - Run tests
- `make build` - Build Docker images
- `make clean` - Clean up containers and artifacts

### Rate Limiting

- **Development**: Uses in-memory rate limiting (10 requests/minute per user)
- **Production**: Set `USE_POSTGRES_RATE_LIMIT=true` to use Postgres-based rate limiting
  - Creates `rate_limits` table automatically
  - Provides shared rate limiting across instances

## Features

- Generate Next.js SaaS starter templates
- Generate FastAPI API starter templates
- Download projects as ZIP files
- View project manifests and evaluation reports
