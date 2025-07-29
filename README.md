# ML Pipeline Foundation with Cloud Integration

Simple ML pipeline foundation for future implementation

# For CI/CL pipline part II

## Project Structure

```
ml-pipeline-foundation/
├── .github/workflows/
│   ├── cloud-ci.yml         # Cloud integration CI/CD (ENABLED)
│   ├── docker-ci.yml        # Docker CI/CD (ENABLED)
│   └── ci.yml.disabled      # ML Pipeline CI (DISABLED)
├── docker/
│   ├── Dockerfile.api       # API server container
│   ├── Dockerfile.cloud-api # Cloud API container
│   ├── Dockerfile.cloud-test # Cloud test container
│   ├── Dockerfile.test      # Test runner container
│   ├── run-api.sh          # Shell script for API
│   ├── run-cloud-stack.sh  # Shell script for cloud stack
│   ├── run-cloud-tests.sh  # Shell script for cloud tests
│   └── run-tests.sh        # Shell script for tests
├── src/
│   ├── __init__.py
│   ├── data_processor.py    # Core ML functionality
│   ├── api.py              # Basic REST API server
│   ├── cloud_api.py        # Cloud-integrated API server
│   └── cloud/
│       ├── __init__.py
│       ├── dynamodb_client.py # DynamoDB operations
│       └── s3_client.py       # S3 operations
├── tests/
│   ├── __init__.py
│   ├── test_data_processor.py  # ML pipeline tests
│   ├── test_api.py            # Basic API tests
│   └── test_cloud_api.py      # Cloud API integration tests
├── data/
│   └── iris_simple.csv
├── docker-compose.yml         # Production stack (LocalStack  API)
├── docker-compose.test.yml    # Test stack (LocalStack  Test Runner)
├── requirements.txt           # Basic dependencies, also covers the cloud dependencies
├── requirements-cloud.txt     # Cloud dependencies
└── README.md
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.10
- Git

### 1. Clone and Setup
```bash
git clone https://github.com/QGne/ml-pipeline-foundation.git
cd ml-pipeline-foundation
```

### 2. Run the Cloud Stack
```bash
# Start the complete stack (LocalStack  ML API)
./docker/run-cloud-stack.sh
```

This will:
- Start LocalStack (AWS mock) on port 4566
- Start the ML API server on port 5001
- Create DynamoDB table and S3 bucket automatically
- Run until manually stopped (CtrlC)

### 3. Test the API
```bash
# Health check
curl http://localhost:5001/health

# Create a model
curl -X POST http://localhost:5001/models \
  -H "Content-Type: application/json" \
  -d '{"model_id": "my-model", "data_path": "data/iris_simple.csv"}'

# Get model
curl http://localhost:5001/models?model_id=my-model

# Update model
curl -X PUT http://localhost:5001/models/my-model \
  -H "Content-Type: application/json" \
  -d '{"version": "2.0", "notes": "Updated model"}'

# Delete model
curl -X DELETE http://localhost:5001/models/my-model
```

## Running Tests

### Run All Cloud Integration Tests
```bash
# Run tests and exit with proper status code
./docker/run-cloud-tests.sh
```

This will:
- Start LocalStack and test environment
- Run comprehensive test suite
- Exit with 0 if all tests pass, non-zero if any fail
- Clean up containers automatically

### Test Coverage
The test suite covers all required scenarios:

**GET Endpoints:**
- With appropriate parameters returns expected JSON
- With no results returns appropriate response
- With no parameters returns appropriate response
- With incorrect parameters returns appropriate response

**POST Endpoints:**
- Creates items in both DynamoDB and S3
- Handles duplicate requests appropriately

**PUT Endpoints:**
- Updates existing resources in both DynamoDB and S3
- Handles non-existent targets appropriately

**DELETE Endpoints:**
- Removes items from both DynamoDB and S3
- Handles non-existent targets appropriately

**Data Consistency:**
- Database items and S3 objects match for all operations

##  API Endpoints

### Health Check
```bash
GET /health
```
Returns service status and cloud connectivity information.

### Models Management

#### Create Model
```bash
POST /models
Content-Type: application/json

{
  "model_id": "unique-model-id",
  "model_type": "RandomForest",
  "data_path": "data/iris_simple.csv",
  "description": "Optional description"
}
```

#### Get Models
```bash
# Get specific model
GET /models?model_id=my-model

# Query with filters
GET /models?model_type=RandomForest&accuracy_threshold=0.8
```

#### Update Model
```bash
PUT /models/{model_id}
Content-Type: application/json

{
  "version": "2.0",
  "notes": "Updated notes",
  "retrain": false
}
```

#### Delete Model
```bash
DELETE /models/{model_id}
```

#### Predict with Model
```bash
GET /models/{model_id}/predict?data_path=data/iris_simple.csv
```

## Docker Compose Files

### Production Stack (`docker-compose.yml`)
- **LocalStack**: AWS services mock (S3, DynamoDB)
- **ML API**: Flask application with cloud integration
- Runs continuously until manually stopped

### Test Stack (`docker-compose.test.yml`)
- **LocalStack**: AWS services mock
- **Test Runner**: Automated test execution
- Exits with proper status codes (0 for success, non-zero for failure)

## 🔄 CI/CD Workflows

### Cloud Integration CI/CD (`cloud-ci.yml`)
- Runs on push/PR to main/develop branches
- Tests cloud integration with LocalStack
- Validates API endpoints and data consistency
- **Status**: ✅ ENABLED

### Docker CI/CD (`docker-ci.yml`)
- Tests Docker builds and container functionality
- Validates API container startup and health checks
- **Status**: ✅ ENABLED

### ML Pipeline CI (`ci.yml`)
- Basic ML pipeline testing
- **Status**: ❌ DISABLED (renamed to `ci.yml.disabled`)

## 📊 Data Flow

### Model Creation Flow
1. **POST /models** receives JSON request
2. **DataProcessor** loads and processes data
3. **Model** is trained and evaluated
4. **DynamoDB** stores model metadata
5. **S3** stores model artifact and metadata
6. **Response** includes both DynamoDB item and S3 key

### Model Retrieval Flow
1. **GET /models** with query parameters
2. **DynamoDB** queries for matching models
3. **Response** includes filtered results

### Model Update Flow
1. **PUT /models/{id}** receives update data
2. **DynamoDB** updates model metadata
3. **S3** updates model metadata
4. **Response** confirms updates

### Model Deletion Flow
1. **DELETE /models/{id}** receives delete request
2. **DynamoDB** removes model entry
3. **S3** removes model artifacts
4. **Response** confirms deletion

## 🛠️ Development

### Local Development Setup
```bash
# Create virtual environment
python3 -m venv ml-env
source ml-env/bin/activate  # On Windows: ml-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-cloud.txt

# Run tests locally
pytest tests/ -v

# Run API locally (requires LocalStack)
python -m src.cloud_api
```

### Environment Variables
```bash
# LocalStack configuration
AWS_ENDPOINT_URL=http://localhost:4566
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
```

## API Response Examples

### Successful Model Creation
```json
{
  "message": "Model created successfully",
  "model_id": "my-model",
  "dynamodb_item": {
    "model_id": "my-model",
    "model_type": "RandomForest",
    "train_accuracy": 0.95,
    "test_accuracy": 0.93,
    "created_at": "2023-12-01T10:00:00"
  },
  "s3_key": "models/my-model/model.pkl",
  "metadata": {
    "model_type": "RandomForest",
    "train_accuracy": 0.95,
    "test_accuracy": 0.93
  }
}
```

### Error Response
```json
{
  "error": "Model not found",
  "message": "No model with ID nonexistent-model"
}
```

## Troubleshooting

### LocalStack Connection Issues
```bash
# Check LocalStack health
curl http://localhost:4566/_localstack/health

# Verify DynamoDB table
aws dynamodb list-tables --endpoint-url http://localhost:4566

# Verify S3 bucket
aws s3 ls --endpoint-url http://localhost:4566
```

### Docker Issues
```bash
# Clean up containers
docker-compose down

# Rebuild images
docker-compose build --no-cache

# Check logs
docker-compose logs
```
## AI Use Statement:
During the development of this assignment, I used a large language model (LLM) as a supportive tool for verifying syntax, understanding documentation, and refining debugging steps. All design decisions and implementation were my own.