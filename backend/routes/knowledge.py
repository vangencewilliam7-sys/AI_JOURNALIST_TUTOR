"""
Knowledge ingestion and retrieval routes.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List

from models import YoutubeIngestRequest
from auth import get_current_user
from db.supabase_client import embeddings_model
from db.knowledge_repo import (
    get_knowledge_sources, delete_knowledge_source,
    insert_knowledge_source, update_source_chunk_count, insert_chunks
)
from services.file_parser import _read_file_content, _chunk_text, fetch_youtube_transcript

logger = logging.getLogger("course_architect.routes.knowledge")
router = APIRouter()

@router.get("/knowledge-sources")
async def fetch_sources(user_id: str = Depends(get_current_user)):
    try:
        return {"sources": get_knowledge_sources(user_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/knowledge-sources/{source_id}")
async def delete_source(source_id: str, user_id: str = Depends(get_current_user)):
    try:
        delete_knowledge_source(source_id, user_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest-documents")
async def ingest_documents(files: List[UploadFile] = File(...), user_id: str = Depends(get_current_user)):
    try:
        results = []
        for file in files:
            content_bytes = await file.read()
            text = _read_file_content(content_bytes, file.filename)
            if not text.strip():
                continue
                
            chunks = _chunk_text(text)
            if not chunks:
                continue
                
            embeddings = embeddings_model.embed_documents(chunks)
            source_id = insert_knowledge_source(user_id, file.filename, "document")
            
            chunk_records = []
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                chunk_records.append({
                    "user_id": user_id,
                    "source_id": source_id,
                    "content": chunk,
                    "embedding": emb,
                    "location_marker": f"Part {i+1}"
                })
            insert_chunks(chunk_records)
            update_source_chunk_count(source_id, len(chunks))
            results.append({"filename": file.filename, "chunks": len(chunks)})
            
        return {"status": "success", "ingested": results}
    except Exception as e:
        logger.error(f"Ingest docs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest-youtube")
async def ingest_youtube(request: YoutubeIngestRequest, user_id: str = Depends(get_current_user)):
    try:
        text = fetch_youtube_transcript(request.url)
        chunks = _chunk_text(text)
        embeddings = embeddings_model.embed_documents(chunks)
        
        source_id = insert_knowledge_source(user_id, f"YouTube: {request.url}", "youtube", request.url)
        
        chunk_records = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            chunk_records.append({
                "user_id": user_id,
                "source_id": source_id,
                "content": chunk,
                "embedding": emb,
                "location_marker": f"Part {i+1}"
            })
        insert_chunks(chunk_records)
        update_source_chunk_count(source_id, len(chunks))
        
        return {"status": "success", "url": request.url, "chunks": len(chunks)}
    except Exception as e:
        logger.error(f"Ingest youtube error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
