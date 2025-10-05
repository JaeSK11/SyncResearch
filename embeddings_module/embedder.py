# embeddings_module/embedder.py
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import json
from pathlib import Path
import torch

class LocalEmbedder:
    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5"):
        """
        Initialize local embedding model
        Using BGE as it's optimized for retrieval
        """
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Loading embedding model on {self.device}...")
        
        self.model = SentenceTransformer(model_name)
        self.model.to(self.device)
        print(f"Model loaded: {model_name}")
    
    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for chunks
        """
        # Extract texts
        texts = [chunk['text'] for chunk in chunks]
        
        print(f"Generating embeddings for {len(texts)} chunks...")
        
        # Generate embeddings in batches
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # Important for cosine similarity
        )
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding.tolist()
            chunk['embedding_model'] = self.model.get_sentence_embedding_dimension()
        
        return chunks
    
    def save_embeddings(self, chunks: List[Dict], output_path: str):
        """
        Save chunks with embeddings
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON (for debugging)
        with open(output_path, 'w') as f:
            json.dump(chunks, f, indent=2)
        
        print(f"Saved {len(chunks)} embedded chunks to {output_path}")
        
        # Also save in numpy format for efficiency
        np_path = output_path.with_suffix('.npz')
        embeddings = np.array([c['embedding'] for c in chunks])
        np.savez_compressed(np_path, embeddings=embeddings)
        print(f"Saved embeddings array to {np_path}")