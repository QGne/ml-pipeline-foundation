#!/bin/bash

echo "🚀 Starting ML REST API Server..."

# Build the API Docker image
docker build -f docker/Dockerfile.api -t ml-api:latest .

# Run the API container
echo "📡 API will be available at http://localhost:5001"
echo "🛑 Press Ctrl+C to stop the server"

docker run -it --rm \
    -p 5001:5001 \
    --name ml-api-server \
    ml-api:latest
