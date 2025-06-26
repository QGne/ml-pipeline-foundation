"""
REST API for ML Pipeline
Serves your existing DataProcessor through HTTP endpoints
"""

from flask import Flask, jsonify, request
import json
import os
from src.data_processor import DataProcessor

app = Flask(__name__)

# Global processor instance
processor = DataProcessor()
model_trained = False
last_training_data = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "ML API is running",
        "model_trained": model_trained
    }), 200

@app.route('/train', methods=['POST'])
def train_model():
    """Train the ML model with provided data or default dataset"""
    global model_trained, last_training_data
    
    try:
        # Load data (using default dataset for simplicity)
        data_path = request.json.get('data_path', 'data/iris_simple.csv')
        
        if not os.path.exists(data_path):
            return jsonify({
                "error": "Data file not found",
                "path": data_path
            }), 400
        
        # Process data and train model
        data = processor.load_data(data_path)
        clean_data = processor.clean_data(data)
        X, y = processor.split_features_target(clean_data)
        X_train, X_test, y_train, y_test = processor.prepare_data(X, y)
        
        # Train model
        train_accuracy = processor.train_model(X_train, y_train)
        test_accuracy = processor.evaluate_model(X_test, y_test)
        
        model_trained = True
        last_training_data = {
            "train_accuracy": float(train_accuracy),
            "test_accuracy": float(test_accuracy),
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
        
        return jsonify({
            "message": "Model trained successfully",
            "train_accuracy": float(train_accuracy),
            "test_accuracy": float(test_accuracy),
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }), 201
        
    except Exception as e:
        return jsonify({
            "error": "Training failed",
            "details": str(e)
        }), 500

@app.route('/predict', methods=['GET'])
def get_predictions():
    """Get model predictions and status"""
    global model_trained, last_training_data
    
    if not model_trained:
        return jsonify({
            "error": "Model not trained yet",
            "message": "Please train the model first using POST /train"
        }), 400
    
    try:
        # Load test data for predictions
        data = processor.load_data('data/iris_simple.csv')
        clean_data = processor.clean_data(data)
        X, y = processor.split_features_target(clean_data)
        X_train, X_test, y_train, y_test = processor.prepare_data(X, y)
        
        # Make predictions on test set
        predictions = processor.model.predict(X_test).tolist()
        actual = y_test.tolist()
        
        return jsonify({
            "predictions": predictions,
            "actual": actual,
            "model_info": last_training_data,
            "prediction_count": len(predictions)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Prediction failed",
            "details": str(e)
        }), 500

@app.route('/model', methods=['PUT'])
def update_model_config():
    """Update model configuration"""
    try:
        config = request.json
        
        if not config:
            return jsonify({
                "error": "No configuration provided"
            }), 400
        
        # Update model parameters (simplified example)
        n_estimators = config.get('n_estimators', 10)
        random_state = config.get('random_state', 42)
        
        # Create new processor with updated config
        from sklearn.ensemble import RandomForestClassifier
        processor.model = RandomForestClassifier(
            n_estimators=n_estimators, 
            random_state=random_state
        )
        
        global model_trained
        model_trained = False  # Need to retrain with new config
        
        return jsonify({
            "message": "Model configuration updated",
            "config": {
                "n_estimators": n_estimators,
                "random_state": random_state
            },
            "note": "Model needs retraining"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Configuration update failed",
            "details": str(e)
        }), 500

@app.route('/model', methods=['DELETE'])
def reset_model():
    """Reset/clear the model"""
    global model_trained, last_training_data
    
    try:
        # Reset to fresh processor
        global processor
        processor = DataProcessor()
        model_trained = False
        last_training_data = None
        
        return jsonify({
            "message": "Model reset successfully"
        }), 204
        
    except Exception as e:
        return jsonify({
            "error": "Model reset failed",
            "details": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "GET /health",
            "POST /train", 
            "GET /predict",
            "PUT /model",
            "DELETE /model"
        ]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        "error": "Method not allowed for this endpoint"
    }), 405

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

