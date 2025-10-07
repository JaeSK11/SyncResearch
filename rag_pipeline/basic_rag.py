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
            n_results=n_chunks * 2,  # Get more candidates
            paper_filter=paper_filter
        )
       
        # Filter by similarity threshold
        filtered_chunks = []
        filtered_metadatas = []
        if 'distances' in results and results['distances']:
            for i, distance in enumerate(results['distances'][0]):
                # ChromaDB uses distance (lower = more similar)
                # Keep only chunks with distance < 0.7 (adjust threshold)
                if distance < 1.0:
                    filtered_chunks.append(results['documents'][0][i])
                    if 'metadatas' in results:
                        filtered_metadatas.append(results['metadatas'][0][i])
       
        # ===== ADD CONTEXT TRUNCATION =====
        MAX_CONTEXT_TOKENS = 4500  # Conservative limit (leave 3000 for system + completion)
        CHARS_PER_TOKEN = 3  # More accurate estimate (was 4, too optimistic)
        MAX_CONTEXT_CHARS = MAX_CONTEXT_TOKENS * CHARS_PER_TOKEN  # ~13,500 chars
        
        context_chunks = []
        used_metadatas = []
        total_chars = 0
        
        for i, chunk in enumerate(filtered_chunks[:n_chunks]):
            # Truncate individual chunks if they're too long
            max_chunk_chars = 3000  # ~1000 tokens per chunk (reduced from 6000)
            if len(chunk) > max_chunk_chars:
                chunk = chunk[:max_chunk_chars] + "..."
                print(f"⚠️  Truncated chunk {i+1} from {len(filtered_chunks[i])} to {len(chunk)} chars")
            
            # Check if adding this chunk would exceed limit
            if total_chars + len(chunk) > MAX_CONTEXT_CHARS:
                print(f"⚠️  Context limit reached at {total_chars} chars, stopping at {len(context_chunks)} chunks")
                break
            
            context_chunks.append(chunk)
            if i < len(filtered_metadatas):
                used_metadatas.append(filtered_metadatas[i])
            total_chars += len(chunk)
        
        print(f"📊 Using {len(context_chunks)} chunks (~{total_chars} chars, ~{total_chars//3} tokens)")
        
        # Use truncated chunks
        context = "\n\n---\n\n".join(context_chunks)
       
        # 3. Create prompt
        prompt = self._build_prompt(question, context)
       
        # Double check prompt size
        prompt_tokens = len(prompt) // 3  # More accurate estimate
        print(f"📝 Final prompt: ~{prompt_tokens} tokens")
        
        if prompt_tokens > 7500:  # If still over limit (8192 - 500 for completion - 200 buffer)
            print(f"⚠️  WARNING: Prompt still too large ({prompt_tokens} tokens), further reducing...")
            # Emergency truncation - be very aggressive
            context = context[:10000]  # Hard limit to ~3300 tokens
            prompt = self._build_prompt(question, context)
            print(f"📝 Reduced prompt: ~{len(prompt)//3} tokens")
        
        # 4. Generate response with vLLM
        print(f"Generating response with LLM...")
        response = self._call_llm(prompt)
        
        # Return with actually used sources
        results['metadatas'] = [used_metadatas] if used_metadatas else results.get('metadatas', [[]])
        results['documents'] = [context_chunks]
       
        return response, results
   
    def _build_prompt(self, question: str, context: str) -> str:
        """Build prompt with retrieved context"""
        prompt = f"""You are a helpful research assistant. Answer questions based on the provided research paper excerpts.

IMPORTANT INSTRUCTIONS:
- If the question is a greeting (hi, hello, hey, etc.), respond naturally and offer to help with questions about the research papers.
- If the question is not related to the research papers in the context, politely say you can only answer questions about the uploaded research papers.
- Only use information from the context below to answer research-related questions.
- Be concise and cite specific papers when possible.

Context from papers:
{context}

Question: {question}

Answer:"""
        return prompt
   
    def _call_llm(self, prompt: str) -> str:
        """Call vLLM server"""
        payload = {
            "model": "llama-3.1-8b-instruct",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,  # Reduced from 500 to allow more context
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
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response body: {response.text}")
            raise HTTPException(500, f"LLM HTTP error: {str(e)}")
        except Exception as e:
            print(f"LLM Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(500, f"LLM error: {str(e)}")