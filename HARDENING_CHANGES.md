# Hardening Changes Summary

## Priority B Fixes Implemented

### B1: Preview Route Security ✅
**Files Changed:**
- `apps/api/routes/preview.py` - Complete rewrite with security hardening

**Changes:**
- UUID format validation for project_id and build_id (prevents path traversal)
- Project ownership enforcement (checks user_id match when authenticated)
- Path validation using `resolve().relative_to()` to prevent directory traversal
- Security headers added:
  - `Content-Security-Policy`: Restricts resource loading
  - `X-Content-Type-Options: nosniff`: Prevents MIME sniffing
  - `X-Frame-Options: SAMEORIGIN`: Allows iframe from same origin
  - `Referrer-Policy: strict-origin-when-cross-origin`
- Only serves from build-specific project directory
- Test file created: `apps/api/tests/test_preview_security.py`

### B2: DiffService Safety ✅
**Files Changed:**
- `apps/api/services/diff_service.py` - Complete rewrite with validation gates

**Changes:**
- `validate_file_for_edit()`: Validates file path, type, and directory restrictions
- Allowed file types: `.ts`, `.tsx`, `.js`, `.jsx`, `.css`, `.json`, `.md`, `.txt` only
- Forbidden directories: `node_modules`, `.next`, `.git`, `dist`, `build`
- Path traversal prevention using `resolve().relative_to()`
- `validate_and_apply_changes()`: Runs lint after applying changes, reverts on failure
- `generate_changes_from_prompt()`: Returns `(changes, error_message)` tuple
  - Returns structured error if no pattern matches (no guessing)
  - Validates all files before applying
- Max limits: 10 files per change, 1000 lines per file

### B3: Repair Loop Constraints ✅
**Files Changed:**
- `apps/api/services/repair_service.py` - Added constraints and limits

**Changes:**
- `max_files_per_repair = 3`: Limits files changed per repair attempt
- `max_lines_per_repair = 50`: Limits lines changed per repair attempt
- Counters track changes: `files_changed_count`, `lines_changed_count`
- Dependency addition: Only adds if explicitly needed and logged
- Repair attempts logged with file counts
- Stops after 3 attempts with clear error message
- Validation before applying repair patches

### B4: Rate Limiting for Production ✅
**Files Changed:**
- `apps/api/services/rate_limiter.py` - New file with Postgres and memory limiters
- `apps/api/routes/projects.py` - Updated to use rate limiter service
- `apps/api/database.py` - Creates rate_limits table
- `README.md` - Documented dev vs prod rate limiting

**Changes:**
- Postgres-based rate limiting: `check_rate_limit_postgres()` using `rate_limits` table
- Memory-based rate limiting: `check_rate_limit_memory()` for dev
- Environment variable: `USE_POSTGRES_RATE_LIMIT=true` to enable Postgres limiter
- Automatic table creation on startup
- `README.md` updated with rate limiting documentation

### B5: Credits Config Centralization ✅
**Files Changed:**
- `apps/api/config/credits.py` - New centralized config file
- `apps/api/services/credit_service.py` - Imports from config
- `apps/api/services/project_orchestrator.py` - Imports from config
- `apps/api/routes/projects.py` - Imports from config
- `apps/api/routes/auth.py` - Uses `FREE_TIER_STARTING_CREDITS` from config
- `apps/api/main.py` - Added `/credits/costs` endpoint
- `apps/api/routes/credits.py` - Added `/credits/costs` endpoint

**Changes:**
- All credit costs in single config: `apps/api/config/credits.py`
- `get_credit_costs()` function for API endpoint
- Frontend can fetch costs from `/credits/costs` or `/api/credits/costs`
- No hardcoded values in multiple places
- Values match product decisions:
  - create_project: 5.0
  - small_edit: 1.0
  - medium_edit: 3.0
  - large_edit: 10.0
  - rebuild: 1.0
  - rollback: 3.0
  - export: 20.0
  - publish: 50.0

## Priority C: Smoke Test Script ✅
**Files Changed:**
- `scripts/smoke_test.sh` - New end-to-end test script

**Features:**
- Signs up a user
- Creates a project
- Sends prompt iteration
- Fetches file tree
- Fetches build logs
- Fetches preview
- Exits with proper status codes
- Color-coded output
- Test counter

**Usage:**
```bash
./scripts/smoke_test.sh
```

## Code Changes Summary

### New Files:
1. `apps/api/config/credits.py` - Centralized credit configuration
2. `apps/api/services/rate_limiter.py` - Rate limiting service
3. `apps/api/services/log_sanitizer.py` - Secret redaction
4. `apps/api/tests/test_preview_security.py` - Preview security tests
5. `scripts/smoke_test.sh` - End-to-end smoke test

### Modified Files:
1. `apps/api/routes/preview.py` - Security hardening
2. `apps/api/services/diff_service.py` - Validation gates and safety checks
3. `apps/api/services/repair_service.py` - Constraints and limits
4. `apps/api/services/project_orchestrator.py` - Uses new diff service signature, repair validation
5. `apps/api/services/credit_service.py` - Returns transaction_id, imports from config
6. `apps/api/routes/projects.py` - Rate limiting, safety checks, credit transparency
7. `apps/api/routes/auth.py` - Uses config for starting credits
8. `apps/api/routes/credits.py` - Added costs endpoint
9. `apps/api/main.py` - Added credit costs endpoint
10. `apps/api/database.py` - Creates rate_limits table
11. `README.md` - Rate limiting documentation
