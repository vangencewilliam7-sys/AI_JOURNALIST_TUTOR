"""
Repository functions for Knowledge Sources and Chunks.
"""

import logging
from config import TOP_K_RAG, RAG_MATCH_THRESHOLD
from .supabase_client import supabase, embeddings_model

logger = logging.getLogger("course_architect.knowledge_repo")

def get_knowledge_sources(user_id: str):
    res = supabase.table("knowledge_sources").select("id, title, source_type, chunk_count, created_at").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data or []

def delete_knowledge_source(source_id: str, user_id: str):
    # RLS or user_id check is needed to ensure a user only deletes their own
    res = supabase.table("knowledge_sources").delete().eq("id", source_id).eq("user_id", user_id).execute()
    return res.data

def insert_knowledge_source(user_id: str, title: str, source_type: str, url: str = None) -> str:
    data = {"user_id": user_id, "title": title, "source_type": source_type}
    if url:
        data["url"] = url
    res = supabase.table("knowledge_sources").insert(data).execute()
    return res.data[0]["id"]

def update_source_chunk_count(source_id: str, count: int):
    supabase.table("knowledge_sources").update({"chunk_count": count}).eq("id", source_id).execute()

def insert_chunks(chunks_data: list):
    # Bulk insert is fine, might need batching if > 1000 chunks
    for i in range(0, len(chunks_data), 100):
        batch = chunks_data[i:i+100]
        supabase.table("knowledge_chunks").insert(batch).execute()

def hybrid_rag_fetch(query: str, user_id: str, top_k: int = TOP_K_RAG) -> dict:
    """Embed the query and find matching chunks using the match_knowledge_chunks RPC."""
    try:
        if not query.strip():
            return {"context_str": "", "chunks_used": []}
            
        query_embedding = embeddings_model.embed_query(query)
        
        # Use our new user_id aware RPC function
        res = supabase.rpc(
            "match_knowledge_chunks",
            {
                "query_embedding": query_embedding,
                "match_threshold": RAG_MATCH_THRESHOLD,
                "match_count": top_k,
                "p_user_id": user_id
            }
        ).execute()
        
        matches = res.data or []
        if not matches:
            return {"context_str": "", "chunks_used": []}
            
        context_parts = []
        chunks_used = []
        for m in matches:
            src_info = m.get("knowledge_sources", {})
            title = src_info.get("title", "Unknown Source")
            content = m.get("content", "")
            loc = m.get("location_marker", "")
            context_parts.append(f"[{title} {loc}]: {content}")
            chunks_used.append({
                "source_title": title,
                "content": content[:150] + "...",
                "similarity": m.get("similarity")
            })
            
        return {
            "context_str": "\n\n".join(context_parts),
            "chunks_used": chunks_used
        }
    except Exception as e:
        logger.error(f"RAG fetch error: {e}")
        return {"context_str": "", "chunks_used": []}
