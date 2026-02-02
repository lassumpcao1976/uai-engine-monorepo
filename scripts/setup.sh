#!/bin/bash

set -e

echo "🚀 Setting up UAI Engine..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    npm install -g pnpm
fi

# Install dependencies
echo "📦 Installing dependencies..."
pnpm install

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database
DATABASE_URL=postgresql://uai:uai_password@localhost:5432/uai_engine
POSTGRES_USER=uai
POSTGRES_PASSWORD=uai_password
POSTGRES_DB=uai_engine

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_SECRET_KEY=change-me-in-production-min-32-chars
API_ALGORITHM=HS256
API_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Runner
RUNNER_DOCKER_SOCKET=/var/run/docker.sock
RUNNER_WORK_DIR=/tmp/uai-builds

# Credits
CREDITS_PER_BUILD=10
CREDITS_PER_EXPORT=50
INITIAL_CREDITS=1000

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
EOF
fi

# Start Docker Compose
echo "🐳 Starting Docker Compose services..."
cd infra
docker-compose up -d postgres redis prometheus grafana

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Run migrations
echo "🗄️  Running database migrations..."
cd ../apps/api
python -m pip install -q -r requirements.txt || pip install -q -r requirements.txt
alembic upgrade head

echo "✅ Setup complete!"
echo ""
echo "📋 Services:"
echo "  - Web: http://localhost:3000"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3001 (admin/admin)"
echo ""
echo "🚀 To start all services, run: docker-compose -f infra/docker-compose.yml up"
