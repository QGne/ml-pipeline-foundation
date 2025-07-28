import boto3
import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError


def convert_floats_to_decimals(obj):
    """Convert float values to Decimal types for DynamoDB compatibility."""
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimals(v) for v in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


def convert_decimals_to_floats(obj):
    """Convert Decimal values back to float for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_decimals_to_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_floats(v) for v in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


class DynamoDBClient:    
    def __init__(self, table_name: str = "ml-models"): # Initialize DynamoDB client
        self.table_name = table_name
        
        try:
            # Configure the boto3 for LocalStack
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'test'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
            )
            
            self.table = None
            self._ensure_table_exists()
        except Exception as e:
            raise Exception(f"Failed to initialize DynamoDB client: {str(e)}")
    
    def _ensure_table_exists(self):
        try:
            self.table = self.dynamodb.Table(self.table_name)
            self.table.load()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self._create_table()
            else:
                raise
    

    def _create_table(self): #table creation
        try:
            self.table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'model_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'model_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )

            
            # Wait for table to be created
            self.table.wait_until_exists()
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise
    
    def create_model(self, model_id: str, metadata: Dict) -> Dict:# Create new model entry.
        
        try:
             # Check if model already exists
            existing = self.get_model(model_id)
            if existing:
                raise ValueError(f"Model {model_id} already exists")
            
            item = {
                'model_id': model_id,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                **metadata
            }
            
            # Convert float values to Decimal for DynamoDB compatibility
            item = convert_floats_to_decimals(item)
            
            self.table.put_item(Item=item)
            return item
            
        except ClientError as e:
            raise Exception(f"Failed to create model: {str(e)}")
    
    def get_model(self, model_id: str) -> Optional[Dict]:
        # Get model by ID
        try:
            response = self.table.get_item(Key={'model_id': model_id})
            item = response.get('Item')
            if item:
                # Convert Decimal values back to float for JSON serialization
                return convert_decimals_to_floats(item)
            return item
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return None
            raise
    
    def update_model(self, model_id: str, updates: Dict) -> Dict: # Update existing model
        
        try:
            # Check if model exists
            if not self.get_model(model_id):
                raise ValueError(f"Model {model_id} not found")
            
            
            update_expr = "SET updated_at = :updated_at" # Build update expression
            expr_values = {':updated_at': datetime.utcnow().isoformat()}
            
            for key, value in updates.items():
                if key not in ['model_id', 'created_at']:
                    update_expr += f", {key} = :{key}"
                    expr_values[f":{key}"] = value
            
            # Convert float values to Decimal for DynamoDB compatibility
            expr_values = convert_floats_to_decimals(expr_values)
            
            response = self.table.update_item(
                Key={'model_id': model_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values,
                ReturnValues='ALL_NEW'
            )
            
            # Convert Decimal values back to float for JSON serialization
            return convert_decimals_to_floats(response['Attributes'])
            
        except ClientError as e:
            raise Exception(f"Failed to update model: {str(e)}")
    
    def delete_model(self, model_id: str) -> bool:   # Delete model by ID

        try:
            # Check if model exists
            if not self.get_model(model_id):
                raise ValueError(f"Model {model_id} not found")
            
            self.table.delete_item(Key={'model_id': model_id})
            return True
            
        except ClientError as e:
            raise Exception(f"Failed to delete model: {str(e)}")
    
    def list_models(self, limit: int = 100) -> List[Dict]:
        #List all models
        try:
            response = self.table.scan(Limit=limit)
            items = response.get('Items', [])
            # Convert Decimal values back to float for JSON serialization
            return [convert_decimals_to_floats(item) for item in items]
        except ClientError as e:
            raise Exception(f"Failed to list models: {str(e)}")
    
    def query_models(self, **kwargs) -> List[Dict]:
        # Query models with filters, rather simple now
        try:
            # Quick implem 
            items = self.list_models()
            
            # Apply filters
            filtered = items
            for key, value in kwargs.items():
                filtered = [item for item in filtered if self._compare_values(item.get(key), value)]
            
            return filtered
            
        except Exception as e:
            raise Exception(f"Failed to query models: {str(e)}")
    
    def _compare_values(self, item_value, filter_value):
        """Compare values accounting for different data types (Decimal, float, etc.)"""
        if item_value is None:
            return False
        
        # Convert both values to strings for comparison to handle Decimal types
        try:
            return str(item_value) == str(filter_value)
        except:
            return item_value == filter_value