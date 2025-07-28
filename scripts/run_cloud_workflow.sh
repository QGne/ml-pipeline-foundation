#!/bin/bash

# Cloud Integration Workflow Test Script
# This script helps run the cloud integration tests similar to the GitHub workflow

set -e

echo "🚀 Starting Cloud Integration Workflow Test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_warning "docker-compose not found, trying 'docker compose'"
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Make scripts executable
print_status "Making scripts executable..."
chmod +x scripts/*.sh 2>/dev/null || true

# Run Cloud Integration Tests
print_status "Running Cloud Integration Tests..."
if [ -f "docker/run-cloud-tests.sh" ]; then
    ./docker/run-cloud-tests.sh
elif [ -f "docker-compose.test.yml" ]; then
    $DOCKER_COMPOSE -f docker-compose.test.yml up --build --abort-on-container-exit
else
    print_error "No cloud test script found"
    exit 1
fi

# Check test results
if [ $? -eq 0 ]; then
    print_status "✅ Cloud Integration Tests passed!"
else
    print_error "❌ Cloud Integration Tests failed!"
    exit 1
fi

# Optional: Run API validation tests
print_status "Running API validation tests..."
if [ -f "docker-compose.yml" ]; then
    print_status "Starting cloud stack..."
    $DOCKER_COMPOSE up -d
    
    print_status "Waiting for services to be ready..."
    sleep 20
    
    print_status "Testing API health endpoint..."
    if curl -f http://localhost:5001/health; then
        print_status "✅ API health check passed"
    else
        print_error "❌ API health check failed"
        $DOCKER_COMPOSE down
        exit 1
    fi
    
    print_status "Testing model creation..."
    if curl -X POST http://localhost:5001/models \
        -H "Content-Type: application/json" \
        -d '{"model_id": "workflow-test-model", "data_path": "data/iris_simple.csv"}' \
        -f; then
        print_status "✅ Model creation test passed"
    else
        print_error "❌ Model creation test failed"
        $DOCKER_COMPOSE down
        exit 1
    fi
    
    print_status "Cleaning up..."
    $DOCKER_COMPOSE down
else
    print_warning "No docker-compose.yml found, skipping API validation"
fi

print_status "🎉 Cloud Integration Workflow Test completed successfully!"