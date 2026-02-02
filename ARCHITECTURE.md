# UAI Engine Architecture

## Overview

UAI Engine is a monorepo-based AI-powered website builder that generates Next.js applications from natural language prompts. The system is designed for scalability, maintainability, and production use.

## System Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI   │────▶│   Runner    │
│   Frontend  │     │     API     │     │  Service    │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ PostgreSQL  │     │   Docker    │
                    └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Redis    │
                    └─────────────┘
```

## Components

### 1. Web Frontend (`apps/web`)

**Technology**: Next.js 14, TypeScript, Tailwind CSS, React Query

**Responsibilities**:
- User authentication UI
- Project management interface
- Prompt input and version generation
- File tree visualization
- Unified diff display
- Build status monitoring
- Preview iframe rendering
- Credits balance display

**Key Pages**:
- `/` - Landing page
- `/signup` - User registration
- `/signin` - User login
- `/dashboard` - Project list
- `/projects/new` - Create project
- `/projects/[id]` - Project workspace

### 2. API Service (`apps/api`)

**Technology**: FastAPI, Python 3.11+, SQLAlchemy, Alembic, Pydantic

**Responsibilities**:
- User authentication (JWT)
- Project CRUD operations
- Version management
- Build orchestration
- Credits management
- File tree and diff generation
- API rate limiting
- Structured logging

**Key Endpoints**:
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Current user
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `POST /api/v1/versions/projects/{id}/versions` - Create version
- `POST /api/v1/builds/versions/{id}/builds` - Create build
- `GET /api/v1/credits/balance` - Get credits

### 3. Runner Service (`apps/runner`)

**Technology**: FastAPI, Python 3.11+, Docker SDK

**Responsibilities**:
- Execute builds in sandboxed Docker containers
- Generate Next.js project structure
- Build Docker images
- Run preview containers
- Stream build logs
- Update build status via API
- Container lifecycle management

**Key Endpoints**:
- `POST /builds` - Start build execution
- `GET /health` - Health check

### 4. SDK (`packages/sdk`)

**Technology**: TypeScript, Axios

**Responsibilities**:
- Type-safe API client
- Authentication helpers
- Build management utilities
- Error handling

## Data Models

### User
- `id`: Primary key
- `email`: Unique email address
- `hashed_password`: Bcrypt hashed password
- `full_name`: User's full name
- `is_active`: Account status
- `credits`: Current credit balance
- `created_at`, `updated_at`: Timestamps

### Project
- `id`: Primary key
- `name`: Project name
- `description`: Optional description
- `owner_id`: Foreign key to User
- `created_at`, `updated_at`: Timestamps

### Version
- `id`: Primary key
- `project_id`: Foreign key to Project
- `prompt`: User's prompt text
- `file_tree`: JSON structure of generated files
- `unified_diff`: Diff from previous version
- `created_at`: Timestamp

### Build
- `id`: Primary key
- `project_id`: Foreign key to Project
- `version_id`: Foreign key to Version
- `status`: Enum (pending, running, success, failed, cancelled)
- `logs`: Build output logs
- `preview_url`: URL to preview container
- `error_message`: Error details if failed
- `created_at`, `updated_at`, `completed_at`: Timestamps

### CreditTransaction
- `id`: Primary key
- `user_id`: Foreign key to User
- `amount`: Credit amount (can be negative)
- `transaction_type`: Enum (build, export, refund, bonus)
- `description`: Transaction description
- `build_id`: Optional foreign key to Build
- `created_at`: Timestamp

## Build Flow

1. **User submits prompt** → Frontend sends to API
2. **API creates version** → Stores prompt and generates file tree
3. **User triggers build** → API creates build record
4. **API checks credits** → Verifies user has sufficient credits
5. **API charges credits** → Deducts credits from user
6. **API calls Runner** → Sends build request to Runner service
7. **Runner generates project** → Creates Next.js structure from file tree
8. **Runner builds Docker image** → Compiles Next.js application
9. **Runner starts container** → Runs preview server
10. **Runner updates API** → Sends build status, logs, preview URL
11. **Frontend polls API** → Displays build status and preview

## Security

- **Authentication**: JWT tokens with configurable expiration
- **Authorization**: User-scoped resources (projects, builds)
- **Input Validation**: Pydantic schemas for all inputs
- **Sandboxing**: Docker containers for build execution
- **Rate Limiting**: (To be implemented)
- **CORS**: Configured for frontend origins only

## Monitoring

- **Prometheus**: Metrics collection from API and Runner
- **Grafana**: Visualization and dashboards
- **Structured Logging**: JSON logs from all services
- **Health Checks**: `/health` endpoints on all services

## Scalability Considerations

- **Stateless Services**: API and Runner are stateless
- **Database Connection Pooling**: SQLAlchemy connection pooling
- **Horizontal Scaling**: Services can be scaled independently
- **Container Isolation**: Each build runs in isolated container
- **Async Operations**: FastAPI async endpoints for I/O operations

## Future Enhancements

- OAuth authentication (GitHub, Google)
- WebSocket support for real-time build updates
- Advanced AI model integration for code generation
- Export functionality (ZIP downloads)
- Team collaboration features
- Advanced monitoring and alerting
- CI/CD integration
