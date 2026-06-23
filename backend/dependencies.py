import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

env_path = os.path.join(os.path.dirname(__file__), '.env')

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("SUPABASE_DB_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL:
    from dotenv import dotenv_values
    config = dotenv_values(env_path)
    SUPABASE_URL = config.get("SUPABASE_URL")
    SUPABASE_ANON_KEY = config.get("SUPABASE_ANON_KEY")

security = HTTPBearer()

def get_current_expert_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Validates the Supabase JWT token from the Authorization header
    and returns the authenticated user's ID (which corresponds to the expert_id).
    """
    token = credentials.credentials
    # Create an ephemeral client specifically for verifying this token
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    try:
        # get_user automatically validates the JWT signature against Supabase
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user_response.user.id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
