"""Authentication dependency for FastAPI."""

import logging
from fastapi import Header, HTTPException
from db.supabase_client import supabase

logger = logging.getLogger("course_architect.auth")

async def get_current_user(authorization: str = Header(...)) -> str:
    """
    Extracts the Bearer token from the Authorization header and verifies it with Supabase.
    Returns the user's UUID string.
    """
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header")
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header. Must use Bearer token.")
        
    token = authorization.replace("Bearer ", "")
    
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        return str(user_response.user.id)
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
