#!/bin/bash

set -e

echo "🚀 Starting UAI Engine..."

cd "$(dirname "$0")/../infra"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start all services
docker-compose up
