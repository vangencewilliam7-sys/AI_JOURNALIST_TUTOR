"""
Repository functions for conversation sessions and messages.
"""

from datetime import datetime, timezone
import logging
from .supabase_client import supabase

logger = logging.getLogger("course_architect.session_repo")

def ensure_session(session_id: str, topic: str, user_id: str) -> str:
    """Create a session row if it doesn't exist. Returns the DB row UUID (id)."""
    try:
        existing = supabase.table("conversation_sessions").select("id").eq("session_id", session_id).eq("user_id", user_id).execute()
        if existing.data:
            return existing.data[0]["id"]
        else:
            res = supabase.table("conversation_sessions").insert({
                "session_id": session_id,
                "user_id": user_id,
                "topic": topic,
                "status": "active",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "total_messages": 0
            }).execute()
            logger.info(f"Created new session: {session_id}")
            return res.data[0]["id"]
    except Exception as e:
        logger.error(f"Failed to ensure session: {e}")
        return ""

def save_message(db_session_id: str, role: str, content: str, input_source: str = "text", metadata: dict = None):
    """Save a single message to the database."""
    if not db_session_id:
        logger.error("Cannot save message: no db_session_id")
        return
    try:
        count_res = supabase.table("conversation_messages").select("id", count="exact").eq("session_id", db_session_id).execute()
        msg_index = count_res.count if count_res.count else 0
        
        msg_data = {
            "session_id": db_session_id,
            "message_index": msg_index,
            "role": role,
            "content": content,
            "input_source": input_source,
        }
        if metadata:
            msg_data["metadata"] = metadata
        
        supabase.table("conversation_messages").insert(msg_data).execute()
        
        supabase.table("conversation_sessions").update({
            "total_messages": msg_index + 1
        }).eq("id", db_session_id).execute()
        
        logger.info(f"Saved message #{msg_index} ({role}) for session {db_session_id[:8]}")
    except Exception as e:
        logger.error(f"Failed to save message: {e}")

def get_session_messages(db_session_id: str):
    res = supabase.table("conversation_messages").select("role, content, message_index").eq("session_id", db_session_id).order("message_index").execute()
    return res.data or []
