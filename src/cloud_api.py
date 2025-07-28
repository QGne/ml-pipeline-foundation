from flask import Flask, jsonify, request
import json
import os
import uuid
from datetime import datetime
from src.data_processor import DataProcessor
from src.cloud import DynamoDBClient, S3Client

app = Flask(__name__)

# Initialize cloud clients lazily
dynamodb = None
s3 = None

def get_cloud_clients():
    #Get or initialize cloud clients
    global dynamodb, s3
    try:
        if dynamodb is None:
            dynamodb = DynamoDBClient()
        if s3 is None:
            s3 = S3Client()
        return dynamodb, s3
    except Exception as e:
        # If cloud clients can't be initialized, raise a more descriptive error
        raise Exception(f"Failed to initialize cloud clients: {str(e)}")

# In-memory cache for current model
current_model = None
current_model_id = None


@app.route('/health', methods=['GET'])
def health_check():
    #Health check endpoint
    return jsonify({
        "status": "healthy",
        "message": "Cloud ML API is running",
        "services": {
            "dynamodb": "connected",
            "s3": "connected"
        }
    }), 200


@app.route('/models', methods=['GET'])
def get_models():
    #Get models with optional query parameters
    dynamodb, s3 = get_cloud_clients()
    try:
        # Check for query parameters
        query_params = request.args.to_dict()
        
        if not query_params:
            # No parameters - return appropriate response
            return jsonify({
                "error": "No query parameters provided",
                "message": "Please provide query parameters to filter models",
                "available_filters": ["model_type", "accuracy_threshold", "created_after"]
            }), 400
        
        # Check for incorrect parameters
        valid_params = ['model_type', 'accuracy_threshold', 'created_after', 'model_id']
        invalid_params = [p for p in query_params if p not in valid_params]
        
        if invalid_params:
            return jsonify({
                "error": "Invalid query parameters",
                "invalid_parameters": invalid_params,
                "valid_parameters": valid_params
            }), 400
        
        # Query models
        if 'model_id' in query_params:
            # Get specific model
            model = dynamodb.get_model(query_params['model_id'])
            if not model:
                return jsonify({
                    "error": "Model not found",
                    "model_id": query_params['model_id']
                }), 404
            return jsonify(model), 200
        
        # Query with filters
        models = dynamodb.query_models(**query_params)
        
        if not models:
            return jsonify({
                "message": "No models found matching criteria",
                "filters": query_params,
                "results": []
            }), 200
        
        return jsonify({
            "filters": query_params,
            "count": len(models),
            "results": models
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to query models",
            "details": str(e)
        }), 500


@app.route('/models', methods=['POST'])
def create_model():
    #Create and train a new model
    global current_model, current_model_id
    
    try:
        # Get cloud clients
        dynamodb, s3 = get_cloud_clients()

        # Parse request body
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Generate model ID
        model_id = data.get('model_id', f"model_{uuid.uuid4().hex[:8]}")
        
        # Check if model already exists
        existing_model = dynamodb.get_model(model_id)
        if existing_model:
            return jsonify({
                "error": "Duplicate model ID",
                "message": f"Model {model_id} already exists",
                "existing_model": existing_model
            }), 409
        
        # Load and process data
        processor = DataProcessor()
        data_path = data.get('data_path', 'data/iris_simple.csv')
        
        if not os.path.exists(data_path):
            return jsonify({"error": "Data file not found"}), 400
        
        # Train model
        ml_data = processor.load_data(data_path)
        clean_data = processor.clean_data(ml_data)
        X, y = processor.split_features_target(clean_data)
        X_train, X_test, y_train, y_test = processor.prepare_data(X, y)
        
        train_accuracy = processor.train_model(X_train, y_train)
        test_accuracy = processor.evaluate_model(X_test, y_test)
        
        # Prepare metadata
        metadata = {
            "model_type": data.get('model_type', 'RandomForest'),
            "train_accuracy": train_accuracy,
            "test_accuracy": test_accuracy,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "features": list(X.columns),
            "data_path": data_path,
            **{k: v for k, v in data.items() if k not in ['model_id', 'data_path']}
        }
        
        # Store in DynamoDB
        db_item = dynamodb.create_model(model_id, metadata)
        
        # Store in S3
        s3_key = s3.upload_model(model_id, processor.model, metadata)
        
        # Update current model
        current_model = processor
        current_model_id = model_id
        
        return jsonify({
            "message": "Model created successfully",
            "model_id": model_id,
            "dynamodb_item": db_item,
            "s3_key": s3_key,
            "metadata": metadata
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        return jsonify({
            "error": "Failed to create model",
            "details": str(e)
        }), 500


@app.route('/models/<model_id>', methods=['PUT'])
def update_model(model_id):
    #Update existing model
    global current_model, current_model_id
    
    try:
        #Get cloud clients
        dynamodb, s3 = get_cloud_clients()

        # Check if model exists
        existing_model = dynamodb.get_model(model_id)
        if not existing_model:
            return jsonify({
                "error": "Model not found",
                "message": f"No model with ID {model_id}"
            }), 404
        
        # Parse request body
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # If retraining is requested
        if data.get('retrain', False):
            processor = DataProcessor()
            data_path = data.get('data_path', existing_model.get('data_path', 'data/iris_simple.csv'))
            
            # Retrain model
            ml_data = processor.load_data(data_path)
            clean_data = processor.clean_data(ml_data)
            X, y = processor.split_features_target(clean_data)
            X_train, X_test, y_train, y_test = processor.prepare_data(X, y)
            
            train_accuracy = processor.train_model(X_train, y_train)
            test_accuracy = processor.evaluate_model(X_test, y_test)
            
            # Update metadata
            updates = {
                "train_accuracy": train_accuracy,
                "test_accuracy": test_accuracy,
                "last_trained": datetime.utcnow().isoformat()
            }
            
            # Update S3 with new model
            s3.update_model(model_id, processor.model, updates)
            
            # Update current model if it's the active one
            if current_model_id == model_id:
                current_model = processor
        else:
            # Just update metadata
            updates = {k: v for k, v in data.items() if k not in ['model_id', 'retrain']}
        
        # Update DynamoDB
        updated_item = dynamodb.update_model(model_id, updates)
        
        # Update S3 metadata
        s3.update_model(model_id, metadata=updates)
        
        return jsonify({
            "message": "Model updated successfully",
            "model_id": model_id,
            "updates": updates,
            "updated_item": updated_item
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({
            "error": "Failed to update model",
            "details": str(e)
        }), 500


@app.route('/models/<model_id>', methods=['DELETE'])
def delete_model(model_id):
    #Delete model from both DynamoDB and S3
    global current_model, current_model_id
    
    try:
        #Get cloud clients
        dynamodb, s3 = get_cloud_clients()

        # Check if model exists
        existing_model = dynamodb.get_model(model_id)
        if not existing_model:
            return jsonify({
                "error": "Model not found",
                "message": f"No model with ID {model_id}"
            }), 404
        
        # Delete from DynamoDB
        dynamodb.delete_model(model_id)
        
        # Delete from S3
        s3.delete_model(model_id)
        
        # Clear current model if it's the one being deleted
        if current_model_id == model_id:
            current_model = None
            current_model_id = None
        
        return jsonify({
            "message": "Model deleted successfully",
            "model_id": model_id
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({
            "error": "Failed to delete model",
            "details": str(e)
        }), 500


@app.route('/models/<model_id>/predict', methods=['GET'])
def predict(model_id):
    #Make predictions using a specific model
    global current_model, current_model_id
    
    try:
        #Get cloud clients
        dynamodb, s3 = get_cloud_clients()
        
        # Load model if not current
        if current_model_id != model_id:
            # Check if model exists in DynamoDB
            model_metadata = dynamodb.get_model(model_id)
            if not model_metadata:
                return jsonify({
                    "error": "Model not found",
                    "model_id": model_id
                }), 404
            
            # Load model from S3
            model = s3.download_model(model_id)
            if not model:
                return jsonify({
                    "error": "Model artifact not found in S3",
                    "model_id": model_id
                }), 404
            
            # Create processor and set model
            processor = DataProcessor()
            processor.model = model
            current_model = processor
            current_model_id = model_id
        
        # Make predictions on test data
        data_path = request.args.get('data_path', 'data/iris_simple.csv')
        data = current_model.load_data(data_path)
        clean_data = current_model.clean_data(data)
        X, y = current_model.split_features_target(clean_data)
        X_train, X_test, y_train, y_test = current_model.prepare_data(X, y)
        
        predictions = current_model.model.predict(X_test).tolist()
        actual = y_test.tolist()
        
        return jsonify({
            "model_id": model_id,
            "predictions": predictions,
            "actual": actual,
            "accuracy": current_model.model.score(X_test, y_test)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Prediction failed",
            "details": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    #Handle 404 errors
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "GET /health",
            "GET /models",
            "POST /models",
            "PUT /models/<model_id>",
            "DELETE /models/<model_id>",
            "GET /models/<model_id>/predict"
        ]
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    #Handle 405 errors
    return jsonify({
        "error": "Method not allowed for this endpoint"
    }), 405


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)