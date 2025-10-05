# storage/minio_client.py
import boto3
from botocore.client import Config
import os
from dotenv import load_dotenv
from pathlib import Path
import json

load_dotenv()

class MinIOStorage:
    def __init__(self):
        # MinIO connection settings
        self.endpoint_url = os.getenv('MINIO_ENDPOINT', 'http://YOUR_UNRAID_IP:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin123')
        self.bucket_name = os.getenv('MINIO_BUCKET', 'research-papers')
        
        # Create S3 client with MinIO endpoint
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'  # MinIO doesn't care but boto3 needs it
        )
        
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Bucket '{self.bucket_name}' exists")
        except:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            print(f"Created bucket '{self.bucket_name}'")
    
    def upload_pdf(self, local_path: str, paper_id: str) -> str:
        """Upload PDF to MinIO"""
        s3_key = f"raw-papers/{paper_id}.pdf"
        self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
        print(f"Uploaded to MinIO: {s3_key}")
        return s3_key
    
    def upload_processed(self, processed_data: dict, paper_id: str) -> str:
        """Upload processed JSON to MinIO"""
        s3_key = f"processed/{paper_id}_docling.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=json.dumps(processed_data)
        )
        print(f"Uploaded processed data to MinIO: {s3_key}")
        return s3_key
    
    def download_file(self, s3_key: str, local_path: str):
        """Download file from MinIO"""
        self.s3_client.download_file(self.bucket_name, s3_key, local_path)
        print(f"Downloaded {s3_key} to {local_path}")
    
    def list_papers(self):
        """List all papers in bucket"""
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix='raw-papers/'
        )
        
        papers = []
        if 'Contents' in response:
            for obj in response['Contents']:
                papers.append(obj['Key'])
        return papers