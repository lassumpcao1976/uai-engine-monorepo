#!/bin/bash
# Comprehensive validation script for UAI Engine
# Runs dev mode, smoke test, prod mode, smoke test, and API tests

set -e  # Exit on error

LOG_DIR="validation_logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/validation_${TIMESTAMP}.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_section() {
    echo "" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
    echo "$1" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

log "Starting comprehensive validation"
log "Log file: $LOG_FILE"

# Check prerequisites
log_section "Checking Prerequisites"
if ! command -v docker &> /dev/null; then
    log "${RED}ERROR: docker not found${NC}"
    exit 1
fi
if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
    log "${RED}ERROR: docker compose not found${NC}"
    exit 1
fi
log "${GREEN}✓ Prerequisites OK${NC}"

# Set required environment variables
export JWT_SECRET="${JWT_SECRET:-dev-secret-key-minimum-32-chars-for-local-testing-only}"
export RUNNER_SECRET="${RUNNER_SECRET:-dev-runner-secret-minimum-32-chars-for-local-testing-only}"

# Cleanup function
cleanup() {
    log "Cleaning up..."
    docker compose -f infra/docker-compose.dev.yml down 2>&1 | tee -a "$LOG_FILE" || true
    docker compose -f infra/docker-compose.yml down 2>&1 | tee -a "$LOG_FILE" || true
}

trap cleanup EXIT

# Phase 1: Dev Mode
log_section "Phase 1: Dev Mode Validation"
log "Starting dev mode..."

docker compose -f infra/docker-compose.dev.yml down 2>&1 | tee -a "$LOG_FILE" || true
docker compose -f infra/docker-compose.dev.yml up --build -d 2>&1 | tee -a "$LOG_FILE"

log "Waiting for services to start..."
sleep 10

# Check if services are running
log "Checking service status..."
docker compose -f infra/docker-compose.dev.yml ps 2>&1 | tee -a "$LOG_FILE"

# Health checks
log "Running health checks..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log "${GREEN}✓ API health check passed${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        log "${RED}✗ API health check failed${NC}"
        docker compose -f infra/docker-compose.dev.yml logs --tail=50 api 2>&1 | tee -a "$LOG_FILE"
        exit 1
    fi
    sleep 2
done

for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        log "${GREEN}✓ Web health check passed${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        log "${RED}✗ Web health check failed${NC}"
        log "Web container logs (last 200 lines):"
        docker compose -f infra/docker-compose.dev.yml logs --tail=200 web 2>&1 | tee -a "$LOG_FILE"
        log "Web container status:"
        docker compose -f infra/docker-compose.dev.yml ps web 2>&1 | tee -a "$LOG_FILE"
        # Check for npm ci failures specifically
        if docker compose -f infra/docker-compose.dev.yml logs web 2>&1 | grep -q "npm ci failed\|npm ERR!"; then
            log "${RED}✗ npm ci failure detected in web container${NC}"
            log "npm debug log snippet:"
            docker compose -f infra/docker-compose.dev.yml exec -T web sh -c "cat ~/.npm/_logs/*-debug-*.log 2>/dev/null | tail -50" 2>&1 | tee -a "$LOG_FILE" || true
        fi
        exit 1
    fi
    sleep 2
done

# Smoke test in dev mode
log_section "Running Smoke Test (Dev Mode)"
if [ -f scripts/smoke_test.sh ]; then
    chmod +x scripts/smoke_test.sh
    set +e  # Temporarily disable exit on error to capture exit code
    ./scripts/smoke_test.sh 2>&1 | tee -a "$LOG_FILE"
    SMOKE_EXIT_CODE=${PIPESTATUS[0]}
    set -e  # Re-enable exit on error
    if [ $SMOKE_EXIT_CODE -eq 0 ]; then
        log "${GREEN}✓ Smoke test passed${NC}"
    else
        log "${RED}✗ Smoke test failed with exit code $SMOKE_EXIT_CODE${NC}"
        exit 1
    fi
else
    log "${YELLOW}⚠ Smoke test script not found, skipping${NC}"
fi

# Stop dev mode
log "Stopping dev mode..."
docker compose -f infra/docker-compose.dev.yml down 2>&1 | tee -a "$LOG_FILE"

# Phase 2: Prod Mode
log_section "Phase 2: Prod Mode Validation"
log "Starting prod mode..."

docker compose -f infra/docker-compose.yml down 2>&1 | tee -a "$LOG_FILE" || true
docker compose -f infra/docker-compose.yml up --build -d 2>&1 | tee -a "$LOG_FILE"

log "Waiting for services to start..."
sleep 15

# Check if services are running
log "Checking service status..."
docker compose -f infra/docker-compose.yml ps 2>&1 | tee -a "$LOG_FILE"

# Health checks
log "Running health checks..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log "${GREEN}✓ API health check passed${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        log "${RED}✗ API health check failed${NC}"
        docker compose -f infra/docker-compose.yml logs --tail=50 api 2>&1 | tee -a "$LOG_FILE"
        exit 1
    fi
    sleep 2
done

for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        log "${GREEN}✓ Web health check passed${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        log "${RED}✗ Web health check failed${NC}"
        log "Web container logs (last 200 lines):"
        docker compose -f infra/docker-compose.yml logs --tail=200 web 2>&1 | tee -a "$LOG_FILE"
        log "Web container status:"
        docker compose -f infra/docker-compose.yml ps web 2>&1 | tee -a "$LOG_FILE"
        # Check for npm ci failures specifically
        if docker compose -f infra/docker-compose.yml logs web 2>&1 | grep -q "npm ci failed\|npm ERR!"; then
            log "${RED}✗ npm ci failure detected in web container${NC}"
            log "npm debug log snippet:"
            docker compose -f infra/docker-compose.yml exec -T web sh -c "cat ~/.npm/_logs/*-debug-*.log 2>/dev/null | tail -50" 2>&1 | tee -a "$LOG_FILE" || true
        fi
        exit 1
    fi
    sleep 2
done

# Smoke test in prod mode
log_section "Running Smoke Test (Prod Mode)"
if [ -f scripts/smoke_test.sh ]; then
    chmod +x scripts/smoke_test.sh
    set +e  # Temporarily disable exit on error to capture exit code
    PROD_MODE=1 ./scripts/smoke_test.sh 2>&1 | tee -a "$LOG_FILE"
    SMOKE_EXIT_CODE=${PIPESTATUS[0]}
    set -e  # Re-enable exit on error
    if [ $SMOKE_EXIT_CODE -eq 0 ]; then
        log "${GREEN}✓ Smoke test passed${NC}"
    else
        log "${RED}✗ Smoke test failed with exit code $SMOKE_EXIT_CODE${NC}"
        exit 1
    fi
else
    log "${YELLOW}⚠ Smoke test script not found, skipping${NC}"
    exit 1
fi

# Phase 3: API Tests
log_section "Phase 3: API Unit Tests"
log "Running API tests..."
# Tests are copied to /app/tests in the container
set +e  # Temporarily disable exit on error to capture exit code
docker compose -f infra/docker-compose.yml exec -T api python -m pytest tests -v 2>&1 | tee -a "$LOG_FILE"
TEST_EXIT_CODE=${PIPESTATUS[0]}
set -e  # Re-enable exit on error
if [ $TEST_EXIT_CODE -eq 0 ]; then
    log "${GREEN}✓ API tests passed${NC}"
else
    log "${RED}✗ API tests failed with exit code $TEST_EXIT_CODE${NC}"
    exit 1
fi

# Stop prod mode
log "Stopping prod mode..."
docker compose -f infra/docker-compose.yml down 2>&1 | tee -a "$LOG_FILE"

# Summary
log_section "Validation Summary"
log "${GREEN}✓ All validation phases completed${NC}"
log "Log file saved to: $LOG_FILE"
log "Validation completed successfully!"
