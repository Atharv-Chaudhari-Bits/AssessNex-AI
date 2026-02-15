"""
RAG (Retrieval-Augmented Generation) endpoints.
Handles storing and retrieving subject concepts.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List, Optional, Dict, Any
import os
import tempfile

from backend.app.rag.subject_rag import get_rag
from backend.app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/subjects/{subject}/content")
async def add_subject_content(
    subject: str,
    content: str,
    source: str = "manual",
    metadata: Optional[str] = None
):
    """
    Add text content for a subject to the vector store.
    """
    try:
        rag = get_rag()
        
        # Parse metadata if provided
        metadata_dict = {}
        if metadata:
            try:
                import json
                metadata_dict = json.loads(metadata)
            except:
                pass
        
        success = rag.add_subject_content(
            subject=subject,
            content=content,
            metadata=metadata_dict,
            source=source
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Content added for subject: {subject}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add content")
            
    except Exception as e:
        logger.error(f"Error adding content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subjects/{subject}/upload")
async def upload_subject_document(
    subject: str,
    file: UploadFile = File(...)
):
    """
    Upload a document for a subject and add to vector store.
    Supports PDF, DOCX, TXT files.
    """
    temp_path = None
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name
        
        rag = get_rag()
        success = rag.add_subject_document(subject, temp_path)
        
        if success:
            return {
                "status": "success",
                "message": f"Document {file.filename} added for subject: {subject}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add document")
            
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/subjects/{subject}/query")
async def query_subject(
    subject: str,
    q: str = Query(..., description="Query text"),
    k: int = Query(5, description="Number of results"),
    threshold: float = Query(0.0, description="Score threshold (0-1)")
):
    """
    Query a subject's vector store for relevant context.
    """
    try:
        rag = get_rag()
        results = rag.query_subject(
            subject=subject,
            query=q,
            k=k,
            score_threshold=threshold if threshold > 0 else None
        )
        
        return {
            "subject": subject,
            "query": q,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error querying subject: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_all(
    query: str,
    subjects: Optional[List[str]] = None,
    k_per_subject: int = 3
):
    """
    Query all subjects or specific ones.
    """
    try:
        rag = get_rag()
        results = rag.query_all_subjects(
            query=query,
            subjects=subjects,
            k_per_subject=k_per_subject
        )
        
        return {
            "query": query,
            "subjects_queried": subjects or "all",
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error in query all: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subjects")
async def list_subjects():
    """List all available subjects in the vector store."""
    try:
        rag = get_rag()
        subjects = rag.list_subjects()
        
        return {
            "subjects": subjects,
            "count": len(subjects)
        }
        
    except Exception as e:
        logger.error(f"Error listing subjects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subjects/{subject}/summary")
async def get_subject_summary(subject: str, max_chunks: int = 5):
    """Get a summary of a subject's content."""
    try:
        rag = get_rag()
        summary = rag.get_subject_summary(subject, max_chunks)
        
        return {
            "subject": subject,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/subjects/{subject}")
async def delete_subject(subject: str):
    """Delete a subject's vector store."""
    try:
        rag = get_rag()
        success = rag.delete_subject(subject)
        
        if success:
            return {
                "status": "success",
                "message": f"Deleted subject: {subject}"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Subject {subject} not found")
            
    except Exception as e:
        logger.error(f"Error deleting subject: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(subject: Optional[str] = None):
    """Get statistics about the vector stores."""
    try:
        rag = get_rag()
        stats = rag.get_stats(subject)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))