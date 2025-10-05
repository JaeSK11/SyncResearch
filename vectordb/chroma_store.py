# vectordb/chroma_store.py
import chromadb
from chromadb.config import Settings
import numpy as np
from pathlib import Path
import json
from typing import List, Dict, Optional

class ChromaStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB with local persistence"""
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        print(f"ChromaDB initialized at: {self.persist_directory}")
    
    def create_collection(self, collection_name: str = "research_papers"):
        """Create or get a collection"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(collection_name)
            print(f"Using existing collection: {collection_name}")
        except:
            # Create new collection
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            print(f"Created new collection: {collection_name}")
        
        self.collection = collection
        return collection
    
    def add_embedded_chunks(self, embedded_chunks_file: str, paper_id: str):
        """Add embedded chunks to ChromaDB"""
        # Load embedded chunks
        with open(embedded_chunks_file, 'r') as f:
            chunks = json.load(f)
        
        # Prepare data for ChromaDB
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Create unique ID
            chunk_id = f"{paper_id}_chunk_{i}"
            ids.append(chunk_id)
            
            # Get embedding
            embeddings.append(chunk['embedding'])
            
            # Get text
            documents.append(chunk['text'])
            
            # Prepare metadata
            metadata = chunk['metadata'].copy()
            metadata['paper_id'] = paper_id
            metadata['chunk_index'] = i
            metadatas.append(metadata)
        
        # Add to ChromaDB
        print(f"Adding {len(chunks)} chunks to ChromaDB...")
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✅ Added {len(chunks)} chunks for paper: {paper_id}")
    
    def search(self, query_embedding: List[float], n_results: int = 5, paper_filter: Optional[str] = None):
        """Search for similar chunks"""
        where_clause = {"paper_id": paper_filter} if paper_filter else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause
        )
        
        return results
    
    def search_text(self, query_text: str, embedder, n_results: int = 5, paper_filter: Optional[str] = None):
        """Search using text query (generates embedding first)"""
        # Generate embedding for query
        query_chunk = [{"text": query_text, "metadata": {}}]
        embedded = embedder.embed_chunks(query_chunk)
        query_embedding = embedded[0]['embedding']
        
        # Search
        return self.search(query_embedding, n_results, paper_filter)
    
    def get_collection_stats(self):
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection.name
        }