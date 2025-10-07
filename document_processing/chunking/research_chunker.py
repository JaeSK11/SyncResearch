# document_processing/chunking/research_chunker.py
from typing import List, Dict, Optional
import json
import re

class ResearchPaperChunker:
    def __init__(self, context_percentage: float = 0.15):
        """
        Args:
            context_percentage: How much context to include from adjacent sections (0.1-0.15 = 10-15%)
        """
        self.context_percentage = context_percentage
        
        # Section-specific configs
        self.section_configs = {
            'abstract': {'max_size': 500, 'overlap': 0},
            'introduction': {'max_size': 1500, 'overlap': 300},
            'methodology': {'max_size': 1200, 'overlap': 200},
            'results': {'max_size': 800, 'overlap': 150},
            'conclusion': {'max_size': 1000, 'overlap': 200},
            'default': {'max_size': 1000, 'overlap': 200}
        }
    
    def chunk_paper(self, processed_paper: Dict) -> List[Dict]:
        """Smart chunking with section-aware context bleeding"""
        chunks = []
        
        # USE THE SECTIONS ALREADY EXTRACTED BY PAPERPROCESSOR!
        sections = processed_paper.get('sections', [])
        
        if not sections:
            print("⚠️  No sections found in processed_paper")
            return chunks
        
        print(f"📋 Chunking {len(sections)} sections...")
        
        # Process each section with surrounding context
        for i, section in enumerate(sections):
            # Get adjacent sections for context
            prev_section = sections[i-1] if i > 0 else None
            next_section = sections[i+1] if i < len(sections) - 1 else None
            
            section_chunks = self._chunk_section_with_bleed(
                section,
                prev_section,
                next_section,
                processed_paper['metadata']
            )
            chunks.extend(section_chunks)
        
        # Handle special elements
        chunks.extend(self._process_tables(processed_paper))
        
        print(f"✅ Created {len(chunks)} total chunks")
        return chunks
    
    def _chunk_section_with_bleed(
        self, 
        section: Dict, 
        prev_section: Optional[Dict],
        next_section: Optional[Dict],
        metadata: Dict
    ) -> List[Dict]:
        """
        Chunk a section with 10-15% context from surrounding sections
        """
        # Determine section type from title
        section_title = section.get('title', '').lower()
        section_type = 'default'
        
        if 'abstract' in section_title:
            section_type = 'abstract'
        elif 'introduction' in section_title:
            section_type = 'introduction'
        elif 'method' in section_title or 'approach' in section_title:
            section_type = 'methodology'
        elif 'result' in section_title or 'experiment' in section_title:
            section_type = 'results'
        elif 'conclusion' in section_title:
            section_type = 'conclusion'
        
        config = self.section_configs.get(section_type, self.section_configs['default'])
        
        chunks = []
        
        # Get full section text
        section_text = self._extract_section_text(section)
        
        # Skip empty sections
        if not section_text.strip():
            return chunks
        
        # Calculate context sizes (10-15% of adjacent sections)
        context_chars = int(len(section_text) * self.context_percentage)
        
        # Get bleeding context
        prev_context = ""
        next_context = ""
        
        if prev_section:
            prev_text = self._extract_section_text(prev_section)
            # Take last N characters from previous section
            prev_context = prev_text[-context_chars:] if len(prev_text) > context_chars else prev_text
            if prev_context:
                prev_context = f"[Context from previous section: {prev_section.get('title', 'Unknown')}]\n{prev_context}\n\n"
        
        if next_section:
            next_text = self._extract_section_text(next_section)
            # Take first N characters from next section
            next_context = next_text[:context_chars] if len(next_text) > context_chars else next_text
            if next_context:
                next_context = f"\n\n[Context from next section: {next_section.get('title', 'Unknown')}]\n{next_context}"
        
        # For short sections, keep as single chunk with context
        full_text_with_context = prev_context + section_text + next_context
        
        if len(section_text) < config['max_size']:
            chunks.append({
                'text': full_text_with_context.strip(),
                'metadata': {
                    **metadata,
                    'section': section_type,
                    'section_title': section.get('title', 'Unknown'),
                    'chunk_type': 'complete_with_context',
                    'has_prev_context': bool(prev_context),
                    'has_next_context': bool(next_context),
                    'context_percentage': self.context_percentage
                }
            })
            return chunks
        
        # For longer sections, chunk with paragraph awareness
        paragraphs = section_text.split('\n\n')
        current_chunk = ""
        chunk_index = 0
        
        for i, para in enumerate(paragraphs):
            test_chunk = current_chunk + para + '\n\n'
            
            if len(test_chunk) > config['max_size'] and current_chunk:
                # Finalize current chunk
                chunk_text = current_chunk.strip()
                
                # Add contexts only to first and last chunks
                if chunk_index == 0 and prev_context:
                    chunk_text = prev_context + chunk_text
                
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        **metadata,
                        'section': section_type,
                        'section_title': section.get('title', 'Unknown'),
                        'chunk_type': 'section_part',
                        'chunk_index': chunk_index,
                        'has_prev_context': (chunk_index == 0 and bool(prev_context)),
                        'has_next_context': False,  # Will be updated for last chunk
                        'context_percentage': self.context_percentage
                    }
                })
                
                chunk_index += 1
                current_chunk = para + '\n\n'
            else:
                current_chunk = test_chunk
        
        # Add final chunk with next context
        if current_chunk.strip():
            chunk_text = current_chunk.strip()
            if next_context:
                chunk_text = chunk_text + next_context
            
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    **metadata,
                    'section': section_type,
                    'section_title': section.get('title', 'Unknown'),
                    'chunk_type': 'section_part',
                    'chunk_index': chunk_index,
                    'has_prev_context': False,
                    'has_next_context': bool(next_context),
                    'context_percentage': self.context_percentage
                }
            })
        
        return chunks
    
    def _extract_section_text(self, section: Dict) -> str:
        """Extract all text from a section (PaperProcessor format)"""
        text = section.get('title', '') + '\n\n'
        
        # PaperProcessor stores content as list of strings
        for item in section.get('content', []):
            if isinstance(item, str):
                text += item + '\n\n'
            elif isinstance(item, dict) and 'text' in item:
                text += item['text'] + '\n\n'
        
        return text.strip()
    
    def _process_tables(self, processed_paper: Dict) -> List[Dict]:
        """Tables get their own chunks with context"""
        chunks = []
        tables = processed_paper.get('tables', [])
        
        for i, table in enumerate(tables):
            table_text = f"[TABLE {i+1}]\n"
            if table.get('caption'):
                table_text += f"Caption: {table['caption']}\n\n"
            
            if table.get('data'):
                table_text += str(table['data'])
            
            chunks.append({
                'text': table_text,
                'metadata': {
                    **processed_paper['metadata'],
                    'chunk_type': 'table',
                    'table_index': i,
                    'section': 'table'
                }
            })
        
        return chunks