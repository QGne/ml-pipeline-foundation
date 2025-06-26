#!/bin/bash

echo "🚀 Starting ML REST API Server..."

# Build the API Docker image
docker build -f docker/Dockerfile.api -t ml-api:latest .

# Run the API container
echo "📡 API will be available at http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"

docker run -it --rm \
    -p 5000:5000 \
    --name ml-api-server \
    ml-api:latest
