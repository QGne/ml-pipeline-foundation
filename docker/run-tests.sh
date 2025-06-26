#!/bin/bash

echo "🧪 Running ML API Tests in Docker..."

# Build the test Docker image
docker build -f docker/Dockerfile.test -t ml-api-tests:latest .

# Run tests and capture exit code
docker run --rm \
    --name ml-api-tests \
    ml-api-tests:latest

# Get exit code from docker run
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed!"
fi

exit $EXIT_CODE
