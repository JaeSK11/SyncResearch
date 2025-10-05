import boto3
from pathlib import Path
import json
from typing import Optional

class S3PaperManager:
    def __init__(self, bucket_name: str):
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name
        self.processor = PaperProcessor()
        
    def download_and_process(self, s3_key: str, local_temp_dir: str = "/tmp") -> dict:
        """Download from S3, process with Docling, upload results"""
        # Download PDF
        local_path = Path(local_temp_dir) / Path(s3_key).name
        self.s3_client.download_file(self.bucket_name, s3_key, str(local_path))
        
        # Process with Docling
        paper_id = Path(s3_key).stem
        result = self.processor.process_paper(str(local_path), paper_id)
        
        # Upload processed JSON back to S3
        processed_key = f"processed/{paper_id}_docling.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=processed_key,
            Body=json.dumps(result)
        )
        
        # Clean up local file
        local_path.unlink()
        
        return result