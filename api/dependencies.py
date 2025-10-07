# api/dependencies.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from document_processing.chunking.research_chunker import ResearchPaperChunker 
from functools import lru_cache
from rag_pipeline.basic_rag import BasicRAG
from storage.minio_client import MinIOStorage
from document_processing.processor import PaperProcessor
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
            self.chunker = ResearchPaperChunker(context_percentage=0.15)  
            self.embedder = LocalEmbedder()
            self.chroma = ChromaStore()
            self.chroma.create_collection('research_papers')  # Create collection!
            self.storage = MinIOStorage()  
           
        def process_paper(self, pdf_path):
            # 1. Process with Docling
            print("📄 Processing PDF with Docling...")
            result = self.processor.process_paper(pdf_path)
            paper_id = result['metadata']['paper_id']
            
            # 2. Upload to MinIO
            print("☁️ Uploading to MinIO...")
            self.storage.upload_pdf(pdf_path, paper_id)
            
            # 3. Chunk the document with research chunker
            print("✂️ Chunking document...")
            chunks = self.chunker.chunk_paper(result)
            print(f"   Created {len(chunks)} chunks")
            
            # 4. Generate embeddings
            print("🧮 Generating embeddings...")
            embedded_chunks = self.embedder.embed_chunks(chunks)
            
            # 5. Store in ChromaDB
            print("💾 Storing in ChromaDB...")
            # Prepare for ChromaDB
            ids = [f"{paper_id}_chunk_{i}" for i in range(len(embedded_chunks))]
            embeddings = [chunk['embedding'] for chunk in embedded_chunks]
            documents = [chunk['text'] for chunk in embedded_chunks]
            metadatas = [chunk['metadata'] for chunk in embedded_chunks]
            
            self.chroma.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            print(f"✅ Successfully processed {paper_id}")
            return {
                'paper_id': paper_id,
                'num_chunks': len(chunks)
            }
           
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
   
    # Check ChromaDB
    try:
        from vectordb.chroma_store import ChromaStore
        store = ChromaStore()
        store.create_collection('research_papers')
        store.get_collection_stats()  
        status['chromadb'] = 'connected'
    except Exception as e:
        print(f"ChromaDB check failed: {e}")
        status['chromadb'] = 'disconnected'
   
    # Check vLLM
    try:
        import requests
        settings = get_settings()
        response = requests.get(f"{settings.vllm_url}/v1/models", timeout=2)
        if response.status_code == 200:
            status['vllm'] = 'connected'
        else:
            status['vllm'] = 'disconnected'
    except Exception as e:
        print(f"vLLM check failed: {e}")
        status['vllm'] = 'disconnected'
   
    return status