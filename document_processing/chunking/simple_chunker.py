# Create simple_chunker.py for now
# document_processing/chunking/simple_chunker.py
from typing import List, Dict
import json

class SimpleChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_paper(self, processed_paper: Dict) -> List[Dict]:
        chunks = []
        
        # Extract all text from Docling output
        all_text = ""
        if 'content' in processed_paper and 'texts' in processed_paper['content']:
            for text_item in processed_paper['content']['texts']:
                if isinstance(text_item, dict) and 'text' in text_item:
                    all_text += text_item['text'] + "\n\n"
        
        # Simple sliding window
        start = 0
        chunk_id = 0
        
        while start < len(all_text):
            end = min(start + self.chunk_size, len(all_text))
            chunk_text = all_text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        **processed_paper['metadata'],
                        'chunk_id': chunk_id,
                        'char_start': start,
                        'char_end': end
                    }
                })
                chunk_id += 1
            
            start += (self.chunk_size - self.overlap)
        
        return chunks