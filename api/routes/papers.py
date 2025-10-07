from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import shutil
from api.models.responses import PaperInfo
from api.dependencies import get_pipeline
import sys
from pathlib import Path
# Add parent directory to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from functools import lru_cache
from rag_pipeline.basic_rag import BasicRAG
from storage.minio_client import MinIOStorage
router = APIRouter()

@router.post("/upload")
async def upload_paper(file: UploadFile = File(...)):
    """Upload and process a new research paper"""
    print(f"📤 Received upload: {file.filename}")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files accepted")
    
    temp_path = Path(f"/tmp/{file.filename}")
    
    try:
        # Save file
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"💾 Saved to: {temp_path}")
        
        # Process through pipeline
        print(f"🔄 Starting processing pipeline...")
        pipeline = get_pipeline()
        result = pipeline.process_paper(str(temp_path))
        print(f"✅ Processing complete: {result}")
        
        return {"message": "Paper processed", "paper_id": result['paper_id']}
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR during processing:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Processing failed: {str(e)}")
        
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()
            print(f"🧹 Cleaned up temp file")

@router.get("/")
async def list_papers():
    """List all papers in the system"""
    print("📋 list_papers endpoint called")
    pipeline = get_pipeline()
    
    papers = []
    
    # Get papers from ChromaDB (the source of truth for processed papers)
    try:
        results = pipeline.chroma.collection.get()
        paper_ids = set()
        
        for metadata in results.get('metadatas', []):
            if 'paper_id' in metadata:
                paper_ids.add(metadata['paper_id'])
        
        print(f"📄 Found {len(paper_ids)} papers in ChromaDB")
        
        for pid in paper_ids:
            papers.append({
                "paper_id": pid,
                "title": pid,  # Could extract from metadata if stored
                "num_chunks": 0,  # Will be filled by status endpoint
                "processed_at": ""
            })
    except Exception as e:
        print(f"❌ Error querying ChromaDB: {e}")
    
    # Also check MinIO for papers that might not be indexed yet
    try:
        objects = pipeline.storage.s3_client.list_objects_v2(
            Bucket=pipeline.storage.bucket_name,
            Prefix="raw-papers/"
        )
        
        if objects.get('Contents'):
            for obj in objects['Contents']:
                # Extract paper_id from filename
                filename = obj['Key'].split('/')[-1]
                paper_id = filename.replace('.pdf', '')
                
                # Only add if not already in list from ChromaDB
                if not any(p['paper_id'] == paper_id for p in papers):
                    papers.append({
                        "paper_id": paper_id,
                        "title": "Unknown",
                        "num_chunks": 0,
                        "processed_at": ""
                    })
        
        print(f"📄 Total papers (ChromaDB + MinIO): {len(papers)}")
    except Exception as e:
        print(f"❌ Error querying MinIO: {e}")
    
    return papers

@router.get("/{paper_id}/status")
async def get_paper_status(paper_id: str):
    """Get processing status for a paper"""
    print(f"🔍 Status check for paper: {paper_id}")
    from pathlib import Path
    
    pipeline = get_pipeline()
    status = {
        "paper_id": paper_id,
        "steps": {
            "docling": False,
            "minio": False,
            "chunked": False,
            "embedded": False,
            "chromadb": False
        },
        "details": {}
    }
    
    # Check ChromaDB FIRST (most reliable)
    try:
        results = pipeline.chroma.collection.get(
            where={"paper_id": paper_id},
            limit=1
        )
        if results['ids']:
            status["steps"]["chromadb"] = True
            
            # Count total chunks
            all_results = pipeline.chroma.collection.get(
                where={"paper_id": paper_id}
            )
            status["details"]["num_chunks"] = len(all_results['ids'])
            
            # If in ChromaDB, it MUST have been processed, chunked, and embedded
            status["steps"]["docling"] = True
            status["steps"]["chunked"] = True
            status["steps"]["embedded"] = True
    except Exception as e:
        print(f"❌ ChromaDB check failed: {e}")
    
    # Check Docling processing file (optional verification)
    processed_path = Path(f"data/processed/{paper_id}_processed.json")
    if processed_path.exists():
        status["details"]["docling_path"] = str(processed_path)
    
    # Check MinIO
    try:
        # Handle paper IDs that might be partial filenames
        objects = pipeline.storage.s3_client.list_objects_v2(
            Bucket=pipeline.storage.bucket_name,
            Prefix=f"raw-papers/"
        )
        if objects.get('Contents'):
            for obj in objects['Contents']:
                # Check if paper_id is in the object key
                if paper_id in obj['Key']:
                    status["steps"]["minio"] = True
                    status["details"]["minio_size"] = obj['Size']
                    break
    except Exception as e:
        print(f"❌ MinIO check failed: {e}")
    
    print(f"✅ Status for {paper_id}: {status}")
    return status

@router.delete("/{paper_id}")
async def delete_paper(paper_id: str):
    """Remove a paper from the system"""
    pipeline = get_pipeline()
    errors = []
    
    print(f"🗑️  Deleting paper: {paper_id}")
    
    # 1. Delete from ChromaDB
    try:
        pipeline.chroma.collection.delete(
            where={"paper_id": paper_id}
        )
        print(f"✅ Deleted from ChromaDB")
    except Exception as e:
        errors.append(f"ChromaDB: {e}")
        print(f"❌ ChromaDB deletion failed: {e}")
    
    # 2. Delete from MinIO
    try:
        objects = pipeline.storage.s3_client.list_objects_v2(
            Bucket=pipeline.storage.bucket_name,
            Prefix=f"raw-papers/"
        )
        
        print(f"🔍 Looking for paper_id '{paper_id}' in MinIO...")
        
        if objects.get('Contents'):
            print(f"📦 Available objects in MinIO:")
            for obj in objects['Contents']:
                print(f"   - {obj['Key']}")
            
            deleted_count = 0
            for obj in objects['Contents']:
                obj_key = obj['Key']
                # Check if paper_id appears anywhere in the key
                if paper_id in obj_key:
                    print(f"✅ MATCH! Deleting: {obj_key}")
                    pipeline.storage.s3_client.delete_object(
                        Bucket=pipeline.storage.bucket_name,
                        Key=obj_key
                    )
                    deleted_count += 1
                else:
                    print(f"❌ No match: '{paper_id}' not in '{obj_key}'")
            
            if deleted_count == 0:
                print(f"⚠️  Warning: No MinIO objects matched '{paper_id}'")
                errors.append(f"MinIO: No objects found matching '{paper_id}'")
            else:
                print(f"✅ Deleted {deleted_count} object(s) from MinIO")
        else:
            print(f"⚠️  No objects found in MinIO bucket")
            
    except Exception as e:
        errors.append(f"MinIO: {e}")
        print(f"❌ MinIO deletion failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Delete processed file
    try:
        from pathlib import Path
        processed_path = Path(f"data/processed/{paper_id}_processed.json")
        if processed_path.exists():
            processed_path.unlink()
            print(f"✅ Deleted processed file")
    except Exception as e:
        errors.append(f"File system: {e}")
        print(f"❌ File deletion failed: {e}")
    
    if errors:
        return {
            "message": f"Paper {paper_id} partially deleted",
            "errors": errors
        }
    
    return {"message": f"Paper {paper_id} completely deleted"}