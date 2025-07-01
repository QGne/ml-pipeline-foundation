# ml-pipeline-foundation
Simple ML pipeline foundation for future implementation

# For CI/CL pipline part II

### Current project structure 

```bash
ml-pipeline-foundation/
├── .github/workflows/
│   ├── ci.yml               # Original workflow
│   └── docker-ci.yml        # Docker workflow
├── docker/
│   ├── Dockerfile.api       # API server container
│   ├── Dockerfile.test      # Test runner container
│   ├── run-api.sh          # Shell script for API
│   └── run-tests.sh        # Shell script for tests
├── src/
│   ├── __init__.py
│   ├── data_processor.py    # Core ML functionality
│   └── api.py              # REST API server
├── tests/
│   ├── __init__.py
│   ├── test_data_processor.py  # ML pipeline tests
│   └── test_api.py            # API endpoint tests
├── data/
│   └── iris_simple.csv
├── requirements.txt         # Updated with Flask
└── README.md
```

### Installation & Setup(MAC
```bash
# 1. Clone the repository
git clone https://github.com/QGne/ml-pipeline-foundation.git
cd ml-pipeline-foundation

# 2. Create virtual environment
python3 -m venv ml-env
source ml-env/bin/activate

# 3. Install dependencies (includes Flask for API)
pip install -r requirements.txt
```

### Complete Pipline Test

#### Test Locally (Before Docker)

```bash
# Run API server
python -m src.api

# In another terminal, test endpoints:
curl http://localhost:5001/health
curl -X POST http://localhost:5001/train \
  -H "Content-Type: application/json" \
  -d '{"data_path": "data/iris_simple.csv"}'
curl http://localhost:5001/predict

```

#### Shell Scripts for API Testings
### Test POST endpoint (Training):
```bash
cat > test_post.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing POST /train endpoint..."

# Test training with valid data
echo "Testing with valid data..."
response=$(curl -s -X POST http://localhost:5001/train \
  -H "Content-Type: application/json" \
  -d '{"data_path": "data/iris_simple.csv"}')

echo "Response: $response"

# Check if training was successful
if echo "$response" | grep -q "Model trained successfully"; then
    echo "✅ POST /train test PASSED"
else
    echo "❌ POST /train test FAILED"
fi
EOF

chmod +x test_post.sh
./test_post.sh
rm test_post.sh
```

### Test PUT endpoint (Model Configuration):
```bash
cat > test_put.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing PUT /model endpoint..."

# Test updating model configuration
echo "Updating model configuration..."
response=$(curl -s -X PUT http://localhost:5001/model \
  -H "Content-Type: application/json" \
  -d '{"n_estimators": 50, "random_state": 42}')

echo "Response: $response"

# Check if configuration was updated
if echo "$response" | grep -q "Model configuration updated"; then
    echo "✅ PUT /model test PASSED"
else
    echo "❌ PUT /model test FAILED"
fi
EOF

chmod +x test_put.sh
./test_put.sh
rm test_put.sh
```

### Test DELETE endpoint (Model Reset):
```bash
cat > test_delete.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing DELETE /model endpoint..."

# Test resetting the model
echo "Resetting model..."
response=$(curl -s -X DELETE http://localhost:5001/model -w "HTTP_CODE:%{http_code}")

echo "Response: $response"

# Check if reset was successful (HTTP 204)
if echo "$response" | grep -q "HTTP_CODE:204"; then
    echo "✅ DELETE /model test PASSED"
else
    echo "❌ DELETE /model test FAILED"
fi
EOF

chmod +x test_delete.sh
./test_delete.sh
rm test_delete.sh
```

#### Test with Docker

```bash
# Run tests in Docker
./docker/run-tests.sh

# Run API server in Docker
./docker/run-api.sh
```

### Unit Tests
#### Run Core ML Tests
```bash
pytest tests/test_data_processor.py -v

# Expected output:
# ===== 5 passed in X.XXs =====
```

#### Run API Tests
```bash

# Test REST API endpoints
pytest tests/test_api.py -v

# Expected: 11 passed
```
#### Run All Tests
```bash
# Complete test suite
pytest tests/ -v

# Expected: 16 passed
```

# For previous CI/CL pipline

### project structure 
```bash
ml-pipeline-foundation/
├── .github/workflows/
│   └── ci.yml              # GitHub Actions CI/CD pipeline
├── src/
│   ├── init.py
│   └── data_processor.py   # Main ML pipeline implementation
├── tests/
│   ├── init.py
│   └── test_data_processor.py  # Unit tests
├── data/
│   └── iris_simple.csv     # Sample dataset
├── requirements.txt        # Python dependencies
└── README.md
```

### Installation & Setup(MAC
```bash

# 1. Clone the repository
git clone https://github.com/QGne/ml-pipeline-foundation.git
cd ml-pipline-foundation

# 2. Create virtual environment
python3 -m venv ml-env
source ml-env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Complete Pipline Test
```bash
cat > pipeline_test.py << 'EOF'
from src.data_processor import DataProcessor

processor = DataProcessor()
data = processor.load_data('data/iris_simple.csv')
clean_data = processor.clean_data(data)
X, y = processor.split_features_target(clean_data)
X_train, X_test, y_train, y_test = processor.prepare_data(X, y)

train_acc = processor.train_model(X_train, y_train)
test_acc = processor.evaluate_model(X_test, y_test)

print(f'Training accuracy: {train_acc:.3f}')
print(f'Test accuracy: {test_acc:.3f}')
print('✅ Pipeline completed successfully!')
EOF

python pipeline_test.py
rm pipeline_test.py
```

### Unit Tests
```bash

pytest tests/ -v

# Expected output:
# ===== 5 passed in X.XXs =====
