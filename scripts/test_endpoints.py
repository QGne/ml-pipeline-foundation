#!/usr/bin/env python3


import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:5001"

#quick tests for api all
def test_health():
    #Test health endpoint
    print("\n🏥 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_get_models_no_params():
    #Test GET models without parameters
    print("\n📋 Testing GET /models without parameters...")
    response = requests.get(f"{BASE_URL}/models")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 400

def test_get_models_invalid_params():
    #Test GET models with invalid parameters
    print("\n❌ Testing GET /models with invalid parameters...")
    response = requests.get(f"{BASE_URL}/models?invalid=test&bad_param=value")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 400

def test_create_model():
    #Test model creation
    print("\n🚀 Testing POST /models...")
    model_id = f"test_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    data = {
        "model_id": model_id,
        "model_type": "RandomForest",
        "description": "Test model from endpoint script",
        "data_path": "data/iris_simple.csv"
    }
    
    response = requests.post(f"{BASE_URL}/models", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        return model_id
    return None

def test_duplicate_create(model_id):
    # test duplicate model creation
    print("\n🔄 Testing duplicate POST /models...")
    data = {
        "model_id": model_id,
        "data_path": "data/iris_simple.csv"
    }
    
    response = requests.post(f"{BASE_URL}/models", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 409

def test_get_model(model_id):
    # Test getting specific model
    print(f"\n🔍 Testing GET /models with model_id={model_id}...")
    response = requests.get(f"{BASE_URL}/models?model_id={model_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_update_model(model_id):
    #Test model update 
    print(f"\n✏️  Testing PUT /models/{model_id}...")
    data = {
        "version": "2.0",
        "updated_by": "test_script",
        "notes": "Updated via test script"
    }
    
    response = requests.put(f"{BASE_URL}/models/{model_id}", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_predict(model_id):
    # Test model prediction
    print(f"\n🔮 Testing GET /models/{model_id}/predict...")
    response = requests.get(f"{BASE_URL}/models/{model_id}/predict")
    print(f"Status: {response.status_code}")
    data = response.json()
    if 'predictions' in data:
        print(f"Predictions: {data['predictions'][:5]}...")  # Show first 5
        print(f"Accuracy: {data.get('accuracy', 'N/A')}")
    else:
        print(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200

def test_delete_model(model_id):
    # Test model deletion
    print(f"\n🗑️  Testing DELETE /models/{model_id}...")
    response = requests.delete(f"{BASE_URL}/models/{model_id}")
    print(f"Status: {response.status_code}")
    if response.text:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_delete_nonexistent():
    # Test deleting non-existent model
    print("\n❌ Testing DELETE on non-existent model...")
    response = requests.delete(f"{BASE_URL}/models/nonexistent_model_xyz")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 404

def main():
    #Run all tests
    print("🧪 Starting API endpoint tests...")
    print(f"🌐 Base URL: {BASE_URL}")
    
    results = []
    
    # Test health
    results.append(("Health Check", test_health()))
    
    # Test GET errors
    results.append(("GET without params", test_get_models_no_params()))
    results.append(("GET invalid params", test_get_models_invalid_params()))
    
    # Create a model
    model_id = test_create_model()
    if model_id:
        results.append(("Create Model", True))
        
        # Test duplicate
        results.append(("Duplicate Create", test_duplicate_create(model_id)))
        
        # Test get
        results.append(("Get Model", test_get_model(model_id)))
        
        # Test update
        results.append(("Update Model", test_update_model(model_id)))
        
        # Test predict
        results.append(("Predict", test_predict(model_id)))
        
        # Test delete
        results.append(("Delete Model", test_delete_model(model_id)))
    else:
        results.append(("Create Model", False))
    
    # Test delete non-existent
    results.append(("Delete Non-existent", test_delete_nonexistent()))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    print("="*50)
    print(f"Total: {passed}/{total} passed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())