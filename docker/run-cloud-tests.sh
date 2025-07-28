#!/bin/bash

echo "🧪 Running ML Cloud Integration Tests..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Create test results directory
mkdir -p test-results

# Stop any existing test containers
echo "🛑 Cleaning up test environment..."
docker-compose -f docker-compose.test.yml down

# Run tests
echo "📦 Starting LocalStack and running tests..."
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test-runner

# Capture exit code
EXIT_CODE=$?

# Clean up
echo "🧹 Cleaning up..."
docker-compose -f docker-compose.test.yml down

# Display results
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed with exit code: $EXIT_CODE"
fi

# Exit with the test exit code
exit $EXIT_CODE