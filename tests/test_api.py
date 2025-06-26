"""
Tests for the REST API endpoints
"""

import pytest
import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestAPIEndpoints:
    """Test all API endpoints"""
    
    def test_health_check_get(self, client):
        """Test GET /health endpoint"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'model_trained' in data
    
    def test_train_model_post(self, client):
        """Test POST /train endpoint"""
        # Test with default data
        response = client.post('/train', 
                             json={'data_path': 'data/iris_simple.csv'},
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'train_accuracy' in data
        assert 'test_accuracy' in data
        assert data['training_samples'] > 0
        assert data['test_samples'] > 0
        assert 0 <= data['train_accuracy'] <= 1
        assert 0 <= data['test_accuracy'] <= 1
    
    def test_train_model_post_missing_file(self, client):
        """Test POST /train with missing data file"""
        response = client.post('/train',
                             json={'data_path': 'nonexistent.csv'},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_predict_get_without_training(self, client):
        """Test GET /predict before training model"""
        response = client.get('/predict')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not trained' in data['error'].lower()
    
    def test_predict_get_after_training(self, client):
        """Test GET /predict after training model"""
        # First train the model
        train_response = client.post('/train',
                                   json={'data_path': 'data/iris_simple.csv'},
                                   content_type='application/json')
        assert train_response.status_code == 201
        
        # Then get predictions
        response = client.get('/predict')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'predictions' in data
        assert 'actual' in data
        assert len(data['predictions']) > 0
        assert len(data['actual']) > 0
    
    def test_update_model_config_put(self, client):
        """Test PUT /model endpoint"""
        config = {
            'n_estimators': 20,
            'random_state': 123
        }
        
        response = client.put('/model',
                            json=config,
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'config' in data
        assert data['config']['n_estimators'] == 20
        assert data['config']['random_state'] == 123
    
    def test_update_model_config_put_empty(self, client):
        """Test PUT /model with empty config"""
        response = client.put('/model',
                            json={},
                            content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_reset_model_delete(self, client):
        """Test DELETE /model endpoint"""
        response = client.delete('/model')
        
        assert response.status_code == 204
        # 204 responses don't have content
    
    def test_not_found_endpoint(self, client):
        """Test 404 for non-existent endpoint"""
        response = client.get('/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'available_endpoints' in data
    
    def test_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method"""
        response = client.patch('/health')  # PATCH not allowed
        
        assert response.status_code == 405
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_full_workflow(self, client):
        """Test complete API workflow"""
        # 1. Check health
        health_response = client.get('/health')
        assert health_response.status_code == 200
        
        # 2. Train model
        train_response = client.post('/train',
                                   json={'data_path': 'data/iris_simple.csv'},
                                   content_type='application/json')
        assert train_response.status_code == 201
        
        # 3. Get predictions
        predict_response = client.get('/predict')
        assert predict_response.status_code == 200
        
        # 4. Update config
        config_response = client.put('/model',
                                   json={'n_estimators': 15},
                                   content_type='application/json')
        assert config_response.status_code == 200
        
        # 5. Reset model
        reset_response = client.delete('/model')
        assert reset_response.status_code == 204
        
        # 6. Verify model is reset
        predict_after_reset = client.get('/predict')
        assert predict_after_reset.status_code == 400  # Model not trained
