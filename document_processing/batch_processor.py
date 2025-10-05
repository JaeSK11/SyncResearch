from pathlib import Path
from typing import List
import concurrent.futures
from tqdm import tqdm
from .processor import PaperProcessor

class BatchPaperProcessor:
    def __init__(self, max_workers: int = 2):
        self.processor = PaperProcessor()
        self.max_workers = max_workers
        
    def process_directory(self, input_dir: str) -> List[str]:
        """Process all PDFs in a directory"""
        input_path = Path(input_dir)
        pdf_files = list(input_path.glob("*.pdf"))
        
        print(f"Found {len(pdf_files)} PDFs to process")
        
        processed = []
        failed = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_safe, pdf): pdf 
                for pdf in pdf_files
            }
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(pdf_files)):
                pdf_path = futures[future]
                try:
                    result = future.result()
                    if result:
                        processed.append(str(pdf_path))
                except Exception as e:
                    print(f"Failed to process {pdf_path}: {e}")
                    failed.append(str(pdf_path))
                    
        print(f"\nProcessed: {len(processed)} papers")
        print(f"Failed: {len(failed)} papers")
        
        return processed
    
    def _process_safe(self, pdf_path: Path) -> bool:
        """Safely process a single PDF"""
        try:
            self.processor.process_paper(str(pdf_path))
            return True
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {e}")
            return False