# document_processing/research_chunker.py
from typing import List, Dict, Optional
import json
import re

class ResearchPaperChunker:
    def __init__(self):
        # Research papers need different chunk sizes for different sections
        self.section_configs = {
            'abstract': {'max_size': 500, 'overlap': 0},  # Keep whole
            'introduction': {'max_size': 1500, 'overlap': 300},
            'methodology': {'max_size': 1200, 'overlap': 200},
            'results': {'max_size': 800, 'overlap': 150},  # Smaller for precision
            'conclusion': {'max_size': 1000, 'overlap': 200},
            'default': {'max_size': 1000, 'overlap': 200}
        }
    
    def chunk_paper(self, processed_paper: Dict) -> List[Dict]:
        """
        Smart chunking that respects research paper structure
        """
        chunks = []
        
        # First, identify paper sections from Docling output
        sections = self._identify_sections(processed_paper['content'])
        
        for section in sections:
            section_chunks = self._chunk_section_with_context(
                section,
                processed_paper['metadata']
            )
            chunks.extend(section_chunks)
        
        # Handle special elements
        chunks.extend(self._process_tables(processed_paper))
        chunks.extend(self._process_figures(processed_paper))
        chunks.extend(self._process_equations(processed_paper))
        
        return chunks
    
    def _identify_sections(self, content: Dict) -> List[Dict]:
        """
        Identify research paper sections from Docling output
        """
        sections = []
        current_section = None
        section_patterns = {
            'abstract': r'(?i)^abstract',
            'introduction': r'(?i)^(1\.?|I\.?|introduction)',
            'related_work': r'(?i)(related work|background|literature)',
            'methodology': r'(?i)(method|approach|framework)',
            'results': r'(?i)(result|experiment|evaluation)',
            'discussion': r'(?i)^discussion',
            'conclusion': r'(?i)^conclusion'
        }
        
        texts = content.get('texts', [])
        
        for elem in texts:
            text = elem.get('text', '')
            elem_type = elem.get('type', '')
            
            # Check if this is a section header
            if elem_type == 'heading':
                for section_type, pattern in section_patterns.items():
                    if re.match(pattern, text):
                        # Save previous section
                        if current_section:
                            sections.append(current_section)
                        
                        current_section = {
                            'type': section_type,
                            'title': text,
                            'content': [],
                            'subsections': []
                        }
                        break
                else:
                    # Subsection or unlabeled section
                    if current_section:
                        current_section['subsections'].append({
                            'title': text,
                            'content': []
                        })
            elif current_section:
                # Add content to current section or subsection
                if current_section['subsections']:
                    current_section['subsections'][-1]['content'].append(elem)
                else:
                    current_section['content'].append(elem)
        
        # Don't forget the last section
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _chunk_section_with_context(self, section: Dict, metadata: Dict) -> List[Dict]:
        """
        Chunk a section with smart boundaries and context preservation
        """
        section_type = section.get('type', 'default')
        config = self.section_configs.get(section_type, self.section_configs['default'])
        
        chunks = []
        
        # Combine section content
        full_text = section['title'] + '\n'
        for elem in section['content']:
            if isinstance(elem, dict):
                full_text += elem.get('text', '') + '\n'
        
        # For abstract and conclusion, keep as single chunk if possible
        if section_type in ['abstract', 'conclusion'] and len(full_text) < 1500:
            chunks.append({
                'text': full_text.strip(),
                'metadata': {
                    **metadata,
                    'section': section_type,
                    'section_title': section['title'],
                    'chunk_type': 'section_complete'
                }
            })
            return chunks
        
        # Smart chunking with paragraph awareness
        paragraphs = full_text.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            # Check if adding this paragraph exceeds size limit
            if len(current_chunk) + len(para) > config['max_size'] and current_chunk:
                # Save current chunk with forward context
                chunk_text = current_chunk.strip()
                
                # Add preview of next paragraph (forward context)
                if len(para) > 100:
                    chunk_text += f"\n[Next: {para[:100]}...]"
                
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        **metadata,
                        'section': section_type,
                        'section_title': section['title'],
                        'chunk_type': 'section_part'
                    }
                })
                
                # Start new chunk with backward context
                if chunks:
                    # Add context from previous chunk
                    prev_text = current_chunk.strip()
                    if len(prev_text) > 100:
                        current_chunk = f"[Previous: ...{prev_text[-100:]}]\n"
                    else:
                        current_chunk = f"[Previous: {prev_text}]\n"
                else:
                    current_chunk = ""
                
                current_chunk += para + '\n\n'
            else:
                current_chunk += para + '\n\n'
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                'text': current_chunk.strip(),
                'metadata': {
                    **metadata,
                    'section': section_type,
                    'section_title': section['title'],
                    'chunk_type': 'section_part'
                }
            })
        
        return chunks
    
    def _process_tables(self, processed_paper: Dict) -> List[Dict]:
        """
        Tables get their own chunks with context
        """
        chunks = []
        tables = processed_paper.get('tables', [])
        
        for i, table in enumerate(tables):
            table_text = f"[TABLE {i+1}]\n"
            if table.get('caption'):
                table_text += f"Caption: {table['caption']}\n"
            
            # Add reference context
            table_text += "[This table contains data that may be referenced in the text]\n"
            
            # Include table data
            if table.get('data'):
                table_text += str(table['data'])
            
            chunks.append({
                'text': table_text,
                'metadata': {
                    **processed_paper['metadata'],
                    'chunk_type': 'table',
                    'table_index': i,
                    'searchable_terms': self._extract_table_terms(table)
                }
            })
        
        return chunks
    
    def _extract_table_terms(self, table: Dict) -> List[str]:
        """
        Extract key terms from table for better retrieval
        """
        terms = []
        caption = table.get('caption', '')
        
        # Extract numbers, model names, metrics
        terms.extend(re.findall(r'\b[A-Z]+[-\d.]+\b', caption))  # Model names
        terms.extend(re.findall(r'\d+\.?\d*%?', caption))  # Numbers/percentages
        
        return terms
    
    def _process_figures(self, processed_paper: Dict) -> List[Dict]:
        """
        Process figure captions as chunks
        """
        # Similar to tables
        return []
    
    def _process_equations(self, processed_paper: Dict) -> List[Dict]:
        """
        Extract equations as special chunks
        """
        # Would need equation extraction from Docling
        return []