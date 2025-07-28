#!/bin/bash

echo "🧪 Running ML Cloud Integration Tests..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Create test results directory
mkdir -p test-results

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

# Stop any existing test containers
echo "🛑 Cleaning up test environment..."
$DOCKER_COMPOSE -f docker-compose.test.yml down

# Run tests
echo "📦 Starting LocalStack and running tests..."
$DOCKER_COMPOSE -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test-runner

# Capture exit code
EXIT_CODE=$?

# Clean up
echo "🧹 Cleaning up..."
$DOCKER_COMPOSE -f docker-compose.test.yml down

# Display results
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed with exit code: $EXIT_CODE"
fi

# Exit with the test exit code
exit $EXIT_CODE