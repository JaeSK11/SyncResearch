# api/dependencies.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from functools import lru_cache
from rag_pipeline.basic_rag import BasicRAG
from storage.minio_client import MinIOStorage
from document_processing.processor import PaperProcessor
from document_processing.chunking.simple_chunker import SimpleChunker
from embeddings_module.embedder import LocalEmbedder
from vectordb.chroma_store import ChromaStore
from api.config import Settings

@lru_cache()
def get_settings():
    """Get settings singleton"""
    return Settings()

@lru_cache()
def get_rag_pipeline():
    """Get RAG pipeline singleton"""
    return BasicRAG()

@lru_cache()
def get_storage():
    """Get storage client singleton"""
    return MinIOStorage()

@lru_cache()
def get_pipeline():
    """Get document processing pipeline"""
    class Pipeline:
        def __init__(self):
            self.processor = PaperProcessor()
            self.storage = MinIOStorage()  
            
        def process_paper(self, pdf_path):
            result = self.processor.process_paper(pdf_path)
            return {'paper_id': result['metadata']['paper_id']}
            
        def list_papers(self):
            papers = self.storage.list_papers()
            return [{"paper_id": p.split('/')[-1].replace('.pdf', ''), 
                    "title": "Unknown", 
                    "num_chunks": 0, 
                    "processed_at": ""} for p in papers]
    
    return Pipeline()

def check_services():
    """Check if all services are running"""
    status = {}
    
    # Check MinIO
    try:
        storage = get_storage()
        storage.s3_client.list_buckets()
        status['minio'] = 'connected'
    except:
        status['minio'] = 'disconnected'
    
    status['chromadb'] = 'unknown'
    status['vllm'] = 'unknown'
    
    return status