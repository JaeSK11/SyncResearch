# rag_pipeline/basic_rag.py
from vectordb.chroma_store import ChromaStore
from embeddings_module.embedder import LocalEmbedder
import requests
import json
from typing import List, Dict
from fastapi import HTTPException

class BasicRAG:
    def __init__(self, vllm_url: str = "http://localhost:8000"):
        self.vllm_url = vllm_url
        self.chroma_store = ChromaStore()
        self.chroma_store.create_collection("research_papers")
        self.embedder = LocalEmbedder()
        
    def query(self, question: str, n_chunks: int = 5, paper_filter: str = None) -> str:
        """Complete RAG pipeline: retrieve → augment → generate"""
        
        # 1. Retrieve relevant chunks
        print(f"Searching for relevant chunks...")
        results = self.chroma_store.search_text(
            question, 
            self.embedder, 
            n_results=n_chunks,
            paper_filter=paper_filter
        )
        
        # 2. Build context from retrieved chunks
        context_chunks = results['documents'][0]
        context = "\n\n".join(context_chunks)
        
        # 3. Create prompt
        prompt = self._build_prompt(question, context)
        
        # 4. Generate response with vLLM
        print(f"Generating response with LLM...")
        response = self._call_llm(prompt)
        
        return response, results
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build prompt with retrieved context"""
        prompt = f"""You are a helpful research assistant. Answer the question based on the provided context from research papers.

Context from papers:
{context}

Question: {question}

Answer based on the context above:"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call vLLM server"""
        payload = {
            "model": "llama-3.1-8b-instruct",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            print(f"Calling vLLM at {self.vllm_url}/v1/chat/completions")
            response = requests.post(
                f"{self.vllm_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            
            print(f"vLLM Response Status: {response.status_code}")
            print(f"vLLM Response: {response.text[:500]}")  # First 500 chars
            
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.ConnectionError as e:
            print(f"Connection Error: {e}")
            raise HTTPException(500, "Could not connect to vLLM server")
        except Exception as e:
            print(f"LLM Error: {type(e).__name__}: {e}")
            raise HTTPException(500, f"LLM error: {str(e)}")