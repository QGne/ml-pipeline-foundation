#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:5001"

echo -e "${BLUE}🧪 Testing ML Cloud API Endpoints${NC}\n"

# Test health
echo -e "${BLUE}1. Testing Health Endpoint${NC}"
curl -s "$BASE_URL/health" | python -m json.tool
echo -e "\n"

# Test GET without parameters (should fail)
echo -e "${BLUE}2. Testing GET /models without parameters (should return 400)${NC}"
curl -s "$BASE_URL/models" | python -m json.tool
echo -e "\n"

# Test GET with invalid parameters (should fail)
echo -e "${BLUE}3. Testing GET /models with invalid parameters (should return 400)${NC}"
curl -s "$BASE_URL/models?wrong_param=value" | python -m json.tool
echo -e "\n"

# Create a test model
MODEL_ID="test_model_$(date +%s)"
echo -e "${BLUE}4. Creating model: $MODEL_ID${NC}"
curl -s -X POST "$BASE_URL/models" \
  -H "Content-Type: application/json" \
  -d "{\"model_id\": \"$MODEL_ID\", \"model_type\": \"RandomForest\", \"data_path\": \"data/iris_simple.csv\"}" \
  | python -m json.tool
echo -e "\n"

# Test duplicate creation (should fail)
echo -e "${BLUE}5. Testing duplicate model creation (should return 409)${NC}"
curl -s -X POST "$BASE_URL/models" \
  -H "Content-Type: application/json" \
  -d "{\"model_id\": \"$MODEL_ID\", \"data_path\": \"data/iris_simple.csv\"}" \
  | python -m json.tool
echo -e "\n"

# Get the model
echo -e "${BLUE}6. Getting model by ID${NC}"
curl -s "$BASE_URL/models?model_id=$MODEL_ID" | python -m json.tool
echo -e "\n"

# Update the model
echo -e "${BLUE}7. Updating model${NC}"
curl -s -X PUT "$BASE_URL/models/$MODEL_ID" \
  -H "Content-Type: application/json" \
  -d "{\"version\": \"2.0\", \"notes\": \"Updated via shell script\"}" \
  | python -m json.tool
echo -e "\n"

# Get predictions
echo -e "${BLUE}8. Getting predictions${NC}"
curl -s "$BASE_URL/models/$MODEL_ID/predict" | python -m json.tool
echo -e "\n"

# Delete the model
echo -e "${BLUE}9. Deleting model${NC}"
curl -s -X DELETE "$BASE_URL/models/$MODEL_ID" | python -m json.tool
echo -e "\n"

# Try to delete non-existent model (should fail)
echo -e "${BLUE}10. Deleting non-existent model (should return 404)${NC}"
curl -s -X DELETE "$BASE_URL/models/nonexistent_model_xyz" | python -m json.tool
echo -e "\n"

echo -e "${GREEN}✅ Test script completed!${NC}"