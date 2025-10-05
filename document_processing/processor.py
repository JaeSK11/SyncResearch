from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
import os
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat

class PaperProcessor:
    def __init__(self, output_dir: str = "data/processed", use_gpu: bool = False):
        """Initialize Docling processor for research papers"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Force CPU if requested
        if not use_gpu:
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            print("Docling: Using CPU for processing")
        else:
            print("Docling: Using GPU for processing")
        
        # Configure Docling for academic papers
        pdf_options = PdfFormatOption(
            use_ocr=False,  # Set True if you have scanned PDFs
        )
        
        self.converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: pdf_options}
        )
        
    def process_paper(self, pdf_path: str, paper_id: Optional[str] = None) -> Dict:
        """Process a single research paper"""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
            
        if paper_id is None:
            paper_id = pdf_path.stem
            
        print(f"Processing: {pdf_path.name}")
        
        # Convert document
        result = self.converter.convert(pdf_path)
        
        # Extract structured content
        doc_output = result.document.export_to_dict()
        
        # Create metadata
        metadata = {
            "paper_id": paper_id,
            "filename": pdf_path.name,
            "processed_at": datetime.now().isoformat(),
            "num_pages": len(doc_output.get("pages", [])),
            "title": self._extract_title(doc_output),
        }
        
        # Structure the output
        processed_paper = {
            "metadata": metadata,
            "content": doc_output,
            "sections": self._extract_sections(doc_output),
            "tables": self._extract_tables(doc_output),
            "figures": self._extract_figures(doc_output)
        }
        
        # Save to file
        output_path = self.output_dir / f"{paper_id}_processed.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_paper, f, indent=2, ensure_ascii=False)
            
        print(f"Saved to: {output_path}")
        return processed_paper
    
    def _extract_title(self, doc_output: Dict) -> Optional[str]:
        """Extract paper title from document"""
        # Docling usually puts title in the first text element
        if "texts" in doc_output and doc_output["texts"]:
            return doc_output["texts"][0].get("text", "Unknown Title")
        return "Unknown Title"
    
    def _extract_sections(self, doc_output: Dict) -> List[Dict]:
        """Extract document sections with hierarchy"""
        sections = []
        current_section = None
        
        for element in doc_output.get("texts", []):
            # Check if element is a heading
            if element.get("type") == "heading":
                level = element.get("level", 1)
                current_section = {
                    "title": element.get("text"),
                    "level": level,
                    "content": []
                }
                sections.append(current_section)
            elif current_section:
                current_section["content"].append(element.get("text", ""))
                
        return sections
    
    def _extract_tables(self, doc_output: Dict) -> List[Dict]:
        """Extract tables from document"""
        tables = []
        for element in doc_output.get("tables", []):
            tables.append({
                "caption": element.get("caption", ""),
                "data": element.get("data", [])
            })
        return tables
    
    def _extract_figures(self, doc_output: Dict) -> List[Dict]:
        """Extract figure information"""
        figures = []
        for element in doc_output.get("figures", []):
            figures.append({
                "caption": element.get("caption", ""),
                "page": element.get("page", 0)
            })
        return figures