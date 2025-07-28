#!/bin/bash

echo "🚀 Starting ML Cloud Stack (LocalStack + API)..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Detect docker compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Neither 'docker-compose' nor 'docker compose' found!"
    exit 1
fi

echo "Using: $DOCKER_COMPOSE"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
$DOCKER_COMPOSE down

# Start the stack
echo "📦 Starting LocalStack and ML API..."
$DOCKER_COMPOSE up --build

# This will run until manually stopped with Ctrl+C