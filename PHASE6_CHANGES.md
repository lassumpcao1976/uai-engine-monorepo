# Phase 6 Changes Summary

## Overview
Phase 6 refactored the build system to be deployable on Render by separating Docker execution from the API service, implemented chat message persistence, added a real diff viewer, and created a comprehensive validation script.

## Files Changed

### A. Build System Architecture

#### New Files:
1. `apps/runner/main.py` - Build runner service (FastAPI)
2. `apps/runner/requirements.txt` - Runner dependencies
3. `apps/runner/Dockerfile` - Runner container definition

#### Modified Files:
1. `apps/api/services/build_service.py` - Refactored to call runner via HTTP instead of Docker directly
2. `apps/api/services/project_orchestrator.py` - Updated repair loop to use `repair_build` method
3. `apps/api/requirements.txt` - Added `requests==2.31.0`
4. `infra/docker-compose.dev.yml` - Added runner service
5. `infra/docker-compose.yml` - Added runner service

### B. Chat Message Persistence

#### Modified Files:
1. `apps/api/routes/projects.py` - Added `GET /projects/{id}/messages` endpoint
2. `apps/api/schemas.py` - Added `ChatMessageResponse` and `MessagesResponse` schemas
3. `apps/web/app/workspace/[projectId]/page.tsx` - Updated `fetchMessages` to load from API

### C. Diff Viewer

#### Modified Files:
1. `apps/api/schemas.py` - Added `unified_diff_text` field to `VersionResponse`
2. `apps/api/routes/builds.py` - Generate unified diff text from `code_diff` JSON
3. `apps/web/app/workspace/[projectId]/page.tsx` - Implemented diff viewer with version selector and syntax highlighting

### D. Validation Script

#### New Files:
1. `scripts/validate_all.sh` - Comprehensive validation script

#### Modified Files:
1. `README.md` - Added architecture section and environment variables documentation

## Key Changes

### 1. Build Service Refactoring

**Before**: `BuildService` directly used Docker client inside API container
**After**: `BuildService` calls Runner service via HTTP with authentication

**Benefits**:
- API container doesn't need Docker access
- Can deploy API on Render without Docker-in-Docker
- Clear separation of concerns
- Runner can be scaled independently

### 2. Runner Service

- FastAPI service running on port 8001
- Authenticates requests using `RUNNER_SECRET` Bearer token
- Handles `/build` and `/repair` endpoints
- Executes builds in isolated Docker containers with resource limits
- Returns build results (logs, exit code) to API

### 3. Chat Message Persistence

- `POST /projects/{id}/prompt` already creates `ChatMessage` records (was working)
- Added `GET /projects/{id}/messages` to retrieve chat history
- Frontend loads and displays saved chat messages

### 4. Diff Viewer

- Backend generates unified diff text from `code_diff` JSON
- Frontend displays diff with syntax highlighting:
  - Green for added lines (`+`)
  - Red for removed lines (`-`)
  - Blue for hunk headers (`@@`)
  - Yellow for file headers (`+++`, `---`)
- Version selector to view diffs for different versions
- Empty state when no diff available

### 5. Validation Script

- Runs dev mode, smoke test, prod mode, smoke test, and API tests
- Writes logs to `validation_logs/` directory with timestamps
- No macOS-incompatible utilities (no `timeout` command)
- Comprehensive health checks and error reporting

## Environment Variables

### Required:
- `JWT_SECRET`: Minimum 32 characters
- `RUNNER_SECRET`: Minimum 32 characters

### API Service:
- `RUNNER_URL`: Default `http://runner:8001`
- `RUNNER_SECRET`: Must match runner's `RUNNER_SECRET`

### Runner Service:
- `PROJECTS_DIR`: Must match API's `PROJECTS_DIR`
- `RUNNER_SECRET`: Must match API's `RUNNER_SECRET`

## Docker Compose Changes

### Dev Mode (`infra/docker-compose.dev.yml`):
- Added `runner` service with Docker socket mount
- API depends on runner
- Shared `api_projects` volume between API and runner

### Prod Mode (`infra/docker-compose.yml`):
- Added `runner` service with Docker socket mount
- API depends on runner
- Shared `api_projects` volume between API and runner
- No bind mounts (production-ready)

## Render Deployment Viability

✅ **API does not run Docker**: API service has no Docker socket access
✅ **Runner runs Docker**: Runner service has Docker socket access and can execute builds
✅ **Separation of concerns**: Clear architecture for deployment

**Deployment Strategy**:
- Deploy API service on Render (no Docker needed)
- Deploy Runner service on a platform with Docker support (e.g., DigitalOcean, AWS ECS)
- Or use Render's Docker service for runner if available

## Testing

Run comprehensive validation:
```bash
chmod +x scripts/validate_all.sh
./scripts/validate_all.sh
```

This will:
1. Start dev mode and run smoke test
2. Start prod mode and run smoke test
3. Run API unit tests
4. Generate logs in `validation_logs/` directory

## Next Steps

1. Deploy API to Render
2. Deploy Runner to Docker-capable platform
3. Configure environment variables
4. Update `RUNNER_URL` in API to point to deployed runner
5. Test end-to-end build flow
