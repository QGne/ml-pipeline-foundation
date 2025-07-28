#!/bin/bash

echo "🚀 🤡 Starting ML Cloud Stack (LocalStack + API)..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Start the stack
echo "📦 Starting LocalStack and ML API..."
docker-compose up --build

# This will run until manually stopped with Ctrl+C