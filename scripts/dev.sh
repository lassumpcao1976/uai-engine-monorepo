#!/bin/bash

set -e

echo "🚀 Starting UAI Engine in development mode..."

cd infra
docker-compose up -d postgres redis prometheus grafana

echo "⏳ Waiting for services to be ready..."
sleep 5

# Start services in background
echo "📦 Starting API..."
cd ../apps/api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "🏃 Starting Runner..."
cd ../runner
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &
RUNNER_PID=$!

echo "🌐 Starting Web..."
cd ../web
pnpm dev &
WEB_PID=$!

echo "✅ All services started!"
echo ""
echo "📋 Services:"
echo "  - Web: http://localhost:3000"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Runner: http://localhost:8001"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $API_PID $RUNNER_PID $WEB_PID; exit" INT TERM
wait
