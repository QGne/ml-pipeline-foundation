
import pytest
import json
import time
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.cloud_api import app
from src.cloud import DynamoDBClient, S3Client


@pytest.fixture
def client():
    # Create test client
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def cloud_clients():
    # Create cloud clients for verification
    dynamodb = DynamoDBClient()
    s3 = S3Client()
    return dynamodb, s3


@pytest.fixture(autouse=True)
def cleanup(cloud_clients):
    # Clean up test data before and after tests
    dynamodb, s3 = cloud_clients
    
    # Clean up before test
    cleanup_test_data(dynamodb, s3)
    
    yield
    
    # Clean up after test
    cleanup_test_data(dynamodb, s3)


def cleanup_test_data(dynamodb, s3):
    # Helper to clean up test data
    try:
        # Clean up test models from DynamoDB
        models = dynamodb.list_models()
        for model in models:
            if model['model_id'].startswith('test_'):
                try:
                    dynamodb.delete_model(model['model_id'])
                except:
                    pass
        
        # Clean up test models from S3
        s3_models = s3.list_models()
        for model_id in s3_models:
            if model_id.startswith('test_'):
                try:
                    s3.delete_model(model_id)
                except:
                    pass
    except:
        pass


class TestCloudAPIEndpoints:
    # Test all Cloud API endpoints
    
    def test_health_check(self, client):
        # Test health endpoint

        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'services' in data
        assert data['services']['dynamodb'] == 'connected'
        assert data['services']['s3'] == 'connected'
    
    def test_get_models_with_parameters(self, client, cloud_clients):
        #Test GET /models with appropriate parameters, returns expected JSON
        dynamodb, s3 = cloud_clients
        
        # Create test model first
        model_id = 'test_model_1'
        client.post('/models', json={
            'model_id': model_id,
            'model_type': 'RandomForest',
            'data_path': 'data/iris_simple.csv'
        })
        
        # Query with valid parameters
        response = client.get('/models?model_id=' + model_id)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['model_id'] == model_id
        assert data['model_type'] == 'RandomForest'
    
    def test_get_models_no_results(self, client):
        # Test GET /models that finds no results
        response = client.get('/models?model_type=NonExistent')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'No models found matching criteria'
        assert data['results'] == []
    
    def test_get_models_no_parameters(self, client):
        # Test GET /models with no parameters
        response = client.get('/models')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No query parameters provided' in data['error']
        assert 'available_filters' in data
    
    def test_get_models_incorrect_parameters(self, client):
        # Test GET /models with incorrect parameters
        response = client.get('/models?invalid_param=value&another_bad=test')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid query parameters' in data['error']
        assert 'invalid_parameters' in data
        assert 'invalid_param' in data['invalid_parameters']
        assert 'another_bad' in data['invalid_parameters']
    
    def test_post_model_creates_in_both_stores(self, client, cloud_clients):
        # Test POST /models creates item in DynamoDB and S3
        dynamodb, s3 = cloud_clients
        
        model_id = 'test_model_2'
        response = client.post('/models', json={
            'model_id': model_id,
            'model_type': 'RandomForest',
            'description': 'Test model for integration',
            'data_path': 'data/iris_simple.csv'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['model_id'] == model_id
        assert 'dynamodb_item' in data
        assert 's3_key' in data
        
        # Verify in DynamoDB
        db_model = dynamodb.get_model(model_id)
        assert db_model is not None
        assert db_model['model_id'] == model_id
        assert db_model['model_type'] == 'RandomForest'
        assert db_model['description'] == 'Test model for integration'
        
        # Verify in S3
        s3_model = s3.download_model(model_id)
        assert s3_model is not None
        
        s3_metadata = s3.get_model_metadata(model_id)
        assert s3_metadata is not None
        assert s3_metadata['model_type'] == 'RandomForest'
    
    def test_post_duplicate_model(self, client):
        # Test duplicate POST request returns appropriate response
        model_id = 'test_model_3'
        
        # First POST
        response1 = client.post('/models', json={
            'model_id': model_id,
            'data_path': 'data/iris_simple.csv'
        })
        assert response1.status_code == 201
        
        # Duplicate POST
        response2 = client.post('/models', json={
            'model_id': model_id,
            'data_path': 'data/iris_simple.csv'
        })
        assert response2.status_code == 409
        data = json.loads(response2.data)
        assert 'error' in data
        assert 'Duplicate model ID' in data['error']
    
    def test_put_existing_model_updates_both_stores(self, client, cloud_clients):
        # Test PUT /models/<id> updates both DynamoDB and S3
        dynamodb, s3 = cloud_clients
        model_id = 'test_model_4'
        
        # Create model first
        client.post('/models', json={
            'model_id': model_id,
            'model_type': 'RandomForest',
            'version': '1.0',
            'data_path': 'data/iris_simple.csv'
        })
        
        # Update model
        response = client.put(f'/models/{model_id}', json={
            'version': '2.0',
            'notes': 'Updated version',
            'retrain': False
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['model_id'] == model_id
        
        # Verify updates in DynamoDB
        db_model = dynamodb.get_model(model_id)
        assert db_model['version'] == '2.0'
        assert db_model['notes'] == 'Updated version'
        
        # Verify metadata update in S3
        s3_metadata = s3.get_model_metadata(model_id)
        assert s3_metadata['version'] == '2.0'
    
    def test_put_nonexistent_model(self, client):
        # Test PUT request with no valid target
        response = client.put('/models/nonexistent_model', json={
            'version': '2.0'
        })
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Model not found' in data['error']
    
    def test_delete_model_removes_from_both_stores(self, client, cloud_clients):
        # Test DELETE removes from both DynamoDB and S3
        dynamodb, s3 = cloud_clients
        model_id = 'test_model_5'
        
        # Create model first
        client.post('/models', json={
            'model_id': model_id,
            'data_path': 'data/iris_simple.csv'
        })
        
        # Verify it exists
        assert dynamodb.get_model(model_id) is not None
        assert s3.model_exists(model_id) is True
        
        # Delete model
        response = client.delete(f'/models/{model_id}')
        assert response.status_code == 200
        
        # Verify removal from DynamoDB
        assert dynamodb.get_model(model_id) is None
        
        # Verify removal from S3
        assert s3.model_exists(model_id) is False
    
    def test_delete_nonexistent_model(self, client):
        # Test DELETE request with no valid target
        response = client.delete('/models/nonexistent_model')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Model not found' in data['error']
    
    def test_predict_with_model(self, client):
        # Test predictions using a stored model
        model_id = 'test_model_6'
        
        # Create and train model
        response = client.post('/models', json={
            'model_id': model_id,
            'data_path': 'data/iris_simple.csv'
        })
        assert response.status_code == 201
        
        # Get predictions
        response = client.get(f'/models/{model_id}/predict')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'predictions' in data
        assert 'actual' in data
        assert 'accuracy' in data
        assert len(data['predictions']) > 0
        assert 0 <= data['accuracy'] <= 1
    
    def test_full_workflow(self, client, cloud_clients):
        # Test complete workflow with data consistency
        dynamodb, s3 = cloud_clients
        model_id = 'test_workflow_model'
        
        #####  create model
        create_response = client.post('/models', json={
            'model_id': model_id,
            'model_type': 'RandomForest',
            'experiment': 'workflow_test',
            'data_path': 'data/iris_simple.csv'
        })
        assert create_response.status_code == 201
        
        #####  Verify data consistency
        db_model = dynamodb.get_model(model_id)
        s3_metadata = s3.get_model_metadata(model_id)
        
        # Check matching metadata
        assert db_model['model_type'] == s3_metadata['model_type']
        assert db_model['experiment'] == s3_metadata['experiment']
        assert db_model['train_accuracy'] == s3_metadata['train_accuracy']
        
        ####  Update model
        update_response = client.put(f'/models/{model_id}', json={
            'version': '2.0',
            'updated_by': 'test_suite'
        })
        assert update_response.status_code == 200
        
        #### Verify updates are consistent
        db_model_updated = dynamodb.get_model(model_id)
        s3_metadata_updated = s3.get_model_metadata(model_id)
        
        assert db_model_updated['version'] == '2.0'
        assert s3_metadata_updated['version'] == '2.0'
        assert db_model_updated['updated_by'] == 'test_suite'
        
        ###### Get predictions
        predict_response = client.get(f'/models/{model_id}/predict')
        assert predict_response.status_code == 200
        
        ###### Delete model
        delete_response = client.delete(f'/models/{model_id}')
        assert delete_response.status_code == 200
        
        ##### Verify complete deletion
        assert dynamodb.get_model(model_id) is None
        assert s3.model_exists(model_id) is False