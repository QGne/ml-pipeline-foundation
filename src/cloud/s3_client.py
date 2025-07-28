import boto3
import json
import os
import pickle
from typing import Dict, Optional, Any
from botocore.exceptions import ClientError


class S3Client:     #Handles S3 operations for ML model artifacts.

    
    def __init__(self, bucket_name: str = "ml-models-bucket"):
        #Initialize S3 client
        self.bucket_name = bucket_name
        
        # Configure boto3 for LocalStack
        self.s3 = boto3.client(
            's3',
            endpoint_url=os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566'),
            region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'test'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'test')
        )
        
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        #Create bucket if it doesn't exist
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                self._create_bucket()
            else:
                raise
    
    def _create_bucket(self):
        #Create S3 bucket
        try:
            self.s3.create_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] != 'BucketAlreadyExists':
                raise
    
    def upload_model(self, model_id: str, model_object: Any, metadata: Dict = None) -> str:
        #Upload model artifact to S3
        try:
            # Serialize model
            model_key = f"models/{model_id}/model.pkl"
            model_bytes = pickle.dumps(model_object)
            
            # Upload model
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=model_key,
                Body=model_bytes,
                Metadata=metadata or {}
            )
            
            # Upload metadata as JSON
            if metadata:
                metadata_key = f"models/{model_id}/metadata.json"
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=metadata_key,
                    Body=json.dumps(metadata, indent=2),
                    ContentType='application/json'
                )
            
            return model_key
            
        except Exception as e:
            raise Exception(f"Failed to upload model: {str(e)}")
    
    def download_model(self, model_id: str) -> Optional[Any]:
        # download model artifact from S3
        try:
            model_key = f"models/{model_id}/model.pkl"
            
            # Download model
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=model_key
            )
            
            # Deserialize model
            model_bytes = response['Body'].read()
            model_object = pickle.loads(model_bytes)
            
            return model_object
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise Exception(f"Failed to download model: {str(e)}")
    
    def get_model_metadata(self, model_id: str) -> Optional[Dict]:
        # Get model metadata from S3
        try:
            metadata_key = f"models/{model_id}/metadata.json"
            
            response = self.s3.get_object(
                Bucket=self.bucket_name,
                Key=metadata_key
            )
            
            metadata = json.loads(response['Body'].read())
            return metadata
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise
    
    def update_model(self, model_id: str, model_object: Any = None, metadata: Dict = None) -> str:
        # Update existing model in S3 
        try:
            # Check if model exists
            existing_metadata = self.get_model_metadata(model_id)
            if not existing_metadata:
                raise ValueError(f"Model {model_id} not found")
            
            # Update model if provided
            if model_object:
                model_key = f"models/{model_id}/model.pkl"
                model_bytes = pickle.dumps(model_object)
                
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=model_key,
                    Body=model_bytes
                )

            
            if metadata: # Merge with existing metadata
                
                updated_metadata = {**existing_metadata, **metadata}
                metadata_key = f"models/{model_id}/metadata.json"
                
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=metadata_key,
                    Body=json.dumps(updated_metadata, indent=2),
                    ContentType='application/json'
                )
            
            return f"models/{model_id}/model.pkl"
            
        except Exception as e:
            raise Exception(f"Failed to update model: {str(e)}")
    
    def delete_model(self, model_id: str) -> bool:
        #Delete model artifacts from S3 
        try:
            # List all objects with the model prefix
            prefix = f"models/{model_id}/"
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                raise ValueError(f"Model {model_id} not found")
            
            # Delete all objects
            objects = [{'Key': obj['Key']} for obj in response['Contents']]
            
            self.s3.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects}
            )
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to delete model: {str(e)}")
    
    def list_models(self) -> list:
        # List all model IDs in S3
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='models/',
                Delimiter='/'
            )
            
            if 'CommonPrefixes' not in response:
                return []
            
            # Extract model IDs from prefixes
            model_ids = []
            for prefix in response['CommonPrefixes']:
                # Extract model id from path following in de form of 'models/model_id/'
                path_parts = prefix['Prefix'].strip('/').split('/')
                if len(path_parts) >= 2:
                    model_ids.append(path_parts[1])
            
            return model_ids
            
        except Exception as e:
            raise Exception(f"Failed to list models: {str(e)}")
    
    def model_exists(self, model_id: str) -> bool:
        # Check if model exists in S3 
        try:
            model_key = f"models/{model_id}/model.pkl"
            self.s3.head_object(Bucket=self.bucket_name, Key=model_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise