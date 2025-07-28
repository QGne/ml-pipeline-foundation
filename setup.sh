#!/bin/bash

echo "🔧 Setting up ML Pipeline Cloud Project..."

# Make all shell scripts executable
echo "📝 Making scripts executable..."
chmod +x docker/run-api.sh
chmod +x docker/run-tests.sh
chmod +x docker/run-cloud-stack.sh
chmod +x docker/run-cloud-tests.sh
chmod +x scripts/test_api.sh
chmod +x scripts/test_endpoints.py

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p scripts
mkdir -p test-results

# Copy environment file if not exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file..."
    cp .env.example .env
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Run the cloud stack: ./docker/run-cloud-stack.sh"
echo "2. Run the tests: ./docker/run-cloud-tests.sh"
echo "3. Test endpoints: python scripts/test_endpoints.py"